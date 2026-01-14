import pandas as pd
import types
import owlready2
import tempfile
 
 
"""
Generate an enriched ontology version based on collected information from both Wikidata and DBpedia: 
Features: 
    - Fetching correspondences
    - Filtering based on the theshold value
    - Normalising the representation
    - Generting the curated ontology file
Args: populated ontology path, enriched ontology path
Returns: enriched ontology file
"""
 
class Onto_Updater:
 
    dbpedia_results : pd.DataFrame
    wikidata_results : pd.DataFrame
    ontology_content : str
    all_results : pd.DataFrame
 
    def __init__(self, dbpedia_results : pd.DataFrame, wikidata_results : pd.DataFrame, ontology_content : str):
        self.dbpedia_results = dbpedia_results
        self.wikidata_results = wikidata_results
        self.ontology_content = ontology_content
 
        self.editprop_map = {
            'label': 'title',
            'subclass': 'relation',
            'DBpedia ID': 'identifier',
            'description': 'description',
            'abstract': 'description',
            'image': 'subject',
            'subject': 'subject'
        }
 
    @staticmethod
    def format_label_for_ontology(label):
        return label.strip().replace(" ", "_").replace("(", "").replace(")", "")
 
    @staticmethod
    def normalize_text(text : str) -> str:
        if type(text) is list:
            text = text[0]
        return text.lower().strip()
 
 
    @staticmethod
    def lower_case_spot_column(sheets_dict):
        for df in sheets_dict.values():
            if 'Spot' in df.columns:
                df['Spot'] = df['Spot'].astype(str).apply(Onto_Updater.normalize_text) 
        return sheets_dict
    @staticmethod
    def find_highest_confidence(df, threshold=0.7):
        if 'Confidence Score' in df.columns and not df.empty:
            max_score_index = df['Confidence Score'].idxmax()
            highest_confidence_row = df.loc[[max_score_index]]
            return highest_confidence_row if highest_confidence_row['Confidence Score'].iloc[0] >= threshold else None
        return None
    @staticmethod
    def search_spot_in_sheets(sheets_dict, spot_value, source, threshold=0.7):
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
    @staticmethod
    def get_raw_value(raw_values_string : str):
        if raw_values_string.count("'") == 4:
            splits = raw_values_string.split("'")
            kept_splits = splits[1] + splits[2] + splits[3]
            return kept_splits.split(", ")[0]
        elif raw_values_string.count("'") == 2:
            splits = raw_values_string.split("'")
            kept_splits = splits[1]
            return kept_splits
        else:
            return raw_values_string

 
    def preprocess_nel_results(self) -> None:

        # Regrouping results for same piece of text
        self.dbpedia_results = self.dbpedia_results.drop_duplicates(subset = ["Spot"], keep='first')
        self.wikidata_results = self.wikidata_results.drop_duplicates(subset = ["Spot"], keep='first')
 
        # Merging both dataframes
        sources_column = ["DBpedia"]*self.dbpedia_results.shape[0] + ["Wikidata"]*self.wikidata_results.shape[0]
        all_df = pd.concat([self.dbpedia_results, self.wikidata_results])
        all_df["Source"] = sources_column
 
        self.all_results = all_df
 
    def find_best_matches(self, threshold : float = 0.7) -> dict:
         
        if self.dbpedia_results.empty:
            list_dbpedia_spots = []
            print("Empty dbpedia results")
        else:
            list_dbpedia_spots = self.dbpedia_results["Spot"].to_list()
 
        if self.wikidata_results.empty:
            list_wikidata_spots = []
            print("Empty wikidata results")

        else:
            list_wikidata_spots = self.wikidata_results["Spot"].to_list()
 
        best_matches = {}
 
        for spot_value in list_dbpedia_spots:
 
            # Case where value is found in both enrichments
            if spot_value in list_wikidata_spots:
                dbpedia_index = list_dbpedia_spots.index(spot_value)
                dbpedia_score = self.dbpedia_results["Confidence Score"].to_list()[dbpedia_index]
                dbpedia_score = float(dbpedia_score)
 
                wikidata_index = list_wikidata_spots.index(spot_value)
                wikidata_score = self.wikidata_results["Confidence Score"].to_list()[wikidata_index]
                wikidata_score = float(wikidata_score)
 
                if dbpedia_score >= wikidata_score and dbpedia_score >= threshold:
                    best_matches[spot_value] = self.dbpedia_results.iloc[dbpedia_index].to_dict()
                    best_matches[spot_value]["Source"] = "DBpedia"
                elif wikidata_score >= threshold:
                    best_matches[spot_value] = self.wikidata_results.iloc[wikidata_index].to_dict()
                    best_matches[spot_value]["Source"] = "Wikidata"
                else:
                    print("Skipping value cause inferior to threshold")
                    pass
 
            # Case where value is only found in DBpedia
            else:
                dbpedia_index = list_dbpedia_spots.index(spot_value)
                dbpedia_score = self.dbpedia_results["Confidence Score"].to_list()[dbpedia_index]
                dbpedia_score = float(dbpedia_score)
 
                if dbpedia_score >= threshold:
                    best_matches[spot_value] = self.dbpedia_results.iloc[dbpedia_index].to_dict()
                    best_matches[spot_value]["Source"] = "DBpedia"
 
            
        # for spot_value in self.wikidata_results["Spot"]:
 
        for spot_value in list_wikidata_spots:

            # Skip if already handled in previous loop
            if spot_value in best_matches:
                continue

            wikidata_index = list_wikidata_spots.index(spot_value)
            wikidata_score = float(self.wikidata_results["Confidence Score"].to_list()[wikidata_index])

            if wikidata_score >= threshold:
                best_matches[spot_value] = self.wikidata_results.iloc[wikidata_index].to_dict()
                best_matches[spot_value]["Source"] = "Wikidata"

 
        return best_matches

 
    # Loading of ontology with owlready2 library in order to edit it later
    def load_ontology_owlready2(self):
        with tempfile.NamedTemporaryFile(delete=True, suffix='.owl', mode="w+") as tmp_file:
            tmp_file.write(self.ontology_content)
 
            ontology = owlready2.get_ontology(tmp_file.name).load()
 
        return ontology
 
    
    def add_nel_values_as_classes(self, best_matches : dict) -> None:
 
        for spot_value, spot_info in best_matches.items():
 
            best_label_raw = spot_info["Label"]
            best_label = Onto_Updater.format_label_for_ontology(best_label_raw)
 
            with self.ontology:
 
                if best_label not in self.ontology.classes():
 
 
                    props = {
                        k: v for k, v in spot_info.items()
                        if k.lower() in self.editprop_map
                    }
 
                    # Recherche des parents
                    parent_classes = []
 
                    for onto_class in self.ontology.classes():
                        for instance in onto_class.instances():
                            if hasattr(instance, 'has_text'):
                                has_text_values = [Onto_Updater.normalize_text(text) for text in instance.has_text]
                                if any(self.normalize_text(spot_value) in has_text_value for has_text_value in has_text_values):
                                    parent_classes.append(onto_class)
 
                    
                    NewClass = types.new_class(best_label, tuple(parent_classes))
                    setattr(NewClass, "language", "fr")
                    setattr(NewClass, "format", "RDF/XML")
                    setattr(NewClass, "source", spot_info["Source"])
 
                    for prop_name, prop_value in props.items():
                        onto_prop = self.editprop_map.get(prop_name.lower())
                        if prop_value and onto_prop:
                            setattr(NewClass, onto_prop, prop_value)
 
                    print(f" Label nouvelle classe créée : {best_label}")
                    # print(f"Source : {spot_info["Source"]}")
                    # print(f"Propriétés: {props}")
 
 
    def add_nel_values_as_instance_metadata(self, best_matches : dict) -> None:
 
        for spot_value, spot_info in best_matches.items():
            raw_value = Onto_Updater.get_raw_value( spot_info["Raw text"] )
 
 
            # print("Trying to find match for ", raw_value)
            with self.ontology:
                for onto_class in self.ontology.classes():
                    for instance in onto_class.instances():
                        if hasattr(instance, 'has_text'):
                            # Matching with existing individual
                            if raw_value in instance.has_text:
 
                                # Browsing dbpedia and wikidata annotations
                                properties = {
                                    k: v for k, v in spot_info.items()
                                    if k.lower() in self.editprop_map
                                    }
                                
                                for prop_name, prop_value in properties.items():
                                    prop_name = self.editprop_map.get(prop_name.lower())
                                    onto_prop = getattr(self.ontology, prop_name)
 
 
                                    if type(prop_value) is list:
                                        if len(prop_value) > 0:
                                            prop_value = prop_value[0]
                                        else:
                                            prop_value = ""
 
                                    if onto_prop is not None:
                                        onto_prop[instance].append(prop_value)
                                        print("Added relation : " , instance , " " , onto_prop , " " , prop_value)
 
                                    else:
                                        new_prop = types.new_class(prop_name, (owlready2.DataProperty,))
                                        new_prop[instance].append(prop_value)
                                        print("Created relation then added relation : " , instance , " " , new_prop , " " , prop_value)
 
 
    def get_ontology_result(self) -> str:
 
        with tempfile.NamedTemporaryFile(delete=True, suffix='.owl', mode="w+") as tmp_file:
 
            self.ontology.save(tmp_file.name)
            return tmp_file.read()

 
    def update_ontology(self, enrichment_mode : str = "individuals") -> str:
 
        assert(enrichment_mode in ["classes", "individuals"])
 
        self.preprocess_nel_results()
        self.ontology = self.load_ontology_owlready2()

        best_matches = self.find_best_matches()
 
 
        if enrichment_mode == "classes":
            self.add_nel_values_as_classes(best_matches)
 
        elif enrichment_mode == "individuals":
            self.add_nel_values_as_instance_metadata(best_matches)
 
 
        return self.get_ontology_result()