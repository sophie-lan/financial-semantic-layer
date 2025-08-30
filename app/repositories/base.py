"""Abstract repository interface."""
from abc import ABC, abstractmethod

from app.models import Trade


class TradeRepository(ABC):
    @abstractmethod
    async def get_by_id(self, trade_id: str) -> Trade | None:
        ...

    @abstractmethod
    async def list_all(self) -> list[Trade]:
        ...
