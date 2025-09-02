from abc import ABC, abstractmethod
from langchain_core.language_models.llms import BaseLLM
from langchain_core.messages.ai import AIMessage
import json

# Abstract class for information extraction classes

class InformationExtractor(ABC):

    llm : BaseLLM
    
    @abstractmethod
    def format_prompt(self, text : str):
        pass

    @staticmethod
    def decode_result(json_result : str) -> str:

        # Case using OpenAI LLM
        if isinstance(json_result, AIMessage):
            json_result = json_result.content

        try:
            result = json_result.split("```")[1]
            result = result.strip("json")
            return json.loads(result)
        except Exception as E:
            print("Erreur extracting result from json structured output : " , json_result)
            print(E)
            return json_result
        
    def run(self, text):

        prompt = self.format_prompt(text=text)

        result = self.llm.invoke(prompt)

        return self.decode_result(result)