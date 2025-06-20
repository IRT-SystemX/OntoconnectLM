import pandas as pd
import types
import urllib.parse
from owlready2 import get_ontology


"""
Here the task consists of merging collected information from both Wikidata and DBpedia: 
- Fetching correspondences
- Filtering based on the theshold value
- Normalising the representation
- Generting the curated ontology file
"""

class onto_linking:
    def __init__(self, dbpedia_path, wikidata_path, onto_pop_path, onto_enriched_path):
        self.dbpedia_path = dbpedia_path
        self.wikidata_path = wikidata_path
        self.onto_pop_path = onto_pop_path
        self.onto_enriched_path = onto_enriched_path
        self.dbpedia_sheets = {}
        self.wikidata_sheets = {}
        self.all_spots = set()
        self.all_best_matches = {}
        self.onto_pop = None
        self.existing_classes = {}

        self.editprop_map = {
            'label': 'title',
            'subclass': 'relation',
            'DBpedia ID': 'identifier',
            'description': 'description',
            'abstract': 'description',
            'image': 'subject',
            'subject': 'subject'
        }

    def format_label_for_ontology(self, label):
        return label.strip().replace(" ", "_").replace("(", "").replace(")", "")

    def normalize_text(self, text):
        return str(text).lower().strip()
    
    def lower_case_spot_column(self, sheets_dict):
        for df in sheets_dict.values():
            if 'Spot' in df.columns:
                df['Spot'] = df['Spot'].astype(str).apply(self.normalize_text) 
        return sheets_dict
    
    def find_highest_confidence(self, df, threshold=0.7):
        if 'Confidence Score' in df.columns and not df.empty:
            max_score_index = df['Confidence Score'].idxmax()
            highest_confidence_row = df.loc[[max_score_index]]
            return highest_confidence_row if highest_confidence_row['Confidence Score'].iloc[0] >= threshold else None
        return None
    
    def search_spot_in_sheets(self, sheets_dict, spot_value, source, threshold=0.7):
        results = []
        for df in sheets_dict.values():
            if 'Spot' in df.columns and 'Confidence Score' in df.columns:
                matches = df[df['Spot'] == spot_value]
                if not matches.empty:
                    for _, row in matches.iterrows():
                        if row['Confidence Score'] >= threshold:
                            best_match = row.to_dict()
                            best_match["Source"] = source
                            results.append(best_match)
        return results
    
    def load_data(self):
        self.dbpedia_sheets = self.lower_case_spot_column(
            pd.read_excel(self.dbpedia_path, sheet_name=None)
        )
        self.wikidata_sheets = self.lower_case_spot_column(
            pd.read_excel(self.wikidata_path, sheet_name=None)
        )

    def collect_spots(self):
        for sheets in [self.dbpedia_sheets, self.wikidata_sheets]:
            for df in sheets.values():
                if 'Spot' in df.columns:
                    self.all_spots.update(df['Spot'].dropna().unique())
    
    def find_best_matches(self):
        for spot_value in self.all_spots:
            dbpedia_matches = self.search_spot_in_sheets(self.dbpedia_sheets, spot_value, "DBpedia")
            wikidata_matches = self.search_spot_in_sheets(self.wikidata_sheets, spot_value, "Wikidata")
            all_matches = dbpedia_matches + wikidata_matches

            if all_matches:
                best_match_df = self.find_highest_confidence(pd.DataFrame(all_matches))
                if best_match_df is not None:
                    best_match = best_match_df.iloc[0].to_dict()
                    self.all_best_matches[spot_value] = best_match
            else:
                self.all_best_matches[spot_value] = None
    
    def load_ontology(self):
        self.onto_pop = get_ontology(self.onto_pop_path).load()
        self.existing_classes = {
            self.format_label_for_ontology(cls.name): cls
            for cls in self.onto_pop.classes()
        }
    
    def enrich_ontology(self):
        for spot_value, best_match in self.all_best_matches.items():
            if best_match is not None:
                best_label_raw = best_match.get("Label", "")
                best_label = self.format_label_for_ontology(best_label_raw)

                if best_label and best_label not in self.existing_classes:
                    with self.onto_pop:
                        source = best_match.get("Source")
                        if source in ["DBpedia", "Wikidata"]:
                            props = {
                                k: v for k, v in best_match.items()
                                if k.lower() in self.editprop_map
                            }

                            # Recherche des parents
                            parent_classes = [
                                cls for cls in self.onto_pop.classes()
                                if any(self.normalize_text(spot_value) in self.normalize_text(inst.has_text)
                                       for inst in cls.instances() if hasattr(inst, 'has_text'))
                            ]
                            
                            NewClass = types.new_class(best_label, tuple(parent_classes))
                            setattr(NewClass, "language", "fr")
                            setattr(NewClass, "format", "RDF/XML")
                            setattr(NewClass, "source", source)

                            for prop_name, prop_value in props.items():
                                onto_prop = self.editprop_map.get(prop_name.lower())
                                if prop_value and onto_prop:
                                    setattr(NewClass, onto_prop, prop_value)

                            self.existing_classes[best_label] = NewClass
                            print(f" Label nouvelle classe créée : {best_label}")
                            print(f"Source : {source}")
                            print(f"Propriétés: {props}")

    def save_ontology(self):
        if self.onto_pop:
            self.onto_pop.save(self.onto_enriched_path)
            print("Ontologie mise à jour !")
        else:
            print("Erreur: Problème de sauvegarde.")
    
    def run(self):
        self.load_data()
        self.collect_spots()
        self.find_best_matches()
        self.load_ontology()
        self.enrich_ontology()
        self.save_ontology()






    