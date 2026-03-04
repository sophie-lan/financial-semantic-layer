from typing import Union

from app.models.common import BaseTrade, Currency, Party
from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption, OptionType

Trade = Union[FXForward, FXOption]

__all__ = ["BaseTrade", "Currency", "Party", "FXForward", "FXOption", "OptionType", "Trade"]
