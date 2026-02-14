import hashlib
import json
import random
import time
from pathlib import Path

import requests

CACHE_DIR = Path("data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_path(namespace: str, key: str) -> Path:
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:20]
    return CACHE_DIR / f"{namespace}_{digest}.json"


def fetch_json_with_cache(
    url: str,
    *,
    params=None,
    namespace: str,
    cache_key: str,
    retries: int = 5,
    timeout: int = 20,
    min_wait: float = 1.5,
):
    """Fetch JSON with backoff and cache fallback.

    Returns (payload, source) where source is "live" or "cache".
    Raises RuntimeError when both live and cache fail.
    """
    cache_file = _cache_path(namespace, cache_key)
    session = requests.Session()
    last_error = None

    for attempt in range(retries):
        try:
            response = session.get(url, params=params, timeout=timeout)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = max(float(retry_after), min_wait)
                else:
                    wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)
                continue

            if 500 <= response.status_code < 600:
                wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)
                continue

            response.raise_for_status()
            payload = response.json()
            cache_file.write_text(json.dumps(payload), encoding="utf-8")
            return payload, "live"
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)

    if cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8")), "cache"

    raise RuntimeError(f"Fetch failed and no cache available for {cache_key}: {last_error}")


def fetch_text_with_cache(
    url: str,
    *,
    namespace: str,
    cache_key: str,
    retries: int = 5,
    timeout: int = 20,
    min_wait: float = 1.5,
):
    """Fetch text with backoff and cache fallback.

    Returns (payload, source) where source is "live" or "cache".
    """
    cache_file = _cache_path(namespace, cache_key)
    session = requests.Session()
    last_error = None

    for attempt in range(retries):
        try:
            response = session.get(url, timeout=timeout)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait = max(float(retry_after), min_wait)
                else:
                    wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)
                continue

            if 500 <= response.status_code < 600:
                wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)
                continue

            response.raise_for_status()
            payload = response.text
            cache_file.write_text(payload, encoding="utf-8")
            return payload, "live"
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                wait = max(min_wait, (2 ** attempt) + random.uniform(0.2, 1.0))
                time.sleep(wait)

    if cache_file.exists():
        return cache_file.read_text(encoding="utf-8"), "cache"

    raise RuntimeError(f"Fetch failed and no cache available for {cache_key}: {last_error}")
