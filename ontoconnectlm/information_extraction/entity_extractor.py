from typing import List
from langchain_core.language_models.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
import os

from ontoconnectlm.information_extraction.information_extractor import InformationExtractor

PROMPT_PATH = "prompts/ner_prompt.txt"


class EntityExtractor(InformationExtractor):

    llm : BaseLLM
    context_description : str
    open_entity_extraction : bool
    entity_types : List[str]
    entity_descriptions : dict
    prompt_path : str
    open_extraction_prompt_path : str

    def __init__(self,
                 llm : BaseLLM,
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

        self.prompt_path = PROMPT_PATH



    def format_prompt(self, text : str) -> str:

        # Chargement du prompt
        path = os.path.join(os.path.dirname(__file__), self.prompt_path)
        with open(path ,"r") as read_file:
            template = read_file.read()

        prompt = PromptTemplate.from_template(template)


        # Si pas type entité/relation donnée
        if self.open_entity_extraction:
            entity_types_string = "Proceed to open extraction. You can return any type of entity."
        
        # If entity or relation types are specified
        else:
            
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
            "context_description" : self.context_description,
            "entity_types" : entity_types_string,
            "sentence" : text
        })


