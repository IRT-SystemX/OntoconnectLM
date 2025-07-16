from typing import List
from langchain_core.language_models.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
import os

from ontoconnectlm.information_extraction.information_extractor import InformationExtractor

PROMPT_PATH = "prompts/re_prompt.txt"

class RelationExtractor(InformationExtractor):


    def __init__(self,
                 llm : BaseLLM,
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

        self.prompt_path = PROMPT_PATH


    def format_prompt(self, text : str) -> str:

        # Chargement du prompt
        path = os.path.join(os.path.dirname(__file__), self.prompt_path)
        with open(path ,"r") as read_file:
            template = read_file.read()

        prompt = PromptTemplate.from_template(template)


        # Si pas type entité/relation donnée
        if self.open_relation_extraction:

            relation_types_string = "Proceed to open extraction. You can return any of relation type"
        
        # Si on a précisé les types d'entités ou relations
        else:

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
            "context_description" : self.context_description,
            "relation_types" : relation_types_string,
            "entities" : self.found_entities,
            "text" : text
        })



