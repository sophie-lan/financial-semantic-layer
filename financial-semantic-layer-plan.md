# Financial Semantic Layer — Project Plan

> Inspired by FINOS Legend. Goal: decouple business logic from physical storage via a strict semantic model, mapping layer, and unified GraphQL API.

---

## Architecture Overview

```
[Physical Storage]     ←── raw data, messy, source-specific
        ↑ Mapping / Repository Layer
[Semantic Model]       ←── business entities, strictly typed, storage-agnostic
        ↑ Service Layer
[Query Interface]      ←── unified GraphQL API, consumers don't care where data lives
```

| Legend Layer | Our Stack | Role |
|---|---|---|
| Domain Model | **Pydantic v2** | Define FXOption / FXForward / Party, strict types + auto validation |
| Mapping Layer | **Repository Pattern** | One adapter per source, translates physical data into semantic model |
| Service / Query Layer | **Strawberry + FastAPI** | Code-first GraphQL schema, unified endpoint |

**Two mock data sources (intentionally messy):**
- `SQL source` → SQLite, stores FX Forwards (relational, field names differ from model)
- `NoSQL source` → Python dict/JSON, stores FX Options (document-style, missing fields, type inconsistencies)

---

## Directory Structure

```
financial-semantic-layer/
├── app/
│   ├── models/              # Pydantic domain models (semantic layer)
│   │   ├── __init__.py
│   │   ├── common.py        # Currency enum, Party, shared validators
│   │   ├── fx_forward.py
│   │   └── fx_option.py
│   ├── sources/             # Physical data source adapters
│   │   ├── sql_source.py    # SQLite seed + async read
│   │   └── nosql_source.py  # In-memory dict mock
│   ├── repositories/        # Repository pattern (unified interface)
│   │   ├── base.py          # Abstract TradeRepository
│   │   ├── forward_repo.py
│   │   ├── option_repo.py
│   │   └── unified_repo.py  # Fan-out across both sources
│   ├── graphql/             # Strawberry types + resolvers
│   │   ├── types.py
│   │   └── resolvers.py
│   └── main.py              # FastAPI app entry
├── tests/
│   ├── test_models.py
│   └── test_repos.py
├── README.md
├── DESIGN_DECISIONS.md
└── requirements.txt
```

---

## TODO List

### Phase 0 — Project Init
- [ ] Create directory structure as above
- [ ] Write `requirements.txt`: `fastapi`, `strawberry-graphql[fastapi]`, `pydantic>=2.0`, `uvicorn`, `aiosqlite`

### Phase 1 — Domain Model (Semantic Layer Core)
- [ ] `common.py`: Define `Currency` enum (ISO 4217 subset: USD, EUR, GBP, JPY, CNY)
- [ ] `common.py`: Define `Party` model (`party_id`, `name`, `country`)
- [ ] `fx_forward.py`: Define `FXForward` model
  - Fields: `trade_id`, `notional`, `ccy_pair`, `forward_rate`, `settlement_date`, `counterparty: Party`
  - Validators: `notional > 0`, `forward_rate > 0`, `settlement_date` in future, `ccy_pair` format `XXX/YYY`
- [ ] `fx_option.py`: Define `FXOption` model
  - Fields: `trade_id`, `notional`, `ccy_pair`, `strike`, `expiry`, `option_type` (Call/Put enum), `premium`, `counterparty: Party`
  - Validators: `strike > 0`, `premium >= 0`, `expiry` in future, same `ccy_pair` format
- [ ] `__init__.py`: Export `Trade = Union[FXForward, FXOption]`
- [ ] Use `model_config = ConfigDict(strict=True)` on all models

### Phase 2 — Mock Data Sources (Physical Layer)
- [ ] `sql_source.py`:
  - Seed SQLite with an `fx_forwards` table (5–10 rows)
  - Intentionally use different field names: e.g. `fwd_rate` instead of `forward_rate`, `settle_dt` instead of `settlement_date`
  - Expose `async def fetch_all_forwards() -> list[dict]`
- [ ] `nosql_source.py`:
  - Python list of dicts simulating a document store (5–10 FX Options)
  - Intentionally include: missing `premium` on some records, `notional` stored as string `"1000000"` instead of int
  - Expose `async def fetch_all_options() -> list[dict]`

### Phase 3 — Mapping / Repository Layer
- [ ] `base.py`: Define abstract `TradeRepository` with `async def get_by_id`, `async def list_all`
- [ ] `forward_repo.py`: Implement `ForwardSQLRepository`
  - Fetch from SQLite → rename fields (`fwd_rate` → `forward_rate`, etc.) → construct `FXForward`
- [ ] `option_repo.py`: Implement `OptionNoSQLRepository`
  - Fetch from dict source → fill missing defaults → coerce types → construct `FXOption`
- [ ] `unified_repo.py`: Implement `UnifiedTradeRepository`
  - Fan-out to both repos concurrently (`asyncio.gather`)
  - Merge and return as `list[Trade]`
  - Support optional `trade_type` filter (`"forward"` | `"option"`)

### Phase 4 — GraphQL Schema & Resolvers (Service Layer)
- [ ] `types.py`: Define Strawberry types `FXForwardType`, `FXOptionType`, `PartyType` derived from Pydantic models
- [ ] `types.py`: Define `TradeUnion = strawberry.union("Trade", [FXForwardType, FXOptionType])`
- [ ] `resolvers.py`: Implement query resolvers
  - `trades(trade_type: Optional[str]) -> list[TradeUnion]`
  - `trade(trade_id: str) -> TradeUnion`
- [ ] `main.py`: Mount Strawberry GraphQL app onto FastAPI at `/graphql`

### Phase 5 — Validation & Governance Demo
- [ ] Write `SchemaValidator` util: raw dict → attempt Pydantic construction → return structured validation errors
- [ ] Add a bad data demo entry in `nosql_source.py`: one record with `notional = -500000` to demonstrate interception
- [ ] Ensure validation errors surface cleanly through the resolver (not a 500, but a structured error message)

### Phase 6 — Docs & Interview Materials
- [ ] `README.md`: ASCII architecture diagram + setup instructions + example GraphQL queries
- [ ] `DESIGN_DECISIONS.md`: Three key trade-offs (see Rules section below)

---

## Rules

### Code Standards
1. **Pydantic v2 strict mode** — `model_config = ConfigDict(strict=True)` on all models. No silent type coercion.
2. **Code-first only** — Strawberry types must be derived from Pydantic models. Never hand-write SDL.
3. **Layer isolation** — `repositories/` must not import anything from `graphql/` or `fastapi`. Dependency only flows upward.
4. **Business validation lives in `models/` only** — Repositories do field mapping; they do not enforce business rules.
5. **Async everywhere** — All repository methods use `async def`. SQL access uses `aiosqlite`.
6. **Mock data must be intentionally dirty** — The whole point is to show the mapping layer doing real work. Clean mock data defeats the purpose.

### What Must Be Demo-able in an Interview (15-Min Rule)
- [ ] One GraphQL query that fans out to both sources and returns a unified `[Trade]` list
- [ ] One bad record that gets caught by Pydantic validation with a clear error message
- [ ] Explain verbally: why validation is in the model layer, not the resolver
- [ ] Explain verbally: how you'd swap SQLite for Postgres without touching the GraphQL layer

### DESIGN_DECISIONS.md — Three Trade-offs to Document
1. **Code-first vs SDL-first**: We chose code-first (Pydantic → Strawberry) so the domain model is the single source of truth. SDL-first is more flexible for large teams but risks schema/model drift.
2. **Data Virtualization vs ETL**: We federate at query time (no data copy). Trade-off: higher query latency vs. no sync pipeline to maintain. Production extension would add a cache layer.
3. **Strict mode vs Coercive mode**: Pydantic strict mode rejects `"1000000"` as a float. This forces all coercion to happen explicitly in the mapping layer, making bugs visible rather than silent.

### Out of Scope (Intentional)
- GraphQL subscriptions (real-time push) — noted in DESIGN_DECISIONS as a production extension path
- Authentication / RBAC — out of scope for this prototype
- Production database — SQLite + in-memory dict is sufficient to demonstrate the pattern
