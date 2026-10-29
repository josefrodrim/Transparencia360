from unittest.mock import MagicMock

import pytest

from munilens_scrapers.cli import periodos
from munilens_scrapers.client import PoliteClient, RobotsDisallowedError


def _resp(status, text=""):
    r = MagicMock(status_code=status, text=text, content=text.encode())
    return r


def test_periodos_cruza_anio():
    assert list(periodos("2025-11", "2026-02")) == [(2025, 11), (2025, 12), (2026, 1), (2026, 2)]


def test_respeta_robots_txt():
    session = MagicMock(headers={})
    session.get.return_value = _resp(200, "User-agent: *\nDisallow: /privado\n")
    c = PoliteClient(min_interval_s=0, session=session)
    with pytest.raises(RobotsDisallowedError):
        c.get("https://ejemplo.gob.pe/privado/x")
    session.get.return_value = _resp(200, "ok")
    assert c.get("https://ejemplo.gob.pe/publico").status_code == 200


def test_user_agent_toma_contacto_del_entorno(monkeypatch):
    monkeypatch.delenv("MUNILENS_CONTACTO", raising=False)
    assert "contacto" not in PoliteClient(session=MagicMock(headers={})).user_agent
    monkeypatch.setenv("MUNILENS_CONTACTO", "ops@ejemplo.org")
    assert PoliteClient(session=MagicMock(headers={})).user_agent.endswith("contacto: ops@ejemplo.org)")
