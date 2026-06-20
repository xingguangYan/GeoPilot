"""Ollama Local Provider"""
import json, os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .base import BaseProvider

class OllamaProvider(BaseProvider):
    ENV_KEY = ""
    DEFAULT_URL = "http://localhost:11434"
    def get_default_model(self):
        return "llama3.1"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        prompt = ''
        if system_prompt:
            prompt += f'System: {system_prompt}\n\n'
        for m in messages:
            prompt += f"{m['role'].upper()}: {m['content']}\n\n"
        prompt += 'ASSISTANT: '
        payload = {'model': self.model, 'prompt': prompt, 'stream': False, 'options': {'temperature': temperature, 'num_predict': max_tokens}}
        try:
            with urlopen(Request(f'{self.base_url}/api/generate', json.dumps(payload).encode(), {'Content-Type': 'application/json'}, method='POST'), timeout=300) as resp:
                result = json.loads(resp.read())
                return result.get('response', str(result))
        except Exception as e:
            return f'[Ollama Error] Is ollama running? {str(e)}'
