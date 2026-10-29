"""Cliente HTTP respetuoso: identifica al agente, respeta robots.txt, limita la tasa y reintenta."""

import logging
import os
import time
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)


def default_user_agent() -> str:
    """User-Agent identificable. El contacto se toma de MUNILENS_CONTACTO (no se versiona)."""
    contacto = os.environ.get("MUNILENS_CONTACTO", "").strip()
    sufijo = f"; contacto: {contacto}" if contacto else ""
    return f"MuniLens/0.1 (+investigacion de datos publicos{sufijo})"


class RobotsDisallowedError(RuntimeError):
    """La URL está prohibida por robots.txt; no se debe descargar."""


class PoliteClient:
    def __init__(
        self,
        user_agent: str | None = None,
        min_interval_s: float = 3.0,
        timeout_s: float = 120.0,
        max_retries: int = 3,
        session: requests.Session | None = None,
    ) -> None:
        self.user_agent = user_agent or default_user_agent()
        self.min_interval_s = min_interval_s
        self.timeout_s = timeout_s
        self._last_request = 0.0
        self._robots: dict[str, RobotFileParser] = {}
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = self.user_agent
        retry = Retry(
            total=max_retries,
            backoff_factor=5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def _robots_for(self, url: str) -> RobotFileParser:
        parts = urlsplit(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            parser = RobotFileParser()
            resp = self._raw_get(f"{base}/robots.txt")
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                # Sin robots.txt accesible: se asume permitido (comportamiento estándar).
                parser.parse([])
            self._robots[base] = parser
        return self._robots[base]

    def _throttle(self) -> None:
        wait = self.min_interval_s - (time.monotonic() - self._last_request)
        if wait > 0:
            time.sleep(wait)
        self._last_request = time.monotonic()

    def _raw_get(self, url: str) -> requests.Response:
        self._throttle()
        return self.session.get(url, timeout=self.timeout_s)

    def get(self, url: str) -> requests.Response:
        if not self._robots_for(url).can_fetch(self.user_agent, url):
            raise RobotsDisallowedError(url)
        resp = self._raw_get(url)
        log.info("GET", extra={"ctx": {"url": url, "status": resp.status_code, "bytes": len(resp.content)}})
        resp.raise_for_status()
        return resp
