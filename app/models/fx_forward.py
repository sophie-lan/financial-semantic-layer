from datetime import date

from pydantic import field_validator

from app.models.common import BaseTrade


class FXForward(BaseTrade):
    forward_rate: float
    settlement_date: date

    @field_validator("forward_rate")
    @classmethod
    def forward_rate_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError(f"forward_rate must be > 0, got {v}")
        return v

    @field_validator("settlement_date")
    @classmethod
    def settlement_in_future(cls, v: date) -> date:
        if v < date.today():
            raise ValueError(f"settlement_date must be in the future, got {v}")
        return v
