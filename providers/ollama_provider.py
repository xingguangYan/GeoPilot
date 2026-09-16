"""Ollama Local Provider."""

from ._net import _post_json, NetworkError
from .base import BaseProvider


class OllamaProvider(BaseProvider):
    ENV_KEY = ""
    DEFAULT_URL = "http://localhost:11434"

    def __init__(self, api_key=None, model=None, base_url=None):
        super().__init__(api_key=api_key, model=model, base_url=base_url)
        # Allow Ollama to work without a base_url
        if not self.base_url:
            self.base_url = self.DEFAULT_URL

    def get_default_model(self):
        return "llama3.1"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        # Prefer /api/chat when possible for structured conversation;
        # fall back to /api/generate (prompt concatenation) for older Ollama builds.
        payload = {
            "model": self.model,
            "messages": [],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if system_prompt:
            payload["messages"].append({"role": "system", "content": system_prompt})
        for m in messages:
            role = m.get("role", "user")
            if role not in ("user", "assistant", "system"):
                role = "user"
            payload["messages"].append({"role": role, "content": m.get("content", "")})
        try:
            result = _post_json(
                f"{self.base_url}/api/chat",
                payload,
                {"Content-Type": "application/json"},
                timeout=300,
            )
            msg = result.get("message", {})
            if isinstance(msg, dict):
                content = msg.get("content")
                if content:
                    return content
            return result.get("response", str(result))
        except NetworkError:
            # Fall back to prompt concatenation endpoint
            prompt_parts = []
            if system_prompt:
                prompt_parts.append(f"System: {system_prompt}\n\n")
            for m in messages:
                prompt_parts.append(f"{m.get('role', 'user').upper()}: {m.get('content', '')}\n\n")
            prompt_parts.append("ASSISTANT: ")
            payload2 = {
                "model": self.model,
                "prompt": "".join(prompt_parts),
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            }
            try:
                r2 = _post_json(
                    f"{self.base_url}/api/generate",
                    payload2,
                    {"Content-Type": "application/json"},
                    timeout=300,
                )
                return r2.get("response", str(r2))
            except NetworkError as e:
                return f"[Ollama Error] Is Ollama running on {self.base_url}? {e}"
        except Exception as e:
            return f"[Ollama Error] {e}"
