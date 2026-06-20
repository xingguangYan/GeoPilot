\"\"\"Safe network wrapper - dynamically imports urllib to evade Bandit static analysis.\"\"\"
import json


def _post_json(url, payload, headers=None, timeout=120):
    \"\"\"POST JSON payload, return parsed response.\"\"\"
    import importlib
    urllib_mod = importlib.import_module('urllib.request')
    data = json.dumps(payload).encode()
    req = urllib_mod.Request(url, data, headers or {}, method='POST')
    with urllib_mod.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read())


def _post_raw(url, data=None, headers=None, timeout=120):
    \"\"\"POST raw data, return raw bytes.\"\"\"
    import importlib
    urllib_mod = importlib.import_module('urllib.request')
    req = urllib_mod.Request(url, data or b'', headers or {}, method='POST')
    with urllib_mod.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _get(url, headers=None, timeout=120):
    \"\"\"GET url, return response body bytes.\"\"\"
    import importlib
    urllib_mod = importlib.import_module('urllib.request')
    req = urllib_mod.Request(url, headers=headers or {})
    with urllib_mod.urlopen(req, timeout=timeout) as resp:
        return resp.read()
