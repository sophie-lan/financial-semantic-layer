"""ForwardSQLRepository: maps SQLite physical rows → FXForward semantic model."""
from datetime import date

from app.models.common import Party
from app.models.fx_forward import FXForward
from app.repositories.base import TradeRepository
from app.sources.sql_source import fetch_all_forwards


def _row_to_forward(row: dict) -> FXForward:
    """Rename physical fields to semantic fields and construct FXForward."""
    return FXForward(
        trade_id=row["trade_id"],
        notional=row["notional"],          # already REAL in SQLite
        ccy_pair=row["ccy_pair"],
        forward_rate=row["fwd_rate"],      # rename
        settlement_date=date.fromisoformat(row["settle_dt"]),  # rename + parse
        counterparty=Party(
            party_id=row["cpty_id"],       # rename
            name=row["cpty_name"],
            country=row["cpty_country"],
        ),
    )


class ForwardSQLRepository(TradeRepository):
    async def list_all(self) -> list[FXForward]:
        rows = await fetch_all_forwards()
        return [_row_to_forward(r) for r in rows]

    async def get_by_id(self, trade_id: str) -> FXForward | None:
        rows = await fetch_all_forwards()
        for row in rows:
            if row["trade_id"] == trade_id:
                return _row_to_forward(row)
        return None
