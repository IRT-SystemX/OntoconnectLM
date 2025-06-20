import os
import pandas as pd
from owlready2 import get_ontology
from nerd import nerd_client
from SPARQLWrapper import SPARQLWrapper, JSON

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
       
    def __init__(self, ontology_path, wikidata_nel_results, wiki_endpoint='https://query.wikidata.org/sparql'):
        self.ontology_path = ontology_path
        self.wikidata_nel_results = wikidata_nel_results
        self.wiki_endpoint = wiki_endpoint
        self.onto = get_ontology(self.ontology_path).load()
        self.nerd= nerd_client.NerdClient()
        
        if os.path.exists(self.wikidata_nel_results):
            os.remove(self.wikidata_nel_results)

    def extract_wikidata_metadata(self, resource):
        query = f"""
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX wd: <http://www.wikidata.org/entity/>
        PREFIX wdt: <http://www.wikidata.org/prop/direct/>
        PREFIX wikibase: <http://wikiba.se/ontology#>
        PREFIX bd: <http://www.bigdata.com/rdf#>
        PREFIX schema: <http://schema.org/>
        SELECT ?label ?description ?instanceof ?image ?googleid
        WHERE {{
            wd:{resource} rdfs:label ?label .
            wd:{resource} schema:description ?description .
        OPTIONAL {{ wd:{resource} wdt:P31* ?instanceof . }}
        OPTIONAL {{ wd:{resource} wdt:P18 ?image . }}
        OPTIONAL {{ wd:{resource} wdt:P2671 ?googleid . }}
        FILTER (LANG(?label) = 'fr')
        FILTER (LANG(?description) IN ('fr','en'))
            }}
        """

        sparql = SPARQLWrapper(self.wiki_endpoint)
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
            return data        
        except Exception as e:
                print("Une erreur s'est produite :", str(e))
        return None

    
    def process_individuals(self, cls):
        results = []
        for individual in cls.instances():
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
                        googleid = []

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
                            if 'googleid' in item and item['googleid'] is not None:
                                google_id = item.get('googleid', 'N/A')

                
                        results.append({
                            'Raw text': value,
                            'Raw Name': rawName,
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

    
    def enrich_entities(self):
        for cls in self.onto.classes():
            results = self.process_individuals(cls)
            if results:
                df = pd.DataFrame(results)
                with pd.ExcelWriter(self.wikidata_nel_results, mode='a' if os.path.exists(self.wikidata_nel_results) else 'w') as writer:
                    df.to_excel(writer, sheet_name=cls.name[:31])

        print("Results successfully stored in Wikidata_EL_results")

