from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class CopyMode(str, Enum):
    FIXED_USDC = "fixed_usdc"
    MIRROR_SOURCE_PERCENT = "mirror_source_percent"


class TradeAction(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass(slots=True)
class CopySettings:
    copy_name: str
    wallet_to_follow: str
    mode: CopyMode = CopyMode.FIXED_USDC
    fixed_amount_usdc: float = 10.0
    mirror_source_percent: float = 100.0
    slippage_pct: float = 3.0
    price_min_cents: float = 0.0
    price_max_cents: float = 100.0
    max_total_usdc: float = 100.0
    max_per_market_usdc: float = 20.0
    bankroll_usdc: float = 100.0
    min_trade_usdc: float = 1.0


@dataclass(slots=True)
class SourceTrade:
    market_id: str
    asset_id: str
    question: str
    outcome: str
    action: TradeAction
    source_price: float
    market_price: float
    source_usdc_size: float
    timestamp: str = ""
    transaction_hash: str = ""
    source_position_before_shares: float | None = None
    source_position_after_shares: float | None = None
    end_date: str = ""
    allow_zero_price_close: bool = False


@dataclass(slots=True)
class PaperPosition:
    market_id: str
    asset_id: str
    question: str
    outcome: str
    shares: float
    avg_price: float
    opened_usdc: float
    last_mark_price: float
    end_date: str = ""

    @property
    def market_value(self) -> float:
        return self.shares * self.last_mark_price

    @property
    def cost_basis(self) -> float:
        return self.shares * self.avg_price


@dataclass(slots=True)
class ExecutionDecision:
    accepted: bool
    action: str
    reason: str
    requested_usdc: float = 0.0
    executed_usdc: float = 0.0
    execution_price: float = 0.0
    shares: float = 0.0
    total_open_exposure: float = 0.0
    market_open_exposure: float = 0.0


@dataclass(slots=True)
class ExecutionRecord:
    trade: SourceTrade
    decision: ExecutionDecision


@dataclass(slots=True)
class PaperCopyState:
    settings: CopySettings
    cash_usdc: float = field(init=False)
    realized_pnl_usdc: float = 0.0
    positions: dict[str, PaperPosition] = field(default_factory=dict)
    history: list[ExecutionRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.cash_usdc = self.settings.bankroll_usdc

    @property
    def open_exposure_usdc(self) -> float:
        return sum(position.cost_basis for position in self.positions.values())

    @property
    def equity_usdc(self) -> float:
        return self.cash_usdc + sum(position.market_value for position in self.positions.values())

    def asset_exposure_usdc(self, asset_id: str) -> float:
        position = self.positions.get(asset_id)
        if position is None:
            return 0.0
        return position.cost_basis

    def market_gross_exposure_usdc(self, market_id: str) -> float:
        return sum(
            position.cost_basis
            for position in self.positions.values()
            if position.market_id == market_id
        )

    def market_exposure_usdc(self, market_id: str) -> float:
        side_exposures = [
            position.cost_basis
            for position in self.positions.values()
            if position.market_id == market_id
        ]
        if not side_exposures:
            return 0.0
        return max(side_exposures)

    def snapshot(self) -> dict[str, Any]:
        return {
            "copy_name": self.settings.copy_name,
            "wallet_to_follow": self.settings.wallet_to_follow,
            "cash_usdc": round(self.cash_usdc, 4),
            "open_exposure_usdc": round(self.open_exposure_usdc, 4),
            "equity_usdc": round(self.equity_usdc, 4),
            "realized_pnl_usdc": round(self.realized_pnl_usdc, 4),
            "positions": [
                {
                    "market_id": position.market_id,
                    "asset_id": position.asset_id,
                    "question": position.question,
                    "outcome": position.outcome,
                    "end_date": position.end_date,
                    "shares": round(position.shares, 6),
                    "avg_price": round(position.avg_price, 6),
                    "mark_price": round(position.last_mark_price, 6),
                    "market_value": round(position.market_value, 4),
                    "cost_basis": round(position.cost_basis, 4),
                }
                for position in self.positions.values()
            ],
            "history": [
                {
                    "trade": asdict(record.trade),
                    "decision": asdict(record.decision),
                }
                for record in self.history
            ],
        }


def run_paper_copy(
    settings: CopySettings,
    trades: list[SourceTrade],
    state: PaperCopyState | None = None,
) -> PaperCopyState:
    copy_state = state or PaperCopyState(settings=settings)
    for trade in trades:
        decision = _execute_trade(copy_state, trade)
        copy_state.history.append(ExecutionRecord(trade=trade, decision=decision))
    return copy_state


def _execute_trade(state: PaperCopyState, trade: SourceTrade) -> ExecutionDecision:
    if trade.market_price <= 0 and not (trade.action is TradeAction.SELL and trade.allow_zero_price_close):
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason="no_live_quote",
            execution_price=trade.market_price,
            total_open_exposure=round(state.open_exposure_usdc, 4),
            market_open_exposure=round(state.market_exposure_usdc(trade.market_id), 4),
        )

    price_cents = trade.market_price * 100.0
    total_open = state.open_exposure_usdc
    market_open = state.market_exposure_usdc(trade.market_id)

    if not trade.allow_zero_price_close and not (
        state.settings.price_min_cents <= price_cents <= state.settings.price_max_cents
    ):
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason="price_out_of_range",
            execution_price=trade.market_price,
            total_open_exposure=round(total_open, 4),
            market_open_exposure=round(market_open, 4),
        )

    if not _slippage_ok(state.settings, trade):
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason="slippage_too_high",
            execution_price=trade.market_price,
            total_open_exposure=round(total_open, 4),
            market_open_exposure=round(market_open, 4),
        )

    if trade.action is TradeAction.BUY:
        return _execute_buy(state, trade)
    return _execute_sell(state, trade)


def _execute_buy(state: PaperCopyState, trade: SourceTrade) -> ExecutionDecision:
    requested_usdc = _requested_copy_usdc(state.settings, trade)
    market_open = state.market_exposure_usdc(trade.market_id)
    side_open = state.asset_exposure_usdc(trade.asset_id)
    total_open = state.open_exposure_usdc

    # Per-market is enforced per side/outcome, not gross market notional.
    # This allows hedge/flip behavior inside the same market without freezing the copy.
    allowed_market = max(0.0, state.settings.max_per_market_usdc - side_open)
    allowed_total = max(0.0, state.settings.max_total_usdc - total_open)
    executable_usdc = min(requested_usdc, state.cash_usdc, allowed_market, allowed_total)

    if executable_usdc < state.settings.min_trade_usdc:
        if allowed_total <= 0:
            reason = "max_total_reached"
        elif allowed_market <= 0:
            reason = "max_per_market_reached"
        elif state.cash_usdc < state.settings.min_trade_usdc:
            reason = "insufficient_cash"
        else:
            reason = "below_min_trade"
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason=reason,
            requested_usdc=round(requested_usdc, 4),
            execution_price=trade.market_price,
            total_open_exposure=round(total_open, 4),
            market_open_exposure=round(market_open, 4),
        )

    shares = executable_usdc / trade.market_price
    position = state.positions.get(trade.asset_id)
    if position:
        new_cost_basis = position.cost_basis + executable_usdc
        new_shares = position.shares + shares
        position.avg_price = new_cost_basis / new_shares
        position.shares = new_shares
        position.opened_usdc += executable_usdc
        position.last_mark_price = trade.market_price
        if trade.end_date and not position.end_date:
            position.end_date = trade.end_date
    else:
        state.positions[trade.asset_id] = PaperPosition(
            market_id=trade.market_id,
            asset_id=trade.asset_id,
            question=trade.question,
            outcome=trade.outcome,
            shares=shares,
            avg_price=trade.market_price,
            opened_usdc=executable_usdc,
            last_mark_price=trade.market_price,
            end_date=trade.end_date,
        )

    state.cash_usdc -= executable_usdc
    return ExecutionDecision(
        accepted=True,
        action=trade.action.value,
        reason="executed",
        requested_usdc=round(requested_usdc, 4),
        executed_usdc=round(executable_usdc, 4),
        execution_price=trade.market_price,
        shares=round(shares, 6),
        total_open_exposure=round(state.open_exposure_usdc, 4),
        market_open_exposure=round(state.market_exposure_usdc(trade.market_id), 4),
    )


def _execute_sell(state: PaperCopyState, trade: SourceTrade) -> ExecutionDecision:
    position = state.positions.get(trade.asset_id)
    if not position or position.shares <= 0:
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason="no_position_to_sell",
            execution_price=trade.market_price,
            total_open_exposure=round(state.open_exposure_usdc, 4),
            market_open_exposure=round(state.market_exposure_usdc(trade.market_id), 4),
        )

    position.last_mark_price = trade.market_price
    requested_usdc = _requested_copy_usdc(state.settings, trade)
    if trade.allow_zero_price_close or trade.market_price <= 0:
        requested_shares = position.shares
    else:
        requested_shares = requested_usdc / trade.market_price

    sell_ratio = _source_sell_ratio(trade)
    if sell_ratio is not None:
        requested_shares = min(position.shares, position.shares * sell_ratio)

    executable_shares = min(position.shares, requested_shares)
    if not trade.allow_zero_price_close and executable_shares * trade.market_price < state.settings.min_trade_usdc:
        return ExecutionDecision(
            accepted=False,
            action=trade.action.value,
            reason="below_min_trade",
            requested_usdc=round(requested_usdc, 4),
            execution_price=trade.market_price,
            total_open_exposure=round(state.open_exposure_usdc, 4),
            market_open_exposure=round(state.market_exposure_usdc(trade.market_id), 4),
        )

    average_cost = position.avg_price
    sale_value = executable_shares * trade.market_price
    realized_cost = executable_shares * average_cost
    pnl = sale_value - realized_cost

    position.shares -= executable_shares
    position.last_mark_price = trade.market_price
    state.cash_usdc += sale_value
    state.realized_pnl_usdc += pnl

    if position.shares <= 1e-9:
        del state.positions[trade.asset_id]

    return ExecutionDecision(
        accepted=True,
        action=trade.action.value,
        reason="executed",
        requested_usdc=round(requested_usdc, 4),
        executed_usdc=round(sale_value, 4),
        execution_price=trade.market_price,
        shares=round(executable_shares, 6),
        total_open_exposure=round(state.open_exposure_usdc, 4),
        market_open_exposure=round(state.market_exposure_usdc(trade.market_id), 4),
    )


def _requested_copy_usdc(settings: CopySettings, trade: SourceTrade) -> float:
    if settings.mode is CopyMode.FIXED_USDC:
        return settings.fixed_amount_usdc
    return trade.source_usdc_size * (settings.mirror_source_percent / 100.0)


def _slippage_ok(settings: CopySettings, trade: SourceTrade) -> bool:
    if trade.allow_zero_price_close:
        return True
    source = trade.source_price
    if source <= 0:
        return False
    tolerance = settings.slippage_pct / 100.0
    if trade.action is TradeAction.BUY:
        max_acceptable = source * (1.0 + tolerance)
        return trade.market_price <= max_acceptable
    min_acceptable = source * (1.0 - tolerance)
    return trade.market_price >= min_acceptable


def _source_sell_ratio(trade: SourceTrade) -> float | None:
    before = trade.source_position_before_shares
    after = trade.source_position_after_shares
    if before is None or after is None or before <= 0:
        return None
    sold = max(0.0, before - after)
    return min(1.0, sold / before)
