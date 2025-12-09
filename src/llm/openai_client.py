from src.llm.base import BaseLLMClient

class OpenAIClient(BaseLLMClient):
    """OpenAI LLM Client - TO BE IMPLEMENTED"""
    
    def generate(self, prompt: str, **kwargs) -> str:
        raise NotImplementedError("OpenAI client to be implemented")
    
    def generate_json(self, prompt: str, **kwargs):
        raise NotImplementedError("OpenAI JSON generation to be implemented")
