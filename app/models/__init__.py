from typing import Union

from app.models.common import Currency, Party
from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption, OptionType

Trade = Union[FXForward, FXOption]

__all__ = ["Currency", "Party", "FXForward", "FXOption", "OptionType", "Trade"]
