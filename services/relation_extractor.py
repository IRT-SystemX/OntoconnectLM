from typing import List
from langchain_core.language_models.llms import LLM
from langchain_core.prompts.loading import load_prompt
import json

from information_extractor import InformationExtractor

class RelationExtractor(InformationExtractor):


    def __init__(self,
                 llm : LLM,
                 found_entities : List[list],
                 relation_types : List[str] = [],
                 relation_descriptions : dict = {},
                 context_description : str = ""
                 ):
    
        self.llm = llm
        self.context_description = context_description
        self.found_entities = found_entities

        if len(relation_types) == 0:
            print("Empty value for relation types. Setting extraction to open relation extraction")
            self.open_relation_extraction = True
        else:
            self.open_relation_extraction = False
            self.relation_types = relation_types

        self.relation_descriptions = relation_descriptions

        self.prompt_path = "prompts/triplet_extractor/re_prompt.json"
        self.open_extraction_prompt_path = "prompts/triplet_extractor/re_open_prompt.json"


    def format_prompt(self, text : str) -> str:


        # Si pas type entité/relation donnée
        if self.open_relation_extraction:
            prompt = load_prompt(path=self.open_extraction_prompt_path)

            return prompt.invoke({
                "context_details" : self.context_description,
                "entities" : self.found_entities,
                "text" : text
            })
        
        # Si on a précisé les types d'entités ou relations
        else:
            prompt = load_prompt(path=self.prompt_path)

             # Création de la description des types d'entités à extraire
            if len(self.relation_descriptions) > 0:
                descriptions = []
                for relation_type, description in self.relation_descriptions.items():
                    if relation_type in self.relation_types:
                        descriptions.append(relation_type + " ( " + description + " )")

                relation_types_string = "\n".join(descriptions)

            else:

                relation_types_string = "\n".join(self.relation_types)

            return prompt.invoke({
                "context_details" : self.context_description,
                "relation_types" : relation_types_string,
                "entities" : self.found_entities,
                "text" : text
            })



