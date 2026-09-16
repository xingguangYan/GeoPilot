"""OpenAI-Compatible Provider - All APIs that follow OpenAI chat format."""

from ._net import _post_json, NetworkError
from .base import BaseProvider


class OpenAICompatibleProvider(BaseProvider):
    ENV_KEY = "OPENAI_API_KEY"
    DEFAULT_URL = "https://api.openai.com/v1"

    def get_default_model(self):
        return "gpt-4o"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        if not self.api_key and "localhost" not in (self.base_url or "") and "127.0.0.1" not in (self.base_url or ""):
            return "[Error] API key is not set. Open Provider Settings to configure."
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        # Merge system prompt if passed and messages don't already start with system
        msgs = list(messages)
        if system_prompt and (not msgs or msgs[0].get("role") != "system"):
            msgs.insert(0, {"role": "system", "content": system_prompt})
        payload = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            result = _post_json(f"{self.base_url}/chat/completions", payload, headers, timeout=120)
            return result["choices"][0]["message"]["content"]
        except NetworkError as e:
            return f"[Error] {e}"
        except (KeyError, IndexError, TypeError) as e:
            return f"[Error] Unexpected response: {e}"
        except Exception as e:  # pragma: no cover - defensive
            return f"[Error] {e}"
