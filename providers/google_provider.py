"""Google Gemini Provider."""

from ._net import _post_json, NetworkError
from .base import BaseProvider


class GoogleProvider(BaseProvider):
    ENV_KEY = "GOOGLE_API_KEY"
    DEFAULT_URL = "https://generativelanguage.googleapis.com/v1beta"

    def get_default_model(self):
        return "gemini-2.0-flash"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        if not self.api_key:
            return "[Gemini Error] API key is not set."
        contents = []
        for m in messages:
            role = "user" if m.get("role") in ("user", "system") else "model"
            contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        sys_instr = system_prompt
        if not sys_instr and messages and messages[0].get("role") == "system":
            sys_instr = messages[0].get("content")
        if sys_instr:
            payload["systemInstruction"] = {"parts": [{"text": sys_instr}]}
        url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
        try:
            result = _post_json(url, payload, {"Content-Type": "application/json"}, timeout=60)
            return result["candidates"][0]["content"]["parts"][0]["text"]
        except NetworkError as e:
            return f"[Gemini Error] {e}"
        except (KeyError, IndexError, TypeError) as e:
            # Surface any error message returned by the API
            err = result.get("error", {}).get("message", str(e)) if isinstance(result, dict) else str(e)
            return f"[Gemini Error] {err}"
        except Exception as e:
            return f"[Gemini Error] {e}"
