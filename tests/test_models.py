"""Phase 1: Domain model unit tests."""
from datetime import date, timedelta

import pytest
from pydantic import ValidationError

from app.models.common import Currency, Party
from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption, OptionType

FUTURE = date.today() + timedelta(days=90)
PARTY = Party(party_id="P001", name="Acme Bank", country="US")


# ---------------------------------------------------------------------------
# Currency
# ---------------------------------------------------------------------------

def test_currency_values():
    assert Currency.USD == "USD"
    assert Currency.EUR == "EUR"
    assert set(Currency) == {Currency.USD, Currency.EUR, Currency.GBP, Currency.JPY, Currency.CNY}


# ---------------------------------------------------------------------------
# Party
# ---------------------------------------------------------------------------

def test_party_valid():
    p = Party(party_id="P1", name="Test Corp", country="GB")
    assert p.party_id == "P1"


def test_party_strict_rejects_int_for_str():
    with pytest.raises(ValidationError):
        Party(party_id=123, name="Bad", country="US")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# FXForward — happy path
# ---------------------------------------------------------------------------

def test_fxforward_valid():
    fwd = FXForward(
        trade_id="FWD-001",
        notional=1_000_000.0,
        ccy_pair="EUR/USD",
        forward_rate=1.085,
        settlement_date=FUTURE,
        counterparty=PARTY,
    )
    assert fwd.trade_id == "FWD-001"
    assert fwd.notional == 1_000_000.0


# ---------------------------------------------------------------------------
# FXForward — validation failures
# ---------------------------------------------------------------------------

def test_fxforward_notional_zero():
    with pytest.raises(ValidationError, match="notional must be > 0"):
        FXForward(
            trade_id="FWD-X",
            notional=0.0,
            ccy_pair="EUR/USD",
            forward_rate=1.0,
            settlement_date=FUTURE,
            counterparty=PARTY,
        )


def test_fxforward_negative_rate():
    with pytest.raises(ValidationError, match="forward_rate must be > 0"):
        FXForward(
            trade_id="FWD-X",
            notional=100.0,
            ccy_pair="EUR/USD",
            forward_rate=-0.5,
            settlement_date=FUTURE,
            counterparty=PARTY,
        )


def test_fxforward_past_settlement():
    with pytest.raises(ValidationError, match="settlement_date must be in the future"):
        FXForward(
            trade_id="FWD-X",
            notional=100.0,
            ccy_pair="EUR/USD",
            forward_rate=1.0,
            settlement_date=date.today() - timedelta(days=1),
            counterparty=PARTY,
        )


def test_fxforward_bad_ccy_pair():
    with pytest.raises(ValidationError, match="ccy_pair must match XXX/YYY"):
        FXForward(
            trade_id="FWD-X",
            notional=100.0,
            ccy_pair="EURUSD",
            forward_rate=1.0,
            settlement_date=FUTURE,
            counterparty=PARTY,
        )


def test_fxforward_strict_rejects_string_notional():
    with pytest.raises(ValidationError):
        FXForward(
            trade_id="FWD-X",
            notional="1000000",  # type: ignore[arg-type]
            ccy_pair="EUR/USD",
            forward_rate=1.0,
            settlement_date=FUTURE,
            counterparty=PARTY,
        )


# ---------------------------------------------------------------------------
# FXOption — happy path
# ---------------------------------------------------------------------------

def test_fxoption_valid():
    opt = FXOption(
        trade_id="OPT-001",
        notional=500_000.0,
        ccy_pair="GBP/USD",
        strike=1.27,
        expiry=FUTURE,
        option_type=OptionType.CALL,
        premium=3_500.0,
        counterparty=PARTY,
    )
    assert opt.option_type == OptionType.CALL
    assert opt.premium == 3_500.0


def test_fxoption_zero_premium_allowed():
    opt = FXOption(
        trade_id="OPT-002",
        notional=100_000.0,
        ccy_pair="USD/JPY",
        strike=148.5,
        expiry=FUTURE,
        option_type=OptionType.PUT,
        premium=0.0,
        counterparty=PARTY,
    )
    assert opt.premium == 0.0


# ---------------------------------------------------------------------------
# FXOption — validation failures
# ---------------------------------------------------------------------------

def test_fxoption_negative_strike():
    with pytest.raises(ValidationError, match="strike must be > 0"):
        FXOption(
            trade_id="OPT-X",
            notional=100.0,
            ccy_pair="EUR/USD",
            strike=-1.0,
            expiry=FUTURE,
            option_type=OptionType.CALL,
            premium=0.0,
            counterparty=PARTY,
        )


def test_fxoption_negative_premium():
    with pytest.raises(ValidationError, match="premium must be >= 0"):
        FXOption(
            trade_id="OPT-X",
            notional=100.0,
            ccy_pair="EUR/USD",
            strike=1.1,
            expiry=FUTURE,
            option_type=OptionType.CALL,
            premium=-1.0,
            counterparty=PARTY,
        )


def test_fxoption_past_expiry():
    with pytest.raises(ValidationError, match="expiry must be in the future"):
        FXOption(
            trade_id="OPT-X",
            notional=100.0,
            ccy_pair="EUR/USD",
            strike=1.1,
            expiry=date.today() - timedelta(days=1),
            option_type=OptionType.CALL,
            premium=0.0,
            counterparty=PARTY,
        )


def test_fxoption_strict_rejects_string_notional():
    with pytest.raises(ValidationError):
        FXOption(
            trade_id="OPT-X",
            notional="500000",  # type: ignore[arg-type]
            ccy_pair="EUR/USD",
            strike=1.1,
            expiry=FUTURE,
            option_type=OptionType.CALL,
            premium=0.0,
            counterparty=PARTY,
        )
