from abc import ABC, abstractmethod
from langchain_core.language_models.llms import LLM
import json
from typing import List

# Abstract class for information extraction classes

class InformationExtractor(ABC):

    llm : LLM
    
    @abstractmethod
    def format_prompt(self, text : str):
        pass

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
        
    def run(self, text):

        prompt = self.format_prompt(text=text)

        result = self.llm.invoke(prompt)

        return self.decode_result(result)