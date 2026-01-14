import os
import pandas as pd
from owlready2 import get_ontology
from nerd import nerd_client
from SPARQLWrapper import SPARQLWrapper, JSON
import tempfile
 
WIKIDATA_QUERY_FILEPATH = "sparql_queries/wikidata_query.txt"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
 
class Wikidata_linking:
 
    """
    Service aiming to extract entity metadata from Wikidata
    Input: A populated ontology
    Capabilities : 
    * Load the ontology
    * Run the named entity recognition and linking with Wikidata
    * Query Wikidata for metadata
    * Export the results to an Excel file
    Output: An Excel file containing all the collected information from Wikidata
    """
    def __init__(self,):
 
        self.nerd = nerd_client.NerdClient()
 
        # Loading wikidata query
        load_path = os.path.join(os.path.dirname(__file__), WIKIDATA_QUERY_FILEPATH)
        with open(load_path, "r") as read_file:
            self.wikidata_query = read_file.read()
 
        self.wikidata_endpoint = WIKIDATA_ENDPOINT

 
    def extract_wikidata_metadata(self, resource):
 
        query = self.wikidata_query.format(resource=resource)
        # print("Sending wikidata query for resource : ", resource)
        sparql = SPARQLWrapper(self.wikidata_endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
 
        try:
            results = sparql.query().convert()
            data ={'wikimetadata': []}
 
            for result in results['results']['bindings']:
                entry={}
                if 'label' in result:
                    entry['label']=result['label']['value']
                if 'instanceof' in result: 
                    entry['instanceof']=result['instanceof']['value']
                if 'description' in result: 
                    entry['description']=result['description']['value']
                if 'image' in result:
                    entry['image']=result['image']['value']
                if 'googleid' in result:
                    entry['googleid']=result['googleid']['value']

                data['wikimetadata'].append(entry)

            print("Found medatata for ", resource)
            return data    
        except Exception as e:
                print("Erreur lors de la récupération de métadonnées wikidata :", str(e))
        return None
 
    
    def process_individuals(self, ontology_class):
        print("Processing class : ", )
        results = []
        for individual in ontology_class.instances():
            # print("Processing individual : ", individual)
            value = str(individual.has_text)
 
            if value is not None and value != "":
                try:
                    result = self.nerd.disambiguate_text(f" {value} ", language="fr")
                    entities = result[0].get('entities')
 
                    for ent in entities:
                        label = ""
                        description = ""
                        instanceOfs = []
                        images = []
 
                        rawName = ent.get('rawName', 'N/A')
                        wiki_id = ent.get('wikidataId', 'N/A')
                        confidence = ent.get('confidence_score', 'N/A')
 
                        data = self.extract_wikidata_metadata(wiki_id)
 
                        for item in data.get('wikimetadata', []):
                            if 'label' in item and item['label'] is not None:
                                label = item.get('label', 'N/A')
                            if 'description' in item and item['description'] is not None:
                                description = item.get('description', 'N/A')
                            if 'instanceof' in item and item['instanceof'] is not None:
                                instanceOfs.append(item.get('instanceof', 'N/A'))
                                individual.seeAlso.extend(instanceOfs)
                            if 'image' in item and item['image'] is not None:
                                images.append(item.get('image', 'N/A'))
 
                        results.append({
                            'Raw text': value,
                            'Spot': rawName,
                            'Wiki ID': wiki_id,
                            'Confidence Score': confidence,
                            'Label': label,
                            'Description': description,
                            'InstanceOf': instanceOfs,
                            'Image': images
                        })
                except Exception as e:
                    print(f"print{e}")
            else:
                print(f"Value is None or empty for individual {individual}. Skipping this one.")
        return results
 
    
    def wikidata_enrichment(self, ontology_content : str) -> pd.DataFrame:
 
        enrichment_results = []
 
        with tempfile.NamedTemporaryFile(delete=True, suffix='.owl', mode="w") as tmp_file:
            tmp_file.write(ontology_content)
            ontology = get_ontology(tmp_file.name).load()
 
        for ontology_class in ontology.classes():
            results = self.process_individuals(ontology_class)
            if results:
                df = pd.DataFrame(results)
                enrichment_results.append(df)
 
 
        if enrichment_results:
            return pd.concat(enrichment_results)
        else:
            print("Finally, there is no wikidata result.")
            return pd.DataFrame()