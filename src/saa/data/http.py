"""Shared HTTP plumbing: retrying sessions, polite throttling, secret redaction."""

from __future__ import annotations

import re
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from saa.config import HttpSettings

_SECRET_PARAMS = re.compile(r"(api_key|apikey|token)=[^&\s]+", re.IGNORECASE)


def redact(text: str) -> str:
    """Strip API keys from URLs/messages before they reach logs or run reports."""
    return _SECRET_PARAMS.sub(r"\1=***", text)


def build_session(http: HttpSettings) -> requests.Session:
    retry = Retry(
        total=http.max_retries,
        backoff_factor=http.backoff_s,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET"}),
        respect_retry_after_header=True,
        raise_on_status=False,
    )
    session = requests.Session()
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    session.headers["User-Agent"] = http.user_agent
    return session


class Throttle:
    """Enforce a minimum interval between requests (e.g. FRED allows 120 requests/minute)."""

    def __init__(self, min_interval_s: float):
        self.min_interval_s = min_interval_s
        self._last = 0.0

    def wait(self) -> None:
        delay = self._last + self.min_interval_s - time.monotonic()
        if delay > 0:
            time.sleep(delay)
        self._last = time.monotonic()


def get(
    session: requests.Session,
    url: str,
    *,
    params: dict | None = None,
    timeout: float = 60.0,
    throttle: Throttle | None = None,
) -> requests.Response:
    if throttle is not None:
        throttle.wait()
    try:
        response = session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(redact(str(exc))) from None
    return response
