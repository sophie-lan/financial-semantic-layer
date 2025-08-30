"""Phase 2: Raw data source sanity tests."""
import pytest

from app.sources.nosql_source import fetch_all_options
from app.sources.sql_source import fetch_all_forwards, reset_db


@pytest.fixture(autouse=True)
async def fresh_db():
    await reset_db()
    yield


# ---------------------------------------------------------------------------
# SQL source
# ---------------------------------------------------------------------------

async def test_sql_returns_rows():
    rows = await fetch_all_forwards()
    assert len(rows) == 7


async def test_sql_uses_physical_field_names():
    rows = await fetch_all_forwards()
    first = rows[0]
    # Physical names must be present
    assert "fwd_rate" in first
    assert "settle_dt" in first
    # Semantic names must NOT be present
    assert "forward_rate" not in first
    assert "settlement_date" not in first


async def test_sql_all_have_trade_id():
    rows = await fetch_all_forwards()
    for row in rows:
        assert row["trade_id"].startswith("FWD-")


# ---------------------------------------------------------------------------
# NoSQL source
# ---------------------------------------------------------------------------

async def test_nosql_returns_docs():
    docs = await fetch_all_options()
    assert len(docs) == 7  # 6 good + 1 bad


async def test_nosql_notional_is_string():
    docs = await fetch_all_options()
    good = [d for d in docs if d["trade_id"] != "OPT-BAD"]
    for doc in good:
        assert isinstance(doc["notional"], str), f"{doc['trade_id']} notional should be str"


async def test_nosql_some_missing_premium():
    docs = await fetch_all_options()
    missing = [d for d in docs if "premium" not in d]
    assert len(missing) >= 2


async def test_nosql_option_type_lowercase():
    docs = await fetch_all_options()
    for doc in docs:
        assert doc["option_type"] in ("call", "put")


async def test_nosql_bad_record_present():
    docs = await fetch_all_options()
    bad = next((d for d in docs if d["trade_id"] == "OPT-BAD"), None)
    assert bad is not None
    assert bad["notional"] == "-500000"
