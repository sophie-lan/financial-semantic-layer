"""UnifiedTradeRepository: fans out to both repos concurrently."""
import asyncio
from typing import Literal

from app.models import Trade
from app.repositories.forward_repo import ForwardSQLRepository
from app.repositories.option_repo import OptionNoSQLRepository

TradeTypeFilter = Literal["forward", "option"] | None


class UnifiedTradeRepository:
    def __init__(self) -> None:
        self._forwards = ForwardSQLRepository()
        self._options = OptionNoSQLRepository()

    async def list_all(
        self,
        trade_type: TradeTypeFilter = None,
    ) -> list[Trade]:
        if trade_type == "forward":
            return await self._forwards.list_all()
        if trade_type == "option":
            return await self._options.list_all()

        # Fan-out concurrently
        forwards, options = await asyncio.gather(
            self._forwards.list_all(),
            self._options.list_all(),
        )
        return [*forwards, *options]

    async def get_by_id(self, trade_id: str) -> Trade | None:
        forward, option = await asyncio.gather(
            self._forwards.get_by_id(trade_id),
            self._options.get_by_id(trade_id),
        )
        return forward or option
