"""Strawberry GraphQL types derived from Pydantic models (code-first, no SDL)."""
from datetime import date
from typing import Annotated

import strawberry


@strawberry.type
class PartyType:
    party_id: str
    name: str
    country: str


@strawberry.type(name="FXForward")
class FXForwardType:
    trade_id: str
    notional: float
    ccy_pair: str
    forward_rate: float
    settlement_date: date
    counterparty: PartyType


@strawberry.type(name="FXOption")
class FXOptionType:
    trade_id: str
    notional: float
    ccy_pair: str
    strike: float
    expiry: date
    option_type: str        # expose as plain str; enum is internal domain detail
    premium: float
    counterparty: PartyType


# Union type — resolvers return this
TradeUnion = Annotated[
    FXForwardType | FXOptionType,
    strawberry.union("Trade"),
]


@strawberry.type
class ValidationErrorType:
    trade_id: str
    errors: list[str]
