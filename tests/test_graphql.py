"""Phase 4: GraphQL API integration tests."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.sources.sql_source import reset_db


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
# Health check
# ---------------------------------------------------------------------------

async def test_health(client: AsyncClient):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# trades() — all
# ---------------------------------------------------------------------------

async def test_graphql_trades_all(client: AsyncClient):
    query = """
    {
      trades {
        __typename
        ... on FXForward {
          tradeId
          notional
          ccyPair
        }
        ... on FXOption {
          tradeId
          notional
          ccyPair
        }
      }
    }
    """
    resp = await client.post("/graphql", json={"query": query})
    assert resp.status_code == 200
    data = resp.json()
    assert "errors" not in data, data.get("errors")
    trades = data["data"]["trades"]
    # 7 forwards + 6 valid options = 13
    assert len(trades) == 13


async def test_graphql_trades_typename_mix(client: AsyncClient):
    query = '{ trades { __typename } }'
    resp = await client.post("/graphql", json={"query": query})
    data = resp.json()["data"]["trades"]
    types = {t["__typename"] for t in data}
    assert "FXForward" in types
    assert "FXOption" in types


# ---------------------------------------------------------------------------
# trades(tradeType: ...) — filtered
# ---------------------------------------------------------------------------

async def test_graphql_trades_filter_forward(client: AsyncClient):
    query = '{ trades(tradeType: "forward") { __typename } }'
    resp = await client.post("/graphql", json={"query": query})
    data = resp.json()["data"]["trades"]
    assert len(data) == 7
    assert all(t["__typename"] == "FXForward" for t in data)


async def test_graphql_trades_filter_option(client: AsyncClient):
    query = '{ trades(tradeType: "option") { __typename } }'
    resp = await client.post("/graphql", json={"query": query})
    data = resp.json()["data"]["trades"]
    assert len(data) == 6
    assert all(t["__typename"] == "FXOption" for t in data)


# ---------------------------------------------------------------------------
# trade(tradeId: ...) — single lookup
# ---------------------------------------------------------------------------

async def test_graphql_trade_forward_by_id(client: AsyncClient):
    query = """
    {
      trade(tradeId: "FWD-001") {
        __typename
        ... on FXForward {
          tradeId
          forwardRate
          settlementDate
          counterparty { partyId name country }
        }
      }
    }
    """
    resp = await client.post("/graphql", json={"query": query})
    data = resp.json()["data"]["trade"]
    assert data["__typename"] == "FXForward"
    assert data["tradeId"] == "FWD-001"
    assert data["forwardRate"] == pytest.approx(1.0853)
    assert data["counterparty"]["name"] == "Barclays PLC"


async def test_graphql_trade_option_by_id(client: AsyncClient):
    query = """
    {
      trade(tradeId: "OPT-001") {
        __typename
        ... on FXOption {
          tradeId
          strike
          optionType
          premium
          counterparty { name }
        }
      }
    }
    """
    resp = await client.post("/graphql", json={"query": query})
    data = resp.json()["data"]["trade"]
    assert data["__typename"] == "FXOption"
    assert data["tradeId"] == "OPT-001"
    assert data["optionType"] == "Call"
    assert data["premium"] == pytest.approx(12500.0)


async def test_graphql_trade_missing(client: AsyncClient):
    query = '{ trade(tradeId: "MISSING") { __typename } }'
    resp = await client.post("/graphql", json={"query": query})
    assert resp.json()["data"]["trade"] is None


async def test_graphql_bad_record_not_exposed(client: AsyncClient):
    """OPT-BAD must never appear in any query result."""
    query = '{ trades { ... on FXOption { tradeId } } }'
    resp = await client.post("/graphql", json={"query": query})
    ids = [t.get("tradeId") for t in resp.json()["data"]["trades"]]
    assert "OPT-BAD" not in ids
