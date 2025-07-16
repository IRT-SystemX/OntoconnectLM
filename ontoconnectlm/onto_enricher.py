import pandas as pd

from ontoconnectlm.ontology_enrichment.dbpedia_entity_linking import DBpedia_linking
from ontoconnectlm.ontology_enrichment.wikidata_entity_linking import Wikidata_linking
from ontoconnectlm.ontology_enrichment.onto_updater import Onto_Updater


class OntoEnricher:
    
    def __init__(self, ontology_content : str):
        self.ontology_content = ontology_content

    def dbpedia_enrichment(self) -> pd.DataFrame:

        dbpedia_linker = DBpedia_linking()
        dbpedia_results = dbpedia_linker.dbpedia_enrichment(ontology_content=self.ontology_content)

        return dbpedia_results

    def wikidata_enrichment(self) -> pd.DataFrame:

        wikidata_linker = Wikidata_linking()
        wikidata_results = wikidata_linker.wikidata_enrichment(ontology_content=self.ontology_content)

        return wikidata_results
    
    def ontology_update(self, dbpedia_results : pd.DataFrame, wikidata_results : pd.DataFrame, enrichment_mode : str = "individuals"):

        onto_updater = Onto_Updater(
            dbpedia_results=dbpedia_results,
            wikidata_results=wikidata_results,
            ontology_content = self.ontology_content
        )

        return onto_updater.update_ontology(enrichment_mode=enrichment_mode)


    def run_all_enrichments(self, enrichment_mode : str = "individuals"):

        print("DBpedia metadata collection")
        dbpedia_results = self.dbpedia_enrichment()

        print("Wikidata metadata collection")
        wikidata_results = self.wikidata_enrichment()

        return self.ontology_update(
            dbpedia_results=dbpedia_results,
            wikidata_results=wikidata_results,
            enrichment_mode=enrichment_mode
        )

