import re
from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.common import Party

_CCY_PAIR_RE = re.compile(r"^[A-Z]{3}/[A-Z]{3}$")


class FXForward(BaseModel):
    model_config = ConfigDict(strict=True)

    trade_id: str
    notional: float
    ccy_pair: str
    forward_rate: float
    settlement_date: date
    counterparty: Party

    @field_validator("notional")
    @classmethod
    def notional_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"notional must be > 0, got {v}")
        return v

    @field_validator("forward_rate")
    @classmethod
    def forward_rate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"forward_rate must be > 0, got {v}")
        return v

    @field_validator("settlement_date")
    @classmethod
    def settlement_in_future(cls, v: date) -> date:
        if v <= date.today():
            raise ValueError(f"settlement_date must be in the future, got {v}")
        return v

    @field_validator("ccy_pair")
    @classmethod
    def ccy_pair_format(cls, v: str) -> str:
        if not _CCY_PAIR_RE.match(v):
            raise ValueError(f"ccy_pair must match XXX/YYY format, got '{v}'")
        return v
