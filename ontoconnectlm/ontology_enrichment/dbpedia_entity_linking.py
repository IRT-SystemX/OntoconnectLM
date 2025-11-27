import os
import spacy
import tempfile
import pandas as pd
from owlready2 import get_ontology
from SPARQLWrapper import SPARQLWrapper, JSON

DBPEDIA_QUERY_FILEPATH = "sparql_queries/dbpedia_query.txt"
DBPEDIA_SPARQL_ENDPOINT = 'http://fr.dbpedia.org/sparql'


class DBpedia_linking: 

    """
    Service aiming to extract entity metadata from DBpedia
    Args: A populated ontology
    Features: 
    * Load the ontology
    * Run the named entity and linking with DBpedia
    * Query DBpedia for metadata
    * Export the results to an Excel file
    Returns: An Excel file containing all the collected information from DBpedia
    """


    def __init__(self):

        self.dbpedia_sparql_endpoint = SPARQLWrapper(DBPEDIA_SPARQL_ENDPOINT)

        self.nlp = spacy.load('fr_core_news_lg')
        self.nlp.add_pipe('dbpedia_spotlight', config={'language_code': "fr", 'dbpedia_rest_endpoint':'https://api.dbpedia-spotlight.org/fr/'})


        # Loading dbpedia query
        load_path = os.path.join(os.path.dirname(__file__), DBPEDIA_QUERY_FILEPATH)
        with open(load_path, "r") as read_file:
            self.dbpedia_query = read_file.read()


    def extract_dbpedia_metadata(self, resource):

        query = self.dbpedia_query.format(resource=resource)

        self.dbpedia_sparql_endpoint.setQuery(query)
        self.dbpedia_sparql_endpoint.setReturnFormat(JSON)

        try:
            results = self.dbpedia_sparql_endpoint.query().convert()
            data = {'DBpediametadata': []}
            for result in results['results']['bindings']:
                entry = {
                    'label': result.get('label', {}).get('value'),
                    'subject': result.get('subject', {}).get('value'),
                    'sameAs': result.get('sameAs', {}).get('value'),
                    'abstract': result.get('abstract', {}).get('value')
                }
                data['DBpediametadata'].append(entry)
            return data if data['DBpediametadata'] else None
        except Exception as e:
            print(f"SPARQL Query Error for {resource}: {e}")
            return None


    def process_entities(self, cls):
    
        class_results = []
        for individual in cls.instances():
            value = str(getattr(individual, 'has_text',None))
            if not value:
                continue
            doc = self.nlp(value)
            for ent in doc.ents:
                    if not ent.kb_id_:
                        continue

                    metadata = self.extract_dbpedia_metadata(ent.kb_id_)
                    if metadata and "DBpediametadata" in metadata:
                        meta = metadata["DBpediametadata"][0]
                        subject = meta.get('subject')
                        same = meta.get('sameAs')
                        abstract = meta.get('abstract')

                        class_results.append({
                            "Raw text": value,
                            "Spot": ent.text,
                            "DBpedia ID": ent.kb_id_,
                            "Label": meta.get('label'),
                            "Confidence Score": ent._.dbpedia_raw_result.get('@similarityScore'),
                            "Abstract": abstract,
                            "Subject": subject,
                            "SubClass": same
                        })

        return class_results
        

    def dbpedia_enrichment(self, ontology_content : str) -> pd.DataFrame:

        with tempfile.NamedTemporaryFile(delete=True, suffix='.owl', mode="w+") as tmp_file:
            tmp_file.write(ontology_content)
            ontology = get_ontology(tmp_file.name).load()

        enrichment_results = []

        
        for ontology_class in ontology.classes():
            # print("Processing class : " , ontology_class)
            class_results = self.process_entities(ontology_class)

            if class_results:
                df = pd.DataFrame(class_results)

                enrichment_results.append(df)
                # with pd.ExcelWriter(self.output_path, mode='a' if os.path.exists(self.output_path) else 'w') as writer:
                #     df.to_excel(writer, sheet_name=cls.name[:31])

            if enrichment_results:
                return pd.concat(enrichment_results)
            else:
                return pd.DataFrame()
        


