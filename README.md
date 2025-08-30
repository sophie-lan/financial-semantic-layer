# Financial Semantic Layer

> Inspired by FINOS Legend. Decouples business logic from physical storage via a strict semantic model, mapping layer, and unified GraphQL API.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Consumers  (GraphQL clients, dashboards, downstream services)  │
└────────────────────────────┬────────────────────────────────────┘
                             │  /graphql  (Strawberry + FastAPI)
┌────────────────────────────▼────────────────────────────────────┐
│  Service Layer  ── Query resolvers, union type, schema          │
│  app/graphql/types.py  ·  app/graphql/resolvers.py             │
└────────────────────────────┬────────────────────────────────────┘
                             │  Trade = Union[FXForward, FXOption]
┌────────────────────────────▼────────────────────────────────────┐
│  Semantic Model  ── Pydantic v2 strict, all validators here     │
│  app/models/fx_forward.py  ·  app/models/fx_option.py          │
└────────────┬────────────────────────────┬───────────────────────┘
             │ ForwardSQLRepository       │ OptionNoSQLRepository
             │ (field rename + parse)     │ (coerce types + defaults)
┌────────────▼──────────┐   ┌────────────▼──────────────────────┐
│  SQL Source (SQLite)  │   │  NoSQL Source (in-memory dict)    │
│  fwd_rate, settle_dt… │   │  notional:"1000000", no premium…  │
└───────────────────────┘   └───────────────────────────────────┘
```

**Two intentionally messy sources:**

| Source | Format | Messiness |
|---|---|---|
| SQLite (`fx_forwards`) | Relational | Different field names (`fwd_rate`, `settle_dt`, `cpty_*`) |
| In-memory dict (`fx_options`) | Document | `notional` as string, missing `premium`, lowercase `option_type` |

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the server

```bash
uvicorn app.main:app --reload
```

GraphQL playground: http://localhost:8000/graphql

## Run tests

```bash
pytest -v
```

## Example GraphQL Queries

### All trades (fan-out to both sources)

```graphql
{
  trades {
    __typename
    ... on FXForward {
      tradeId
      notional
      ccyPair
      forwardRate
      settlementDate
      counterparty { name country }
    }
    ... on FXOption {
      tradeId
      notional
      ccyPair
      strike
      expiry
      optionType
      premium
      counterparty { name country }
    }
  }
}
```

### Filter by type

```graphql
{ trades(tradeType: "forward") { ... on FXForward { tradeId forwardRate } } }
{ trades(tradeType: "option")  { ... on FXOption  { tradeId strike optionType } } }
```

### Single trade lookup

```graphql
{
  trade(tradeId: "FWD-001") {
    ... on FXForward { tradeId forwardRate settlementDate }
  }
}
```

### Governance demo — surface bad data without a 500

```graphql
{
  validateTrades {
    tradeId
    errors
  }
}
```

Expected output includes `OPT-BAD` with `notional: Value error, notional must be > 0`.
