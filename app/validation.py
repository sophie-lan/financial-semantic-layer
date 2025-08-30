"""SchemaValidator: raw dict → structured validation result.

Sits above the mapping layer and reports validation failures without raising,
so bad data surfaces cleanly as GraphQL errors rather than 500s.
"""
from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from pydantic import ValidationError

from app.models.common import Party
from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption, OptionType


@dataclass
class ValidationResult:
    trade_id: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    trade: FXForward | FXOption | None = None


def _coerce_option_dict(doc: dict) -> dict:
    """Apply the same coercions as OptionNoSQLRepository before validation."""
    return {
        "trade_id": doc["trade_id"],
        "notional": float(doc["notional"]),
        "ccy_pair": doc["ccy_pair"],
        "strike": float(doc["strike"]),
        "expiry": date.fromisoformat(doc["expiry"]),
        "option_type": OptionType(doc["option_type"].capitalize()),
        "premium": float(doc.get("premium", 0.0)),
        "counterparty": Party(
            party_id=doc["party_id"],
            name=doc["party_name"],
            country=doc["party_country"],
        ),
    }


def _coerce_forward_dict(row: dict) -> dict:
    """Apply the same coercions as ForwardSQLRepository before validation."""
    return {
        "trade_id": row["trade_id"],
        "notional": float(row["notional"]),
        "ccy_pair": row["ccy_pair"],
        "forward_rate": float(row["fwd_rate"]),
        "settlement_date": date.fromisoformat(row["settle_dt"]),
        "counterparty": Party(
            party_id=row["cpty_id"],
            name=row["cpty_name"],
            country=row["cpty_country"],
        ),
    }


class SchemaValidator:
    """Validate a raw source document against the semantic model."""

    def validate_option(self, doc: dict) -> ValidationResult:
        trade_id = doc.get("trade_id", "<unknown>")
        try:
            coerced = _coerce_option_dict(doc)
            trade = FXOption(**coerced)
            return ValidationResult(trade_id=trade_id, valid=True, trade=trade)
        except (ValidationError, ValueError, KeyError) as exc:
            errors = self._extract_errors(exc)
            return ValidationResult(trade_id=trade_id, valid=False, errors=errors)

    def validate_forward(self, row: dict) -> ValidationResult:
        trade_id = row.get("trade_id", "<unknown>")
        try:
            coerced = _coerce_forward_dict(row)
            trade = FXForward(**coerced)
            return ValidationResult(trade_id=trade_id, valid=True, trade=trade)
        except (ValidationError, ValueError, KeyError) as exc:
            errors = self._extract_errors(exc)
            return ValidationResult(trade_id=trade_id, valid=False, errors=errors)

    @staticmethod
    def _extract_errors(exc: Exception) -> list[str]:
        if isinstance(exc, ValidationError):
            return [
                f"{'.'.join(str(l) for l in e['loc'])}: {e['msg']}"
                for e in exc.errors()
            ]
        return [str(exc)]
