"""GraphQL query resolvers — translates domain models into Strawberry types."""
from typing import Optional

import strawberry

from app.graphql.types import (
    FXForwardType,
    FXOptionType,
    PartyType,
    TradeUnion,
    ValidationErrorType,
)
from app.models import Trade
from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption
from app.repositories.unified_repo import UnifiedTradeRepository
from app.sources.nosql_source import fetch_all_options
from app.validation import SchemaValidator

_repo = UnifiedTradeRepository()
_validator = SchemaValidator()


def _party_to_gql(party) -> PartyType:
    return PartyType(
        party_id=party.party_id,
        name=party.name,
        country=party.country,
    )


def _trade_to_gql(trade: Trade) -> FXForwardType | FXOptionType:
    if isinstance(trade, FXForward):
        return FXForwardType(
            trade_id=trade.trade_id,
            notional=trade.notional,
            ccy_pair=trade.ccy_pair,
            forward_rate=trade.forward_rate,
            settlement_date=trade.settlement_date,
            counterparty=_party_to_gql(trade.counterparty),
        )
    return FXOptionType(
        trade_id=trade.trade_id,
        notional=trade.notional,
        ccy_pair=trade.ccy_pair,
        strike=trade.strike,
        expiry=trade.expiry,
        option_type=trade.option_type.value,
        premium=trade.premium,
        counterparty=_party_to_gql(trade.counterparty),
    )


@strawberry.type
class Query:
    @strawberry.field
    async def trades(
        self,
        trade_type: Optional[str] = None,
    ) -> list[TradeUnion]:
        results = await _repo.list_all(trade_type=trade_type)  # type: ignore[arg-type]
        return [_trade_to_gql(t) for t in results]

    @strawberry.field
    async def trade(
        self,
        trade_id: str,
    ) -> Optional[TradeUnion]:
        result = await _repo.get_by_id(trade_id)
        if result is None:
            return None
        return _trade_to_gql(result)

    @strawberry.field
    async def validate_trades(self) -> list[ValidationErrorType]:
        """Return structured validation errors for all invalid raw source records."""
        docs = await fetch_all_options()
        invalid: list[ValidationErrorType] = []
        for doc in docs:
            result = _validator.validate_option(doc)
            if not result.valid:
                invalid.append(
                    ValidationErrorType(
                        trade_id=result.trade_id,
                        errors=result.errors,
                    )
                )
        return invalid
