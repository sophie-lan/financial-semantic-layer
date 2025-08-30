"""Phase 3: Repository layer tests."""
import pytest

from app.models.fx_forward import FXForward
from app.models.fx_option import FXOption
from app.repositories.forward_repo import ForwardSQLRepository
from app.repositories.option_repo import OptionNoSQLRepository
from app.repositories.unified_repo import UnifiedTradeRepository
from app.sources.sql_source import reset_db


@pytest.fixture(autouse=True)
async def fresh_db():
    await reset_db()
    yield


# ---------------------------------------------------------------------------
# ForwardSQLRepository
# ---------------------------------------------------------------------------

async def test_forward_repo_list_all_count():
    repo = ForwardSQLRepository()
    trades = await repo.list_all()
    assert len(trades) == 7


async def test_forward_repo_returns_fxforward_instances():
    repo = ForwardSQLRepository()
    trades = await repo.list_all()
    assert all(isinstance(t, FXForward) for t in trades)


async def test_forward_repo_field_mapping():
    repo = ForwardSQLRepository()
    trades = await repo.list_all()
    fwd = next(t for t in trades if t.trade_id == "FWD-001")
    # semantic field name, not physical
    assert fwd.forward_rate == pytest.approx(1.0853)
    assert fwd.settlement_date.year == 2026


async def test_forward_repo_get_by_id_found():
    repo = ForwardSQLRepository()
    fwd = await repo.get_by_id("FWD-003")
    assert fwd is not None
    assert fwd.trade_id == "FWD-003"
    assert isinstance(fwd, FXForward)


async def test_forward_repo_get_by_id_not_found():
    repo = ForwardSQLRepository()
    result = await repo.get_by_id("NONEXISTENT")
    assert result is None


# ---------------------------------------------------------------------------
# OptionNoSQLRepository
# ---------------------------------------------------------------------------

async def test_option_repo_list_all_excludes_bad():
    repo = OptionNoSQLRepository()
    trades = await repo.list_all()
    # OPT-BAD (negative notional) must be filtered out
    ids = [t.trade_id for t in trades]
    assert "OPT-BAD" not in ids
    assert len(trades) == 6


async def test_option_repo_returns_fxoption_instances():
    repo = OptionNoSQLRepository()
    trades = await repo.list_all()
    assert all(isinstance(t, FXOption) for t in trades)


async def test_option_repo_coerces_notional_string():
    repo = OptionNoSQLRepository()
    trades = await repo.list_all()
    opt = next(t for t in trades if t.trade_id == "OPT-001")
    assert opt.notional == 2_000_000.0
    assert isinstance(opt.notional, float)


async def test_option_repo_defaults_missing_premium():
    repo = OptionNoSQLRepository()
    trades = await repo.list_all()
    opt = next(t for t in trades if t.trade_id == "OPT-002")
    assert opt.premium == 0.0


async def test_option_repo_normalises_option_type():
    repo = OptionNoSQLRepository()
    trades = await repo.list_all()
    for opt in trades:
        assert opt.option_type.value in ("Call", "Put")


async def test_option_repo_get_by_id():
    repo = OptionNoSQLRepository()
    opt = await repo.get_by_id("OPT-003")
    assert opt is not None
    assert opt.trade_id == "OPT-003"


async def test_option_repo_get_by_id_bad_returns_none():
    repo = OptionNoSQLRepository()
    result = await repo.get_by_id("OPT-BAD")
    assert result is None


# ---------------------------------------------------------------------------
# UnifiedTradeRepository
# ---------------------------------------------------------------------------

async def test_unified_list_all_total():
    repo = UnifiedTradeRepository()
    trades = await repo.list_all()
    # 7 forwards + 6 valid options
    assert len(trades) == 13


async def test_unified_filter_forwards_only():
    repo = UnifiedTradeRepository()
    trades = await repo.list_all(trade_type="forward")
    assert all(isinstance(t, FXForward) for t in trades)
    assert len(trades) == 7


async def test_unified_filter_options_only():
    repo = UnifiedTradeRepository()
    trades = await repo.list_all(trade_type="option")
    assert all(isinstance(t, FXOption) for t in trades)
    assert len(trades) == 6


async def test_unified_get_by_id_forward():
    repo = UnifiedTradeRepository()
    trade = await repo.get_by_id("FWD-001")
    assert isinstance(trade, FXForward)


async def test_unified_get_by_id_option():
    repo = UnifiedTradeRepository()
    trade = await repo.get_by_id("OPT-001")
    assert isinstance(trade, FXOption)


async def test_unified_get_by_id_missing():
    repo = UnifiedTradeRepository()
    trade = await repo.get_by_id("MISSING-999")
    assert trade is None
