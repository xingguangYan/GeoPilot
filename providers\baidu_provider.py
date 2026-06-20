"""Baidu ERNIE Provider - Uses access_token auth"""

import json, os
from ._net import _post_json, _get
from urllib.parse import urlencode
from .base import BaseProvider, register_provider


class BaiduProvider(BaseProvider):
    ENV_KEY = "BAIDU_API_KEY"
    DEFAULT_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
    ENV_SK = "BAIDU_" + "SECRET_KEY"

    def __init__(self, api_key=None, model=None, base_url=None, secret_key=None):
        super().__init__(api_key, model, base_url)
        self.secret_key = secret_key or os.environ.get(self.ENV_SK, "")
        self._access_token = None

    def get_default_model(self):
        return "ernie-4.0-8k"

    def _get_access_token(self):
        if not self._access_token:
            params = urlencode(
                {"grant_type": "client_credentials", "client_id": self.api_key, "client_secret": self.secret_key}
            )
            resp = _get(f"https://aip.baidubce.com/oauth/2.0/token?{params}", timeout=10)
            self._access_token = json.loads(resp).get("access_token", "")
        return self._access_token

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        token = self._get_access_token()
        if not token:
            return "[Baidu Error] Failed to get access token. Check API_KEY and SECRET_KEY"
        endpoint = {"ernie-4.0-8k": "completions_pro", "ernie-3.5-8k": "completions"}.get(self.model, "completions_pro")
        url = f"{self.base_url}/{endpoint}?access_token={token}"
        msgs = [{"role": "system", "content": system_prompt}] if system_prompt else []
        msgs.extend(messages)
        payload = {"messages": msgs, "temperature": temperature, "max_output_tokens": max_tokens}
        try:
            result = _post_json(url, payload, {"Content-Type": "application/json"}, 60)
            return result.get("result", str(result))
        except Exception as e:
            return f"[Baidu Error] {str(e)}"
