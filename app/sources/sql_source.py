"""SQL data source: SQLite with intentionally different field names.

Physical table uses:
  fwd_rate      → semantic: forward_rate
  settle_dt     → semantic: settlement_date
  cpty_id       → semantic: counterparty party_id
  cpty_name     → semantic: counterparty name
  cpty_country  → semantic: counterparty country
"""
import aiosqlite

_DB_PATH = ":memory:"
_CONN: aiosqlite.Connection | None = None

_SEED_SQL = """
CREATE TABLE IF NOT EXISTS fx_forwards (
    trade_id     TEXT PRIMARY KEY,
    notional     REAL NOT NULL,
    ccy_pair     TEXT NOT NULL,
    fwd_rate     REAL NOT NULL,
    settle_dt    TEXT NOT NULL,
    cpty_id      TEXT NOT NULL,
    cpty_name    TEXT NOT NULL,
    cpty_country TEXT NOT NULL
);

INSERT INTO fx_forwards VALUES
  ('FWD-001', 5000000.0,  'EUR/USD', 1.0853, '2026-09-15', 'P001', 'Barclays PLC',       'GB'),
  ('FWD-002', 2000000.0,  'GBP/USD', 1.2701, '2026-10-01', 'P002', 'JPMorgan Chase',     'US'),
  ('FWD-003', 10000000.0, 'USD/JPY', 148.75, '2026-11-20', 'P003', 'Deutsche Bank AG',   'DE'),
  ('FWD-004', 750000.0,   'EUR/GBP', 0.8571, '2026-08-30', 'P004', 'Société Générale',   'FR'),
  ('FWD-005', 3000000.0,  'USD/CNY', 7.2310, '2026-12-05', 'P005', 'HSBC Holdings',      'GB'),
  ('FWD-006', 1500000.0,  'EUR/JPY', 161.40, '2026-09-28', 'P001', 'Barclays PLC',       'GB'),
  ('FWD-007', 8000000.0,  'GBP/EUR', 1.1670, '2026-07-15', 'P006', 'BNP Paribas SA',     'FR');
"""


async def _get_conn() -> aiosqlite.Connection:
    global _CONN
    if _CONN is None:
        _CONN = await aiosqlite.connect(_DB_PATH)
        _CONN.row_factory = aiosqlite.Row
        await _CONN.executescript(_SEED_SQL)
        await _CONN.commit()
    return _CONN


async def fetch_all_forwards() -> list[dict]:
    """Return raw rows from SQLite — messy field names, caller must map them."""
    conn = await _get_conn()
    async with conn.execute("SELECT * FROM fx_forwards") as cur:
        rows = await cur.fetchall()
    return [dict(row) for row in rows]


async def reset_db() -> None:
    """Drop and re-seed the DB (used in tests to get a fresh state)."""
    global _CONN
    if _CONN is not None:
        await _CONN.close()
        _CONN = None
