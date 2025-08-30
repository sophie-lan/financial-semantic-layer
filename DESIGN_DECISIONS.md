# Design Decisions

Three key trade-offs made in this prototype, with rationale.

---

## 1. Code-first vs SDL-first GraphQL

**Choice: Code-first (Pydantic → Strawberry)**

The Pydantic domain model is the single source of truth. Strawberry types are derived from it; the SDL is generated automatically.

**Trade-off:**

| Code-first (chosen) | SDL-first |
|---|---|
| Domain model and schema always in sync | Schema can evolve independently of models |
| One place to add a field (Pydantic) | More flexible for large API-first teams |
| Easier to enforce validation in one layer | Risk of schema/model drift over time |
| Slightly harder to share schema with non-Python teams | SDL is language-agnostic, easy to share |

**In production:** SDL-first becomes attractive when the schema is owned by a separate API platform team and consumed by multiple languages. For a single-team Python backend, code-first eliminates an entire class of consistency bugs.

---

## 2. Data Virtualization (Query-time Federation) vs ETL

**Choice: Federate at query time — no data copy**

`UnifiedTradeRepository` fans out to both sources concurrently (`asyncio.gather`) and merges results in memory. No ETL pipeline, no separate data store.

**Trade-off:**

| Query-time federation (chosen) | ETL into a central store |
|---|---|
| No sync pipeline to build or maintain | Lower query latency (data pre-joined) |
| Data is always fresh from the source | Requires pipeline reliability and scheduling |
| Higher per-query latency (two network hops) | Stale data risk if pipeline lags |
| Harder to do cross-source joins or aggregations | Enables complex analytics across sources |

**Production extension:** Add a Redis cache layer in front of `UnifiedTradeRepository`. Cache TTL per source (e.g., 30 s for live rates, 5 min for reference data). This preserves the virtualization architecture while reducing tail latency.

---

## 3. Strict Mode vs Coercive Mode (Pydantic)

**Choice: `model_config = ConfigDict(strict=True)` on all models**

Pydantic's strict mode rejects implicit type coercions: `"1000000"` is not a valid `float`, `123` is not a valid `str`. All coercion must be done *explicitly* in the mapping layer before the model is constructed.

**Trade-off:**

| Strict mode (chosen) | Coercive (default) mode |
|---|---|
| Bugs in the mapping layer surface immediately | Silent coercions hide mapping errors |
| Forces all type normalisation into one layer (repositories) | Validation can happen anywhere |
| Harder to onboard new data sources (must write explicit coercion) | New sources "just work" until they don't |
| Makes the mapping layer's purpose obvious | Mapping layer can feel redundant |

**Key insight:** In a semantic layer the whole point is to make physical-to-semantic translation *explicit and auditable*. Strict mode enforces this architectural boundary at the type system level. The `OPT-BAD` demo record (notional stored as `"-500000"`) shows this in action: the coercion `float("-500000") → -500000.0` succeeds, but then the Pydantic validator `notional > 0` catches the business logic violation — a clean separation of concerns.

---

## Out of Scope (Noted for Production)

- **GraphQL subscriptions** — real-time push would require a message broker (Kafka, Redis Streams). The resolver layer is already async so the extension path is clear.
- **Authentication / RBAC** — a middleware layer on the FastAPI app (e.g., JWT verification) would sit above the GraphQL router, leaving the semantic layer untouched.
- **Production database** — swapping SQLite for Postgres requires only changing `aiosqlite` → `asyncpg` and updating the connection string in `sql_source.py`. The repository layer, models, and GraphQL schema are unaffected — which is the whole point of the architecture.
