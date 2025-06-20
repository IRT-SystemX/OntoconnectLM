from typing import List
from langchain_core.language_models.llms import LLM
from langchain_core.prompts.loading import load_prompt
from information_extractor import InformationExtractor
import json

class EntityExtractor(InformationExtractor):

    llm : LLM
    context_description : str
    open_entity_extraction : bool
    entity_types : List[str]
    entity_descriptions : dict
    prompt_path : str
    open_extraction_prompt_path : str

    def __init__(self,
                 llm : LLM,
                 entity_types : List[str] = [],
                 entity_descriptions : dict = {},
                 context_description : str = "",):
    
        self.llm = llm
        self.context_description = context_description

        if len(entity_types) == 0:
            print("Empty value for entity types. Setting extraction to open entity extraction")
            self.open_entity_extraction = True
        else:
            self.open_entity_extraction = False
            self.entity_types = entity_types

        self.entity_descriptions = entity_descriptions

        self.prompt_path = "prompts/triplet_extractor/ner_prompt.json"
        self.open_extraction_prompt_path = "prompts/triplet_extractor/ner_open_prompt.json"


    def format_prompt(self, text : str) -> str:

        # Si pas type entité/relation donnée
        if self.open_entity_extraction:
            prompt = load_prompt(path=self.open_extraction_prompt_path)

            return prompt.invoke({
                "context_details" : self.context_description,
                "sentence" : text
            })
        
        # Si on a précisé les types d'entités ou relations
        else:
            prompt = load_prompt(path=self.prompt_path)

            # Création de la description des types d'entités à extraire
            if len(self.entity_descriptions) > 0:
                descriptions = []
                for entity_type, description in self.entity_descriptions.items():
                    if entity_type in self.entity_types:
                        descriptions.append(entity_type + " ( " + description + " )")

                entity_types_string = "\n".join(descriptions)

            else:
                entity_types_string = "\n".join(self.entity_types)

            return prompt.invoke({
                "context_details" : self.context_description,
                "entity_types" : entity_types_string,
                "sentence" : text
            })


