"""Google Gemini Provider"""

from ._net import _post_json
from .base import BaseProvider, register_provider


class GoogleProvider(BaseProvider):
    ENV_KEY = "GOOGLE_API_KEY"
    DEFAULT_URL = "https://generativelanguage.googleapis.com/v1beta"

    def get_default_model(self):
        return "gemini-1.5-pro"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        contents = []
        for m in messages:
            role = "user" if m["role"] in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m["content"]}]})
        payload = {
            "contents": contents,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        try:
            result = _post_json(url, payload, {"Content-Type": "application/json"}, 60)
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return f"[Gemini Error] {str(e)}"
