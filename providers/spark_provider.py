"""iFlytek Spark Provider - HTTP compat endpoint.

iFlytek Spark 4.0/3.5 exposes an OpenAI-compatible HTTP endpoint at
``https://spark-api-open.xf-yun.com/v1/chat/completions`` using a Bearer token
formed as ``apiKey:apiSecret`` (base64-encoded by some SDKs; here we accept the
raw Bearer API password directly as configured by the user).

Because the UI only exposes one "API Key" field, users can either set the
``SPARK_API_KEY`` and ``SPARK_API_SECRET`` environment variables separately, or
paste ``apiKey:apiSecret`` into the API Key field.
"""

import base64
import os

from ._net import _post_json, NetworkError
from .base import BaseProvider


class SparkProvider(BaseProvider):
    ENV_KEY = "SPARK_APP_ID"
    DEFAULT_URL = "https://spark-api-open.xf-yun.com/v1"
    ENV_KEY_NAME = "SPARK_API_KEY"
    ENV_SK_NAME = "SPARK_API_SECRET"

    def __init__(self, api_key=None, model=None, base_url=None, **kwargs):
        # Allow "apiKey:apiSecret" shorthand in the UI field for the Bearer token
        secret = kwargs.pop("api_secret", None)
        if api_key and ":" in api_key and not secret:
            api_key, secret = api_key.split(":", 1)
        super().__init__(api_key=api_key, model=model, base_url=base_url)
        self.app_id = api_key or os.environ.get(self.ENV_KEY, "")
        self.api_key_secret = secret or os.environ.get(self.ENV_KEY_NAME, "")
        self.api_secret = os.environ.get(self.ENV_SK_NAME, "")

    def _bearer_token(self):
        """Return the bearer token; the v1 OpenAI-compat endpoint accepts
        ``APIKey:APISecret`` base64-encoded as a Bearer token."""
        raw = f"{self.api_key_secret}:{self.api_secret}".strip(":")
        if self.api_key_secret and self.api_secret:
            return base64.b64encode(raw.encode("utf-8")).decode("ascii")
        # Fall back to api_key_secret alone (already set as a bearer token by user)
        return self.api_key_secret or self.app_id

    def get_default_model(self):
        return "4.0Ultra"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        endpoint_map = {
            "4.0Ultra": "generalv3.5",
            "4.0": "generalv3",
            "3.5": "generalv3",
            "3.0": "generalv2",
        }
        spark_model = endpoint_map.get(self.model, "generalv3.5")
        msgs = []
        if system_prompt:
            msgs.append({"role": "system", "content": system_prompt})
        for m in messages:
            if m.get("role") == "system" and not system_prompt:
                msgs.append(m)
            elif m.get("role") in ("user", "assistant"):
                msgs.append(m)
        payload = {
            "model": spark_model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        headers = {
            "Authorization": f"Bearer {self._bearer_token()}",
            "Content-Type": "application/json",
        }
        try:
            result = _post_json(
                f"{self.base_url}/chat/completions", payload, headers, timeout=60
            )
            if result.get("code", 0) not in (0, None):
                return f"[Spark Error] {result.get('message', result)}"
            return result["choices"][0]["message"]["content"]
        except NetworkError as e:
            return f"[Spark Error] {e}"
        except (KeyError, IndexError, TypeError) as e:
            return f"[Spark Error] Unexpected response: {e}"
        except Exception as e:
            return f"[Spark Error] {e}"
