"""Phase 5: SchemaValidator and GraphQL validation endpoint tests."""
from datetime import date, timedelta

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.sources.sql_source import reset_db
from app.validation import SchemaValidator

FUTURE = date.today() + timedelta(days=90)
PARTY_FIELDS = {"party_id": "P1", "party_name": "Corp", "party_country": "US"}


@pytest.fixture(autouse=True)
async def fresh_db():
    await reset_db()
    yield


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c


# ---------------------------------------------------------------------------
# SchemaValidator unit tests
# ---------------------------------------------------------------------------

def _good_option_doc(**overrides) -> dict:
    base = {
        "trade_id": "OPT-TEST",
        "notional": "1000000",
        "ccy_pair": "EUR/USD",
        "strike": "1.09",
        "expiry": str(FUTURE),
        "option_type": "call",
        "premium": "5000",
        **PARTY_FIELDS,
    }
    base.update(overrides)
    return base


validator = SchemaValidator()


def test_validator_valid_option():
    result = validator.validate_option(_good_option_doc())
    assert result.valid is True
    assert result.trade is not None
    assert result.errors == []


def test_validator_catches_negative_notional():
    doc = _good_option_doc(notional="-500000")
    result = validator.validate_option(doc)
    assert result.valid is False
    assert any("notional" in e for e in result.errors)


def test_validator_catches_past_expiry():
    past = str(date.today() - timedelta(days=1))
    doc = _good_option_doc(expiry=past)
    result = validator.validate_option(doc)
    assert result.valid is False
    assert any("expiry" in e for e in result.errors)


def test_validator_catches_bad_ccy_pair():
    doc = _good_option_doc(ccy_pair="EURUSD")
    result = validator.validate_option(doc)
    assert result.valid is False
    assert any("ccy_pair" in e for e in result.errors)


def test_validator_catches_negative_strike():
    doc = _good_option_doc(strike="-1.0")
    result = validator.validate_option(doc)
    assert result.valid is False
    assert any("strike" in e for e in result.errors)


def test_validator_trade_id_preserved_in_error():
    doc = _good_option_doc(trade_id="OPT-BAD", notional="-500000")
    result = validator.validate_option(doc)
    assert result.trade_id == "OPT-BAD"
    assert result.valid is False


# ---------------------------------------------------------------------------
# GraphQL validateTrades endpoint
# ---------------------------------------------------------------------------

async def test_validate_trades_query_returns_errors(client: AsyncClient):
    query = """
    {
      validateTrades {
        tradeId
        errors
      }
    }
    """
    resp = await client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    data = resp.json()
    assert "errors" not in data, data.get("errors")
    invalid = data["data"]["validateTrades"]
    assert len(invalid) >= 1


async def test_validate_trades_includes_opt_bad(client: AsyncClient):
    query = '{ validateTrades { tradeId errors } }'
    resp = await client.post("/graphql", json={"query": query})
    invalid = resp.json()["data"]["validateTrades"]
    ids = [r["tradeId"] for r in invalid]
    assert "OPT-BAD" in ids


async def test_validate_trades_error_message_meaningful(client: AsyncClient):
    query = '{ validateTrades { tradeId errors } }'
    resp = await client.post("/graphql", json={"query": query})
    invalid = resp.json()["data"]["validateTrades"]
    bad = next(r for r in invalid if r["tradeId"] == "OPT-BAD")
    # Must mention 'notional' in at least one error message
    assert any("notional" in e for e in bad["errors"])


async def test_validate_trades_no_500(client: AsyncClient):
    """Bad data must never cause a 500 — always a structured response."""
    query = '{ validateTrades { tradeId errors } }'
    resp = await client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
