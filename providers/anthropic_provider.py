"""Anthropic Claude Provider"""
import json, os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    ENV_KEY = "ANTHROPIC_API_KEY"
    DEFAULT_URL = "https://api.anthropic.com/v1"
    def get_default_model(self):
        return "claude-3-5-sonnet-20241022"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
        system = system_prompt or ''
        converted = []
        for m in messages:
            if m.get('role') == 'system':
                system += '\n' + m['content']
            elif m.get('role') in ('user', 'assistant'):
                converted.append(m)
        payload = {'model': self.model, 'system': system, 'messages': converted, 'max_tokens': max_tokens, 'temperature': temperature}
        try:
            with urlopen(Request(f'{self.base_url}/messages', json.dumps(payload).encode(), headers, method='POST'), timeout=120) as resp:
                result = json.loads(resp.read())
                return result['content'][0]['text']
        except HTTPError as e:
            return f'[Claude Error {e.code}] {e.read().decode()[:500]}'
        except Exception as e:
            return f'[Claude Error] {str(e)}'
