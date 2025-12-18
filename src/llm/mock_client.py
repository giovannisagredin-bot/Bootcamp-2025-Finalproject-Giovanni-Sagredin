from src.llm.utils import GenerativeAIClient




class MockClient(GenerativeAIClient):
    def generate(self, prompt: str, **kwargs) -> str:
        return f'Mock response for: {prompt}'