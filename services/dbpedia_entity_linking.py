import os
import spacy
import spacy_dbpedia_spotlight
import pandas as pd
from rdflib import Graph
from owlready2 import get_ontology
from SPARQLWrapper import SPARQLWrapper, JSON
from spacy import displacy


class DBpedia_linking: 

    """
    Service aiming to extract entity metadata from DBpedia
    Input: A populated ontology
    Capabilities : 
    * Load the ontology
    * Run the named entity and linking with DBpedia
    * Query DBpedia for metadata
    * Export the results to an Excel file
    Output: An Excel file containing all the collected information from DBpedia
    """


    def __init__(self, ontology_path, output_path, dbpedia_rest_endpoint='http://127.0.0.1:2222/rest', dbpedia_sparql_endpoint='http://fr.dbpedia.org/sparql', lang='fr'):
        self.ontology_path = ontology_path
        self.output_path = output_path
        self.lang = lang
        self.dbpedia_rest_endpoint = dbpedia_rest_endpoint
        self.dbpedia_sparql_endpoint = SPARQLWrapper(dbpedia_sparql_endpoint)
        self.results = []

        self.nlp = spacy.load(f'{lang}_core_news_lg')
        self.nlp.add_pipe('dbpedia_spotlight', config={'language_code': lang, 'dbpedia_rest_endpoint': dbpedia_rest_endpoint})

        self.onto = get_ontology(ontology_path).load()

        if os.path.exists(self.output_path):
            os.remove(self.output_path)
    def extract_dbpedia_metadata(self, resource):
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX dct: <http://purl.org/dc/terms/>
        PREFIX dbo: <http://dbpedia.org/ontology/>

        SELECT DISTINCT ?label ?subject ?sameAs ?abstract
        WHERE {{
            <{resource}> rdfs:label ?label .
            OPTIONAL {{ <{resource}> dct:subject ?subject . }}
            OPTIONAL {{ <{resource}> owl:sameAs ?sameAs . }}
            OPTIONAL {{ <{resource}> dbo:abstract ?abstract . FILTER (LANG(?abstract) IN ('fr','en')) }}
            FILTER (LANG(?label) IN ('fr','en'))
        }}
        """
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

                    displacy.render(doc, style="ent") 

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
        
    def enrich_entities(self):
        for cls in self.onto.classes():
            results = self.process_entities(cls)
            if results:
                df = pd.DataFrame(results)
                with pd.ExcelWriter(self.output_path, mode='a' if os.path.exists(self.output_path) else 'w') as writer:
                    df.to_excel(writer, sheet_name=cls.name[:31])
        

