\"\"\"Anthropic Claude Provider\"\"\"
import json, os
from ._net import _post_json
from .base import BaseProvider

class AnthropicProvider(BaseProvider):
    ENV_KEY = 'ANTHROPIC_API_KEY'
    DEFAULT_URL = 'https://api.anthropic.com/v1'
    def get_default_model(self):
        return 'claude-3-5-sonnet-20241022'
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        headers = {'x-api-key': self.api_key, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'}
        system = system_prompt or ''
        converted = []
        for m in messages:
            if m.get('role') == 'system':
                system += chr(10) + m['content']
            elif m.get('role') in ('user', 'assistant'):
                converted.append(m)
        payload = {'model': self.model, 'system': system, 'messages': converted, 'max_tokens': max_tokens, 'temperature': temperature}
        try:
            result = _post_json(f'{self.base_url}/messages', payload, headers, 120)
            return result['content'][0]['text']
        except Exception as e:
            return f'[Claude Error] {str(e)}'
