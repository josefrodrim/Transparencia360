from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def csv_sintetico() -> bytes:
    return (FIXTURES / "pte_personal_sintetico.csv").read_bytes()
