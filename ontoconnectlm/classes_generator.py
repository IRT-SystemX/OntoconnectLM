from langchain_core.language_models.llms import BaseLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.messages.ai import AIMessage
from typing import List
import numpy as np
from tqdm import tqdm
import json
import os

DEFAULT_PROMPT_PATH = "classes_generator/prompt.txt"
CQ_PROMPT_PATH = "classes_generator/cq_prompt.txt"
MERGE_PROMPT_PATH = "classes_generator/merge_prompt.txt"


class ClassesGenerator:

    """
    Makes suggestions of classes for an ontology. Starts from scratch, without any former class.
    Args: Texts
    Returns: List of class
    
    """

    def __init__(self, 
                 llm : BaseLLM, 
                 context_description : str = "", 
                 competency_questions : List[str] = []):
        
        """Parameters
        
        llm : LLM instance to call for schema generation. Must be langchain compatible with a "inovke" method.
        context_description : String description of the context of the texts you will pass the LLM
        competency_questions : list of competency questions you expect for your target ontology. Will guide the LLM.
        """

        self.llm = llm
        self.context_description = context_description
        self.competency_questions = competency_questions

        self.prompt_path = DEFAULT_PROMPT_PATH
        self.cq_prompt_path = CQ_PROMPT_PATH
        self.merge_prompt_path = MERGE_PROMPT_PATH


    @staticmethod
    def get_batch_size(texts : List[str] , seuil : int = 2000) -> int:

        taille_moyenne = np.mean([len(doc) for doc in texts])

        if seuil < taille_moyenne:
            return 1
        else:
            return int(seuil / taille_moyenne)


    def format_prompt(self, texts:List[str], nb_classes : str) -> str:

        texts_string = "\n\n".join(texts)

        # Si pas de Competency questions
        if len(self.competency_questions) == 0:
            try:
                path = os.path.join(os.path.dirname(__file__), self.prompt_path)
                with open(path ,"r") as read_file:
                    template = read_file.read()

            except Exception as E:
                print(E)
                raise FileNotFoundError("Cannot load prompt at path : " , self.prompt_path)
    
            prompt = PromptTemplate.from_template(template)

            if nb_classes == 0:
                nb_classes = "Number of classes to generated not specified. Generation is set to free mode."
            else:
                nb_classes = str(nb_classes)

            return prompt.invoke({
                "context" : self.context_description,
                "texts" : texts_string,
                "nb_classes" : nb_classes
            })
        
        # Si Competency questions
        else:
            try:
                path = os.path.join(os.path.dirname(__file__), self.cq_prompt_path)
                with open(path ,"r") as read_file:
                    template = read_file.read()

            except Exception as E:
                print(E)
                raise FileNotFoundError("Cannot load prompt at path : " , self.cq_prompt_path)
            
                
            prompt = PromptTemplate.from_template(template)

            cq_string = "\n".join(self.competency_questions)

            if nb_classes == 0:
                nb_classes = "Number of classes to generated not specified. Generation is set to free mode."
            else:
                nb_classes = str(nb_classes)

            return prompt.invoke({
                "context" : self.context_description,
                "cq" : cq_string,
                "texts" : texts_string,
                "nb_classes" : nb_classes

            })
        
    @staticmethod
    def decode_result(llm_result) -> list:

        # Case using OpenAI LLM
        if isinstance(llm_result, AIMessage):
            llm_result = llm_result.content
        
        try:
            result = llm_result.split("```")[1]
            result = result.strip("json")
            return json.loads(result)
        except Exception as E:
            print("Erreur extracting result from json structured output : " , llm_result)
            print(E)
            return []
        
    @staticmethod
    def select_docs(texts : List[str], inf : int, sup : int) -> str:

        selected_texts = texts[inf:sup]

        return "\n".join(selected_texts)

    

    def class_generation(self, texts : List[str], nb_classes : str):
        prompt = self.format_prompt(texts=texts, nb_classes=nb_classes)
        result = self.llm.invoke(prompt)
        return self.decode_result(result)

    
    def merge_classes(self, all_classes : List[List[str]], nb_classes : int = 12):

        try:
            path = os.path.join(os.path.dirname(__file__), self.merge_prompt_path)
            with open(path ,"r") as read_file:
                template = read_file.read()

        except Exception as E:
            print(E)
            raise FileNotFoundError("Cannot load prompt at path : " , self.merge_prompt_path)
        
        prompt = PromptTemplate.from_template(template)

        classes_to_inject = "\n\n".join(["\n".join(classes) for classes in all_classes])

        nb_classes = str(nb_classes)
        
        prompt_value = prompt.invoke({
                "contexte" : self.context_description,
                "nb_classes" : nb_classes,
                "classes" : classes_to_inject

            })

        merging_result = self.llm.invoke(prompt_value)

        return self.decode_result(merging_result)


    def run(self, texts : List[str], max_batch_size : int = 2000, nb_classes : int = 0):

        total_len = sum([len(text) for text in texts])

        # Unique execution cas : if the texts are shorter than the maximum size
        if total_len <= max_batch_size:
            return self.class_generation(texts=texts, nb_classes = str(nb_classes))
            
        
        # Execution cas multiple execution
        else:
            taille_batch = self.get_batch_size(texts=texts, seuil=max_batch_size)

            all_classes = []
            for i in tqdm(range(82//taille_batch)):

                selected_texts = self.select_docs(texts=texts, inf=taille_batch*i, sup=taille_batch*(i+1)).split("\n\n")

                new_classes = self.class_generation(texts=selected_texts, nb_classes="10")
                all_classes.append(new_classes)

            return self.merge_classes(all_classes=all_classes, nb_classes=nb_classes)

    



