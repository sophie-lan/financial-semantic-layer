from enum import Enum

from pydantic import BaseModel, ConfigDict


class Currency(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    JPY = "JPY"
    CNY = "CNY"


class Party(BaseModel):
    model_config = ConfigDict(strict=True)

    party_id: str
    name: str
    country: str
