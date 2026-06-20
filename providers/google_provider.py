"""Google Gemini Provider"""
import json, os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .base import BaseProvider, register_provider

class GoogleProvider(BaseProvider):
    ENV_KEY = "GOOGLE_API_KEY"
    DEFAULT_URL = "https://generativelanguage.googleapis.com/v1beta"
    def get_default_model(self):
        return "gemini-1.5-pro"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        contents = []
        for m in messages:
            role = 'user' if m['role'] in ('user', 'system') else 'model'
            contents.append({'role': role, 'parts': [{'text': m['content']}]})
        payload = {'contents': contents, 'generationConfig': {'temperature': temperature, 'maxOutputTokens': max_tokens}}
        if system_prompt:
            payload['systemInstruction'] = {'parts': [{'text': system_prompt}]}
        url = f'{self.base_url}/models/{self.model}:generateContent?key={self.api_key}'
        try:
            with urlopen(Request(url, json.dumps(payload).encode(), {'Content-Type': 'application/json'}, method='POST'), timeout=60) as resp:  # nosec
                result = json.loads(resp.read())
                return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            return f'[Gemini Error] {str(e)}'

