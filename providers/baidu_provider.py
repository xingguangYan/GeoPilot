"""Baidu ERNIE Provider - Uses access_token auth.

Note: Baidu ERNIE requires an API Key (client_id) and a Secret Key (client_secret).
Because the plugin UI only exposes a single API Key field, users can either set the
BAIDU_SECRET_KEY environment variable or pass the secret key as ``api_key|secret_key``
in the API Key field.
"""

import os

from urllib.parse import urlencode

from ._net import _post_json, _get, NetworkError
from .base import BaseProvider


class BaiduProvider(BaseProvider):
    ENV_KEY = "BAIDU_API_KEY"
    DEFAULT_URL = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat"
    ENV_SK = "BAIDU_SECRET_KEY"

    def __init__(self, api_key=None, model=None, base_url=None, secret_key=None):
        # Support "api_key|secret_key" shorthand in the UI field
        if api_key and "|" in api_key and not secret_key:
            api_key, secret_key = api_key.split("|", 1)
        super().__init__(api_key=api_key, model=model, base_url=base_url)
        self.secret_key = secret_key or os.environ.get(self.ENV_SK, "")
        self._access_token = None

    def get_default_model(self):
        return "ernie-4.0-8k"

    def _get_access_token(self):
        if self._access_token:
            return self._access_token
        if not self.api_key or not self.secret_key:
            return ""
        params = urlencode(
            {
                "grant_type": "client_credentials",
                "client_id": self.api_key,
                "client_secret": self.secret_key,
            }
        )
        try:
            resp = _get(
                f"https://aip.baidubce.com/oauth/2.0/token?{params}",
                timeout=15,
            )
            import json

            self._access_token = json.loads(resp.decode("utf-8")).get("access_token", "")
        except (NetworkError, ValueError, KeyError) as e:
            return ""
        return self._access_token

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        token = self._get_access_token()
        if not token:
            return (
                "[Baidu Error] Failed to get access token. "
                "Set BAIDU_API_KEY and BAIDU_SECRET_KEY (or use 'api_key|secret_key' in the API Key field)."
            )
        endpoint_map = {
            "ernie-4.0-8k": "completions_pro",
            "ernie-3.5-8k": "completions",
            "ernie-speed": "ernie-speed",
            "ernie-lite": "ernie-lite-8k",
            "ernie-tiny": "ernie-tiny-8k",
            "ernie-speed-128k": "ernie-speed-128k",
        }
        endpoint = endpoint_map.get(self.model, "completions_pro")
        url = f"{self.base_url}/{endpoint}?access_token={token}"
        msgs = []
        for m in messages:
            if m.get("role") == "system":
                continue
            msgs.append({"role": m.get("role", "user"), "content": m.get("content", "")})
        payload = {
            "messages": msgs,
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_prompt:
            payload["system"] = system_prompt
        elif messages and messages[0].get("role") == "system":
            payload["system"] = messages[0]["content"]
        try:
            result = _post_json(url, payload, {"Content-Type": "application/json"}, timeout=60)
            if "error_code" in result:
                return f"[Baidu Error] {result.get('error_msg', result)}"
            return result.get("result", str(result))
        except NetworkError as e:
            return f"[Baidu Error] {e}"
        except Exception as e:
            return f"[Baidu Error] {e}"
