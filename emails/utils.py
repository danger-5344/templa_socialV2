
import re
from urllib.parse import urlencode, urlparse, parse_qsl, urlunparse

PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([a-zA-Z0-9_\.\-]+)\s*\}\}")

def detect_placeholders(text):
    return sorted(set(PLACEHOLDER_PATTERN.findall(text or "")))

def fill_placeholders(text, mapping):
    def repl(m):
        key = m.group(1).strip()
        return str(mapping.get(key, m.group(0)))
    return PLACEHOLDER_PATTERN.sub(repl, text or "")

def append_query_params(url, params: dict):
    if not url:
        return ""
    parsed = urlparse(url)
    existing = dict(parse_qsl(parsed.query))
    existing.update({k: v for k, v in params.items() if v is not None})
    new_query = urlencode(existing, doseq=True)
    return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, new_query, parsed.fragment))
