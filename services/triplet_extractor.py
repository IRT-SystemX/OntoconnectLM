from langchain_core.language_models.llms import LLM
from typing import List
from entity_extractor import EntityExtractor
from relation_extractor import RelationExtractor


class TripletExtractor:
    """
    Service aiming to extract triples (entities and relations) from texts.

    Input : Texts, list of entity types, list of relation types.
    Output: List of triples.
    
    If no type is provided, the LLM will perform Open Relation Extraction (with free types)"""


    entity_extractor : EntityExtractor
    relation_extractor : RelationExtractor

    relation_types : List[str]
    relation_descriptions : dict
    llm : LLM
    context_descriptions : str

    def __init__(self, 
                 llm : LLM, 
                 entity_types : List[str] = [],
                 entity_descriptions : dict = {}, 
                 relation_types : List[str] = [],
                 relation_descriptions : dict = {},
                 context_description : str = "",):
        
       
       self.entity_extractor = EntityExtractor(
        llm = llm,
        entity_types = entity_types,
        entity_descriptions = entity_descriptions,
        context_description = context_description
       )

       self.relation_types = relation_types
       self.relation_descriptions = relation_descriptions
       self.llm = llm
       self.context_description = context_description


    def run(self, texts : List[str]):

        found_entities = []
        for text in texts:
            text_entities = self.entity_extractor.run(text)
            found_entities.append(text_entities)

        found_triples = []
        for t,text in enumerate(texts):

            relation_extractor = RelationExtractor(
                llm = self.llm,
                relation_types = self.relation_types,
                relation_descriptions = self.relation_descriptions,
                context_description = self.context_description,
                found_entities = found_entities[t]
            )

            text_triples = relation_extractor.run(text)
            found_triples.append(text_triples)

        return found_triples

        


