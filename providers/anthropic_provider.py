"""Anthropic Claude Provider."""

from ._net import _post_json, NetworkError
from .base import BaseProvider


class AnthropicProvider(BaseProvider):
    ENV_KEY = "ANTHROPIC_API_KEY"
    DEFAULT_URL = "https://api.anthropic.com/v1"

    def get_default_model(self):
        return "claude-3-5-sonnet-20241022"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        if not self.api_key:
            return "[Claude Error] API key is not set."
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        }
        system_parts = []
        converted = []
        for m in messages:
            if m.get("role") == "system":
                system_parts.append(m.get("content", ""))
            elif m.get("role") in ("user", "assistant"):
                converted.append(m)
        if system_prompt:
            system_parts.insert(0, system_prompt)
        system = "\n".join(p for p in system_parts if p)
        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": converted,
        }
        if system:
            payload["system"] = system
        try:
            result = _post_json(f"{self.base_url}/messages", payload, headers, timeout=120)
            content = result.get("content", [])
            if content and isinstance(content, list):
                texts = [b.get("text", "") for b in content if b.get("type") == "text"]
                return "\n".join(texts)
            return str(result)
        except NetworkError as e:
            return f"[Claude Error] {e}"
        except (KeyError, IndexError, TypeError) as e:
            return f"[Claude Error] Unexpected response: {e}"
        except Exception as e:
            return f"[Claude Error] {e}"
