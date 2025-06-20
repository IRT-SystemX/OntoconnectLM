from langchain_core.language_models.llms import LLM
from langchain_core.prompts.loading import load_prompt
from typing import List
import numpy as np
from tqdm import tqdm
import json


class ClassesGenerator:
    """
    Service aiming to make suggestions of classes for an ontology. Starts from scratch, without any former class.

    Input : Texts
    Output: List of class"""

    def __init__(self, 
                 llm : LLM, 
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

        self.prompt_path = "prompts/classes_generator/prompt.json"
        self.cq_prompt_path = "prompts/classes_generator/cq_prompt.json"
        self.merge_prompt_path = "prompts/classes_generator/merge_prompt.json"

    @staticmethod
    def get_batch_size(texts : List[str] , seuil : int = 2000):

        taille_moyenne = np.mean([len(doc) for doc in texts])

        if seuil < taille_moyenne:
            return 1
        else:
            return int(seuil / taille_moyenne)


    def format_prompt(self, texts:List[str]) -> str:

        texts_string = "\n\n".join(texts)

        # Si pas de Competency questions
        if len(self.competency_questions) == 0:
            prompt = load_prompt(path=self.prompt_path)

            return prompt.invoke({
                "context" : self.context_description,
                "texts" : texts_string
            })
        
        # Si Competency questions
        else:
            prompt = load_prompt(path=self.cq_prompt_path)

            cq_string = "\n".join(self.competency_questions)

            return prompt.invoke({
                "context" : self.context_description,
                "cq" : cq_string,
                "texts" : texts_string
            })
        
    @staticmethod
    def decode_result(json_result):
        try:
            result = json_result.split("```")[1]
            result = result.strip("json")
            return json.loads(result)
        except Exception as E:
            print("Erreur de décodage des résultats : " , json_result)
            print(E)
            return json_result
        
    @staticmethod
    def select_docs(texts : List[str], inf : int, sup : int):

        selected_texts = texts[inf:sup]

        return "\n".join(selected_texts)

    @staticmethod
    def extraction_resultat(raw_llm_result : str):

        try:
            result = raw_llm_result.split("```")[1]
            result = result.strip("json")
            return json.loads(result)
        
        except Exception as E:
            print(E)
            return raw_llm_result
        

    def class_generation(self, texts : List[str]):
        prompt = self.format_prompt(texts=texts)
        result = self.llm.invoke(prompt)
        return self.decode_result(result)

    
    def merge_classes(self, all_classes : List[List[str]], nb_classes : int = 16):
        prompt = load_prompt(path=self.merge_prompt_path)
        chain = prompt | self.llm

        classes_to_inject = "\n\n".join(["\n".join(classes) for classes in all_classes])


        merging_result = chain.invoke({
            "contexte" : self.context_description,
            "nb_classes" : nb_classes,
            "classes" : classes_to_inject

        })

        return self.extraction_resultat(merging_result)


    def run(self, texts : List[str], taille_max : int = 2000, nb_classes : int = 16):

        total_len = sum([len(text) for text in texts])

        # Cas execution unique : si les textes sont plus courts que la taille max
        if total_len <= taille_max:
            return self.class_generation(texts=texts)
            
        
        # Cas execution en plusieurs fois
        else:
            taille_batch = self.get_batch_size(texts=texts, seuil=taille_max)

            all_classes = []
            for i in tqdm(range(82//taille_batch)):

                selected_texts = self.select_docs(texts=texts, inf=taille_batch*i, sup=taille_batch*(i+1)).split("\n\n")

                new_classes = self.class_generation(texts=selected_texts)
                all_classes.append(new_classes)

            return self.merge_classes(all_classes=all_classes, nb_classes=nb_classes)

    



