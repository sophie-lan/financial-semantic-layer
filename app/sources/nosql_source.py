"""NoSQL data source: in-memory document store (intentionally dirty).

Intentional messiness to exercise the mapping layer:
  - notional stored as string "1000000" instead of float
  - some records missing 'premium' key entirely
  - option_type uses lowercase ("call"/"put") instead of "Call"/"Put"
  - one record has notional = -500000 (bad data, caught by Phase 5 validator)
"""

_DOCUMENTS: list[dict] = [
    {
        "trade_id": "OPT-001",
        "notional": "2000000",        # string — must coerce
        "ccy_pair": "EUR/USD",
        "strike": 1.0900,
        "expiry": "2026-09-15",
        "option_type": "call",        # lowercase — must normalise
        "premium": 12500.0,
        "party_id": "P002",
        "party_name": "JPMorgan Chase",
        "party_country": "US",
    },
    {
        "trade_id": "OPT-002",
        "notional": "500000",
        "ccy_pair": "GBP/USD",
        "strike": 1.2750,
        "expiry": "2026-10-20",
        "option_type": "put",
        # "premium" deliberately absent — default to 0.0
        "party_id": "P003",
        "party_name": "Deutsche Bank AG",
        "party_country": "DE",
    },
    {
        "trade_id": "OPT-003",
        "notional": "8000000",
        "ccy_pair": "USD/JPY",
        "strike": 150.00,
        "expiry": "2026-11-30",
        "option_type": "call",
        "premium": 55000.0,
        "party_id": "P005",
        "party_name": "HSBC Holdings",
        "party_country": "GB",
    },
    {
        "trade_id": "OPT-004",
        "notional": "1200000",
        "ccy_pair": "EUR/GBP",
        "strike": 0.8600,
        "expiry": "2026-08-01",
        "option_type": "put",
        # "premium" deliberately absent
        "party_id": "P004",
        "party_name": "Société Générale",
        "party_country": "FR",
    },
    {
        "trade_id": "OPT-005",
        "notional": "3500000",
        "ccy_pair": "USD/CNY",
        "strike": 7.3000,
        "expiry": "2026-12-15",
        "option_type": "call",
        "premium": 28000.0,
        "party_id": "P001",
        "party_name": "Barclays PLC",
        "party_country": "GB",
    },
    {
        "trade_id": "OPT-006",
        "notional": "900000",
        "ccy_pair": "EUR/JPY",
        "strike": 162.00,
        "expiry": "2026-09-01",
        "option_type": "put",
        "premium": 0.0,
        "party_id": "P006",
        "party_name": "BNP Paribas SA",
        "party_country": "FR",
    },
    # --- Phase 5 bad-data demo: notional is negative ---
    {
        "trade_id": "OPT-BAD",
        "notional": "-500000",        # negative — Pydantic will reject this
        "ccy_pair": "GBP/EUR",
        "strike": 1.1700,
        "expiry": "2026-10-10",
        "option_type": "call",
        "premium": 1000.0,
        "party_id": "P007",
        "party_name": "Bad Actor Ltd",
        "party_country": "XX",
    },
]


async def fetch_all_options() -> list[dict]:
    """Return raw documents — messy types and missing fields, caller maps them."""
    return list(_DOCUMENTS)
