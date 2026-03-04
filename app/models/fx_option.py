from datetime import date
from enum import Enum

from pydantic import field_validator

from app.models.common import BaseTrade


class OptionType(str, Enum):
    CALL = "Call"
    PUT = "Put"


class FXOption(BaseTrade):
    strike: float
    expiry: date
    option_type: OptionType
    premium: float

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
        if v < date.today():
            raise ValueError(f"expiry must be in the future, got {v}")
        return v
