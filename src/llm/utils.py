from abc import ABC, abstractmethod
from enum import Enum
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class GenerativeAIClient(ABC):

  @abstractmethod
  def generate(self, prompt: str, **kwargs) -> str:
        pass


class Provider(str, Enum):
    OPENAI = 'openai'
    GOOGLE = 'google'
    MOCK = 'mock' 

class GenerativeAIClientFactory:
    
    @staticmethod
    def create_client(provider: Provider) -> GenerativeAIClient:
        # Import inside function to avoid circular imports
        from src.llm.openai_client import OpenAIClient
        from src.llm.gemini_client import GoogleGenAIClient
        from src.llm.mock_client import MockClient
        
        if provider == Provider.OPENAI:
            logging.info("Creating OpenAI client")
            return OpenAIClient()
        elif provider == Provider.GOOGLE:
            logging.info("Creating Google GenAI client")
            return GoogleGenAIClient()
        elif provider == Provider.MOCK:
            logging.info("Creating Mock client")
            return MockClient()
        else:
            raise ValueError(f"Unknown provider: {provider}")