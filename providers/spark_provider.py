"""iFlytek Spark Provider - Uses WebSocket protocol"""
import json, os, hashlib, base64, hmac, datetime, threading
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from .base import BaseProvider, register_provider

class SparkProvider(BaseProvider):
    ENV_KEY = "SPARK_APP_ID"
    ENV_KEY_NAME = "SPARK_API_KEY"  # nosec
    ENV_SECRET_NAME = "SPARK_API_SECRET"  # nosec
    def __init__(self, api_key=None, model=None, base_url=None, **kwargs):
        super().__init__(api_key, model, base_url)
        self.app_id = api_key or os.environ.get(self.ENV_KEY, '')
        self.api_key_secret = os.environ.get(self.ENV_KEY_NAME, '')
        self.api_secret = os.environ.get(self.ENV_SECRET_NAME, '')
    def get_default_model(self):
        return "4.0Ultra"
    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        # Use HTTP REST API (V3.0+ supports HTTP)
        endpoint_map = {'4.0Ultra': 'chat/completions', '3.5': 'chat/completions', '3.0': 'chat/completions'}
        endpoint = endpoint_map.get(self.model, 'chat/completions')
        url = f'https://spark-api-open.xf-yun.com/v1/{endpoint}'
        msgs = [{'role': 'system', 'content': system_prompt}] if system_prompt else []
        msgs.extend(messages)
        payload = {'model': self.model, 'messages': msgs, 'temperature': temperature, 'max_tokens': max_tokens}
        headers = {'Authorization': f'Bearer {self.api_key_secret}', 'Content-Type': 'application/json'}
        try:
            with urlopen(Request(url, json.dumps(payload).encode(), headers, method='POST'), timeout=60) as resp:
                result = json.loads(resp.read())
                return result['choices'][0]['message']['content']
        except Exception as e:
            return f'[Spark Error] {str(e)}'

