import re
from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.common import Party

_CCY_PAIR_RE = re.compile(r"^[A-Z]{3}/[A-Z]{3}$")


class OptionType(str, Enum):
    CALL = "Call"
    PUT = "Put"


class FXOption(BaseModel):
    model_config = ConfigDict(strict=True)

    trade_id: str
    notional: float
    ccy_pair: str
    strike: float
    expiry: date
    option_type: OptionType
    premium: float
    counterparty: Party

    @field_validator("notional")
    @classmethod
    def notional_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"notional must be > 0, got {v}")
        return v

    @field_validator("strike")
    @classmethod
    def strike_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"strike must be > 0, got {v}")
        return v

    @field_validator("premium")
    @classmethod
    def premium_non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"premium must be >= 0, got {v}")
        return v

    @field_validator("expiry")
    @classmethod
    def expiry_in_future(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError(f"expiry must be in the future, got {v}")
        return v

    @field_validator("ccy_pair")
    @classmethod
    def ccy_pair_format(cls, v: str) -> str:
        if not _CCY_PAIR_RE.match(v):
            raise ValueError(f"ccy_pair must match XXX/YYY format, got '{v}'")
        return v
