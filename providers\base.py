"""Base Provider Interface and Global Registry"""

PROVIDER_REGISTRY = {}


def register_provider(name, provider_class, display_name=None, models=None, env_key=None, default_url=None):
    PROVIDER_REGISTRY[name] = {
        "class": provider_class,
        "display_name": display_name or name.title(),
        "models": models or [],
        "env_key": env_key or getattr(provider_class, "ENV_KEY", None),
        "default_url": default_url or getattr(provider_class, "DEFAULT_URL", None),
    }


def list_providers():
    return {k: {kk: vv for kk, vv in v.items() if kk != "class"} for k, v in PROVIDER_REGISTRY.items()}


def get_provider(name, api_key=None, model=None, base_url=None, **kwargs):
    entry = PROVIDER_REGISTRY.get(name.lower())
    if not entry:
        raise ValueError(f"Unknown provider: {name}")
    return entry["class"](api_key=api_key, model=model, base_url=base_url, **kwargs)


class BaseProvider:
    ENV_KEY = "API_KEY"
    DEFAULT_URL = ""

    def __init__(self, api_key=None, model=None, base_url=None):
        self.api_key = api_key or os.environ.get(self.ENV_KEY, "")
        self.model = model or self.get_default_model()
        self.base_url = (base_url or self.DEFAULT_URL).rstrip("/")

    def get_default_model(self):
        return "default"

    def chat(self, messages, system_prompt=None, temperature=0.7, max_tokens=4096):
        raise NotImplementedError
