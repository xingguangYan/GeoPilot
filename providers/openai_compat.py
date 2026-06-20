"""OpenAI-Compatible Provider - All APIs that follow OpenAI chat format."""
import json, os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .base import BaseProvider, register_provider

class OpenAICompatibleProvider(BaseProvider):
    ENV_KEY = "OPENAI_API_KEY"
    DEFAULT_URL = "https://api.openai.com/v1"
    def __init__(self, api_key=None, model=None, base_url=None):
        super().__init__(api_key, model, base_url)
    def get_default_model(self):
        return "gpt-4o"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {'model': self.model, 'messages': messages, 'temperature': temperature, 'max_tokens': max_tokens}
        try:
            with urlopen(Request(f'{self.base_url}/chat/completions', json.dumps(payload).encode(), headers, method='POST'), timeout=120) as resp:  # nosec
                result = json.loads(resp.read())
                return result['choices'][0]['message']['content']
        except HTTPError as e:
            return f'[Error {e.code}] {e.read().decode()[:500]}'
        except Exception as e:
            return f'[Error] {str(e)}'

