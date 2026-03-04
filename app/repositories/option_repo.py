"""OptionNoSQLRepository: maps NoSQL docs → FXOption semantic model.

Coercions performed here (not in the model — strict=True forbids silent coercion):
  - notional: str → float
  - option_type: lowercase → title-case ("call" → "Call")
  - premium: missing key → default 0.0
  - expiry: ISO string → date
"""
import logging
from datetime import date

from pydantic import ValidationError

from app.models.common import Party
from app.models.fx_option import FXOption, OptionType
from app.repositories.base import TradeRepository
from app.sources.nosql_source import fetch_all_options

logger = logging.getLogger(__name__)


def _doc_to_option(doc: dict) -> FXOption:
    """Coerce and map a raw NoSQL document to FXOption."""
    return FXOption(
        trade_id=doc["trade_id"],
        notional=float(doc["notional"]),          # coerce str → float
        ccy_pair=doc["ccy_pair"],
        strike=float(doc["strike"]),
        expiry=date.fromisoformat(doc["expiry"]),  # coerce str → date
        option_type=OptionType(doc["option_type"].capitalize()),  # normalise case
        premium=float(doc.get("premium", 0.0)),   # default missing to 0.0
        counterparty=Party(
            party_id=doc["party_id"],
            name=doc["party_name"],
            country=doc["party_country"],
        ),
    )


class OptionNoSQLRepository(TradeRepository):
    async def list_all(self) -> list[FXOption]:
        docs = await fetch_all_options()
        results: list[FXOption] = []
        for doc in docs:
            try:
                results.append(_doc_to_option(doc))
            except (ValidationError, ValueError) as e:
                logger.warning(
                    "Skipping invalid option doc trade_id=%s: %s",
                    doc.get("trade_id", "?"),
                    e,
                )
        return results

    async def get_by_id(self, trade_id: str) -> FXOption | None:
        docs = await fetch_all_options()
        for doc in docs:
            if doc["trade_id"] == trade_id:
                try:
                    return _doc_to_option(doc)
                except (ValidationError, ValueError):
                    return None
        return None
