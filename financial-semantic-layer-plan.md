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

**Two mock data sources:**
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
