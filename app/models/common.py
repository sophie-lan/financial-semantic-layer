import re
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

_CCY_PAIR_RE = re.compile(r"^[A-Z]{3}/[A-Z]{3}$")


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


class BaseTrade(BaseModel):
    model_config = ConfigDict(strict=True)

    trade_id: str
    notional: float
    ccy_pair: str
    counterparty: Party

    @field_validator("notional")
    @classmethod
    def notional_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"notional must be > 0, got {v}")
        return v

    @field_validator("ccy_pair")
    @classmethod
    def ccy_pair_format(cls, v: str) -> str:
        if not _CCY_PAIR_RE.match(v):
            raise ValueError(f"ccy_pair must match XXX/YYY format, got '{v}'")
        valid = {c.value for c in Currency}
        base, quote = v.split("/")
        if base not in valid or quote not in valid:
            raise ValueError(f"ccy_pair legs must be known currencies, got '{v}'")
        return v
