from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .core import (
    CopyMode,
    CopySettings,
    ExecutionDecision,
    ExecutionRecord,
    PaperCopyState,
    PaperPosition,
    SourceTrade,
    TradeAction,
    run_paper_copy,
)
from .live_report import render_live_html

DATA_API_BASE = "https://data-api.polymarket.com"
CLOB_BASE = "https://clob.polymarket.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CopyBotDev/1.0"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def to_iso_timestamp(value: Any) -> str:
    if value is None:
        return ""
    try:
        raw = float(value)
    except (TypeError, ValueError):
        return str(value)
    if raw > 1_000_000_000_000:
        raw = raw / 1000.0
    return datetime.fromtimestamp(raw, tz=timezone.utc).isoformat()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def sanitize_text(value: Any) -> str:
    text = str(value or "")
    if any(token in text for token in ("Ã", "Â", "â")):
        try:
            text = text.encode("latin-1").decode("utf-8")
        except UnicodeError:
            pass
    return text


def request_json(url: str) -> Any:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def shorten_wallet(wallet: str) -> str:
    if len(wallet) < 12:
        return wallet
    return f"{wallet[:6]}...{wallet[-4:]}"


@dataclass(slots=True)
class LiveConfig:
    host: str = "127.0.0.1"
    port: int = 8875
    refresh_seconds: int = 20
    reports_dir: str = "d:/PolyMarket/copy-bot-dev/reports"
    activity_limit: int = 200
    positions_limit: int = 200
    event_history_limit: int = 40
    state_history_limit: int = 400


@dataclass(slots=True)
class SourceHolding:
    market_id: str
    asset_id: str
    question: str
    outcome: str
    shares: float
    price: float


@dataclass(slots=True)
class CopyRuntime:
    copy_id: str
    settings: CopySettings
    state: PaperCopyState
    active: bool = True
    created_at: str = field(default_factory=now_iso)
    updated_at: str = field(default_factory=now_iso)
    last_poll_at: str = ""
    last_source_trade_at: str = ""
    last_error: str = ""
    source_name: str = ""
    source_pseudonym: str = ""
    recent_events: list[dict[str, Any]] = field(default_factory=list)
    seen_trade_keys: list[str] = field(default_factory=list)
    source_holdings: dict[str, SourceHolding] = field(default_factory=dict)

    def seen_trade_set(self) -> set[str]:
        return set(self.seen_trade_keys)

    def remember_trade_key(self, key: str, limit: int) -> None:
        if key in self.seen_trade_keys:
            return
        self.seen_trade_keys.insert(0, key)
        if len(self.seen_trade_keys) > limit:
            del self.seen_trade_keys[limit:]


def fetch_activity(wallet: str, limit: int) -> list[dict[str, Any]]:
    url = f"{DATA_API_BASE}/activity?user={wallet}&type=TRADE&limit={limit}"
    payload = request_json(url)
    if not isinstance(payload, list):
        return []
    return [item for item in payload if isinstance(item, dict)]


def fetch_positions(wallet: str, limit: int) -> list[dict[str, Any]]:
    url = f"{DATA_API_BASE}/positions?user={wallet}&sizeThreshold=.1&limit={limit}&offset=0"
    payload = request_json(url)
    if not isinstance(payload, list):
        return []
    rows: list[dict[str, Any]] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        current_value = safe_float(item.get("currentValue"))
        cur_price = safe_float(item.get("curPrice"))
        size = safe_float(item.get("size"))
        if size <= 0:
            continue
        if current_value <= 0 and cur_price <= 0:
            continue
        rows.append(item)
    return rows


def fetch_book(asset_id: str) -> dict[str, Any]:
    url = f"{CLOB_BASE}/book?token_id={asset_id}"
    try:
        payload = request_json(url)
    except urllib.error.HTTPError as exc:
        if exc.code == HTTPStatus.NOT_FOUND:
            return {
                "asset_id": asset_id,
                "best_bid": 0.0,
                "best_ask": 0.0,
                "mid_price": 0.0,
                "min_order_size": 5.0,
                "tick_size": 0.01,
            }
        raise

    bids = [safe_float(item.get("price")) for item in payload.get("bids", []) if safe_float(item.get("price")) > 0]
    asks = [safe_float(item.get("price")) for item in payload.get("asks", []) if safe_float(item.get("price")) > 0]
    best_bid = max(bids) if bids else 0.0
    best_ask = min(asks) if asks else 0.0
    if best_bid and best_ask:
        mid_price = (best_bid + best_ask) / 2.0
    else:
        mid_price = best_bid or best_ask or safe_float(payload.get("last_trade_price"))
    return {
        "asset_id": asset_id,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "mid_price": mid_price,
        "min_order_size": safe_float(payload.get("min_order_size"), default=5.0),
        "tick_size": safe_float(payload.get("tick_size"), default=0.01),
    }


def build_trade_key(item: dict[str, Any]) -> str:
    tx_hash = str(item.get("transactionHash") or "")
    if tx_hash:
        return tx_hash
    return "|".join(
        [
            str(item.get("timestamp") or ""),
            str(item.get("asset") or ""),
            str(item.get("side") or ""),
            str(item.get("size") or ""),
            str(item.get("price") or ""),
        ]
    )


def build_source_trade(item: dict[str, Any], book: dict[str, Any]) -> SourceTrade:
    action = TradeAction(str(item.get("side") or "BUY"))
    market_price = book["best_ask"] if action is TradeAction.BUY else book["best_bid"]
    if market_price <= 0:
        market_price = book["mid_price"] or safe_float(item.get("price"))
    return SourceTrade(
        market_id=str(item.get("conditionId") or ""),
        asset_id=str(item.get("asset") or ""),
        question=sanitize_text(item.get("title")),
        outcome=sanitize_text(item.get("outcome")),
        action=action,
        source_price=safe_float(item.get("price")),
        market_price=market_price,
        source_usdc_size=safe_float(item.get("usdcSize")),
        timestamp=to_iso_timestamp(item.get("timestamp")),
        transaction_hash=str(item.get("transactionHash") or ""),
    )


def build_synthetic_sell(
    holding: SourceHolding,
    after_shares: float,
    book: dict[str, Any],
) -> SourceTrade | None:
    if holding.shares <= after_shares:
        return None
    market_price = book["best_bid"] or book["mid_price"] or holding.price
    if market_price <= 0:
        return None
    return SourceTrade(
        market_id=holding.market_id,
        asset_id=holding.asset_id,
        question=holding.question,
        outcome=holding.outcome,
        action=TradeAction.SELL,
        source_price=holding.price,
        market_price=market_price,
        source_usdc_size=(holding.shares - after_shares) * market_price,
        timestamp=now_iso(),
        transaction_hash=f"synthetic-sell:{holding.asset_id}:{holding.shares:.6f}:{after_shares:.6f}",
        source_position_before_shares=holding.shares,
        source_position_after_shares=after_shares,
    )


class CopyLiveManager:
    def __init__(self, config: LiveConfig):
        self.config = config
        self.reports_dir = Path(config.reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.condition = threading.Condition(self.lock)
        self.started_at = now_iso()
        self.cycle_count = 0
        self.version = 0
        self.should_stop = False
        self.last_update_at = ""
        self.last_error = ""
        self.copies: dict[str, CopyRuntime] = {}
        self._restore_state()
        self.latest_state = self.compose_state()

    def start_background_loop(self) -> threading.Thread:
        worker = threading.Thread(target=self._run_loop, name="copy-bot-live-loop", daemon=True)
        worker.start()
        return worker

    def stop(self) -> None:
        with self.condition:
            self.should_stop = True
            self.condition.notify_all()

    def add_copy(self, payload: dict[str, Any]) -> dict[str, Any]:
        settings = self._settings_from_payload(payload)
        runtime = CopyRuntime(
            copy_id=str(payload.get("copy_id") or f"copy-{int(time.time() * 1000)}"),
            settings=settings,
            state=PaperCopyState(settings=settings),
            active=bool(payload.get("active", True)),
            created_at=now_iso(),
            updated_at=now_iso(),
        )
        self._seed_runtime_cursor(runtime)
        with self.condition:
            self.copies[runtime.copy_id] = runtime
            self.version += 1
            self.latest_state = self.compose_state()
            self._persist_state()
            self.condition.notify_all()
        return self._copy_summary(runtime)

    def update_copy(self, copy_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        with self.condition:
            runtime = self.copies[copy_id]
            old_state = runtime.state
            old_wallet = runtime.settings.wallet_to_follow
            settings = self._settings_from_payload(payload, fallback=runtime.settings)
            state = PaperCopyState(settings=settings)
            target_bankroll = settings.bankroll_usdc
            current_bankroll = self._capital_base_usdc(old_state)
            bankroll_delta = target_bankroll - current_bankroll
            if bankroll_delta < 0 and old_state.cash_usdc + bankroll_delta < -1e-9:
                raise ValueError("cannot_reduce_bankroll_below_available_cash")
            state.cash_usdc = old_state.cash_usdc + bankroll_delta
            state.realized_pnl_usdc = old_state.realized_pnl_usdc
            state.positions = old_state.positions
            state.history = old_state.history
            runtime.settings = settings
            runtime.state = state
            runtime.active = bool(payload.get("active", runtime.active))
            if settings.wallet_to_follow != old_wallet:
                runtime.state = PaperCopyState(settings=settings)
                runtime.recent_events = []
                runtime.seen_trade_keys = []
                runtime.source_holdings = {}
                self._seed_runtime_cursor(runtime)
            runtime.updated_at = now_iso()
            self.version += 1
            self.latest_state = self.compose_state()
            self._persist_state()
            self.condition.notify_all()
            return self._copy_summary(runtime)

    def toggle_copy(self, copy_id: str) -> dict[str, Any]:
        with self.condition:
            runtime = self.copies[copy_id]
            runtime.active = not runtime.active
            runtime.updated_at = now_iso()
            self.version += 1
            self.latest_state = self.compose_state()
            self._persist_state()
            self.condition.notify_all()
            return self._copy_summary(runtime)

    def reset_copy(self, copy_id: str) -> dict[str, Any]:
        with self.condition:
            runtime = self.copies[copy_id]
            runtime.state = PaperCopyState(settings=runtime.settings)
            runtime.recent_events = []
            runtime.seen_trade_keys = []
            runtime.source_holdings = {}
            runtime.updated_at = now_iso()
            runtime.last_error = ""
            self._seed_runtime_cursor(runtime)
            self.version += 1
            self.latest_state = self.compose_state()
            self._persist_state()
            self.condition.notify_all()
            return self._copy_summary(runtime)

    def delete_copy(self, copy_id: str) -> None:
        with self.condition:
            self.copies.pop(copy_id, None)
            self.version += 1
            self.latest_state = self.compose_state()
            self._persist_state()
            self.condition.notify_all()

    def get_state(self) -> dict[str, Any]:
        with self.lock:
            return self.latest_state

    def wait_for_update(self, known_version: int, timeout: float) -> tuple[int, dict[str, Any]]:
        with self.condition:
            if self.version == known_version and not self.should_stop:
                self.condition.wait(timeout=timeout)
            return self.version, self.latest_state

    def _run_loop(self) -> None:
        while True:
            with self.condition:
                if self.should_stop:
                    return
            try:
                self._poll_once()
                self.last_error = ""
            except Exception as exc:  # noqa: BLE001
                self.last_error = sanitize_text(str(exc))
            with self.condition:
                self.cycle_count += 1
                self.last_update_at = now_iso()
                self.version += 1
                self.latest_state = self.compose_state()
                self._persist_state()
                self.condition.notify_all()
            time.sleep(max(3, self.config.refresh_seconds))

    def _seed_runtime_cursor(self, runtime: CopyRuntime) -> None:
        activity_rows = fetch_activity(runtime.settings.wallet_to_follow, self.config.activity_limit)
        if activity_rows:
            newest = activity_rows[0]
            runtime.source_name = sanitize_text(newest.get("name"))
            runtime.source_pseudonym = sanitize_text(newest.get("pseudonym"))
            runtime.last_source_trade_at = to_iso_timestamp(newest.get("timestamp"))
            runtime.seen_trade_keys = [
                build_trade_key(item)
                for item in activity_rows[: self.config.state_history_limit]
            ]
        else:
            runtime.seen_trade_keys = []

        position_rows = fetch_positions(runtime.settings.wallet_to_follow, self.config.positions_limit)
        holdings: dict[str, SourceHolding] = {}
        for item in position_rows:
            asset_id = str(item.get("asset") or "")
            if not asset_id:
                continue
            holdings[asset_id] = SourceHolding(
                market_id=str(item.get("conditionId") or ""),
                asset_id=asset_id,
                question=sanitize_text(item.get("title")),
                outcome=sanitize_text(item.get("outcome")),
                shares=safe_float(item.get("size")),
                price=safe_float(item.get("curPrice") or item.get("avgPrice")),
            )
        runtime.source_holdings = holdings
        runtime.last_poll_at = now_iso()

    def _poll_once(self) -> None:
        book_cache: dict[str, dict[str, Any]] = {}
        with self.lock:
            runtimes = list(self.copies.values())

        for runtime in runtimes:
            if not runtime.active:
                continue
            try:
                self._poll_runtime(runtime, book_cache)
                runtime.last_error = ""
            except Exception as exc:  # noqa: BLE001
                runtime.last_error = sanitize_text(str(exc))
            runtime.last_poll_at = now_iso()

    def _poll_runtime(self, runtime: CopyRuntime, book_cache: dict[str, dict[str, Any]]) -> None:
        activity_rows = fetch_activity(runtime.settings.wallet_to_follow, self.config.activity_limit)
        position_rows = fetch_positions(runtime.settings.wallet_to_follow, self.config.positions_limit)
        explicit_sell_assets: set[str] = set()
        seen_keys = runtime.seen_trade_set()

        if activity_rows:
            newest = activity_rows[0]
            runtime.source_name = sanitize_text(newest.get("name"))
            runtime.source_pseudonym = sanitize_text(newest.get("pseudonym"))

        new_activity = sorted(
            (item for item in activity_rows if build_trade_key(item) not in seen_keys),
            key=lambda item: safe_float(item.get("timestamp")),
        )
        for item in new_activity:
            trade_key = build_trade_key(item)
            asset_id = str(item.get("asset") or "")
            if asset_id and str(item.get("side") or "").upper() == "SELL":
                explicit_sell_assets.add(asset_id)
            trade = build_source_trade(item, self._book(asset_id, book_cache))
            self._apply_trade(runtime, trade, source="activity")
            runtime.remember_trade_key(trade_key, self.config.state_history_limit)
            runtime.last_source_trade_at = trade.timestamp or runtime.last_source_trade_at

        current_holdings: dict[str, SourceHolding] = {}
        for item in position_rows:
            asset_id = str(item.get("asset") or "")
            if not asset_id:
                continue
            current_holdings[asset_id] = SourceHolding(
                market_id=str(item.get("conditionId") or ""),
                asset_id=asset_id,
                question=sanitize_text(item.get("title")),
                outcome=sanitize_text(item.get("outcome")),
                shares=safe_float(item.get("size")),
                price=safe_float(item.get("curPrice") or item.get("avgPrice")),
            )

        for asset_id, previous in list(runtime.source_holdings.items()):
            if asset_id in explicit_sell_assets:
                continue
            current = current_holdings.get(asset_id)
            after_shares = current.shares if current else 0.0
            if previous.shares - after_shares <= 1e-6:
                continue
            trade = build_synthetic_sell(previous, after_shares, self._book(asset_id, book_cache))
            if trade is not None:
                self._apply_trade(runtime, trade, source="positions")

        self._refresh_open_position_marks(runtime, book_cache)
        runtime.source_holdings = current_holdings
        runtime.updated_at = now_iso()

    def _book(self, asset_id: str, cache: dict[str, dict[str, Any]]) -> dict[str, Any]:
        if asset_id not in cache:
            cache[asset_id] = fetch_book(asset_id)
        return cache[asset_id]

    def _refresh_open_position_marks(
        self,
        runtime: CopyRuntime,
        book_cache: dict[str, dict[str, Any]],
    ) -> None:
        for position in runtime.state.positions.values():
            book = self._book(position.asset_id, book_cache)
            next_mark = self._mark_price_from_book(book, fallback=position.last_mark_price)
            if next_mark > 0:
                position.last_mark_price = next_mark

    @staticmethod
    def _mark_price_from_book(book: dict[str, Any], fallback: float) -> float:
        best_bid = safe_float(book.get("best_bid"))
        best_ask = safe_float(book.get("best_ask"))
        mid_price = safe_float(book.get("mid_price"))
        if best_bid > 0:
            return best_bid
        if mid_price > 0:
            return mid_price
        if best_ask > 0:
            return best_ask
        return fallback

    def _apply_trade(self, runtime: CopyRuntime, trade: SourceTrade, source: str) -> None:
        run_paper_copy(settings=runtime.settings, trades=[trade], state=runtime.state)
        record = runtime.state.history[-1]
        runtime.recent_events.insert(
            0,
            {
                "timestamp": trade.timestamp or now_iso(),
                "source": source,
                "question": sanitize_text(trade.question),
                "outcome": sanitize_text(trade.outcome),
                "action": trade.action.value,
                "source_price": trade.source_price,
                "market_price": trade.market_price,
                "requested_usdc": record.decision.requested_usdc,
                "executed_usdc": record.decision.executed_usdc,
                "reason": record.decision.reason,
                "accepted": record.decision.accepted,
                "transaction_hash": trade.transaction_hash,
            },
        )
        if len(runtime.recent_events) > self.config.event_history_limit:
            del runtime.recent_events[self.config.event_history_limit :]

    def compose_state(self) -> dict[str, Any]:
        copies = [self._copy_detail(runtime) for runtime in self.copies.values()]
        copies.sort(key=lambda item: item["created_at"], reverse=True)
        total_equity = sum(item["equity_usdc"] for item in copies)
        total_bankroll = sum(item["bankroll_usdc"] for item in copies)
        total_pnl = total_equity - total_bankroll
        return {
            "generated_at": now_iso(),
            "started_at": self.started_at,
            "last_update_at": self.last_update_at,
            "last_error": self.last_error,
            "version": self.version,
            "cycle_count": self.cycle_count,
            "config": asdict(self.config),
            "summary": {
                "copies_total": len(copies),
                "copies_active": len([item for item in copies if item["active"]]),
                "total_bankroll_usdc": round(total_bankroll, 4),
                "total_equity_usdc": round(total_equity, 4),
                "total_pnl_usdc": round(total_pnl, 4),
            },
            "copies": copies,
        }

    def _copy_summary(self, runtime: CopyRuntime) -> dict[str, Any]:
        detail = self._copy_detail(runtime)
        return {
            key: detail[key]
            for key in (
                "copy_id",
                "copy_name",
                "wallet_to_follow",
                "active",
                "mode",
                "fixed_amount_usdc",
                "mirror_source_percent",
                "slippage_pct",
                "price_range",
                "max_total_usdc",
                "max_per_market_usdc",
                "bankroll_usdc",
                "equity_usdc",
                "pnl_usdc",
                "positions_open",
                "signals_processed",
                "signals_executed",
                "copied_volume_usdc",
            )
        }

    def _copy_detail(self, runtime: CopyRuntime) -> dict[str, Any]:
        snapshot = runtime.state.snapshot()
        positions = snapshot["positions"]
        history = snapshot["history"]
        pnl = snapshot["equity_usdc"] - runtime.settings.bankroll_usdc
        copied_volume = sum(
            safe_float(item.get("decision", {}).get("executed_usdc"))
            for item in history
            if item.get("decision", {}).get("accepted")
        )
        signals_executed = len(
            [item for item in history if item.get("decision", {}).get("accepted")]
        )
        return {
            "copy_id": runtime.copy_id,
            "copy_name": runtime.settings.copy_name,
            "wallet_to_follow": runtime.settings.wallet_to_follow,
            "wallet_short": shorten_wallet(runtime.settings.wallet_to_follow),
            "source_name": runtime.source_name,
            "source_pseudonym": runtime.source_pseudonym,
            "active": runtime.active,
            "created_at": runtime.created_at,
            "updated_at": runtime.updated_at,
            "last_poll_at": runtime.last_poll_at,
            "last_source_trade_at": runtime.last_source_trade_at,
            "last_error": runtime.last_error,
            "mode": runtime.settings.mode.value,
            "fixed_amount_usdc": runtime.settings.fixed_amount_usdc,
            "mirror_source_percent": runtime.settings.mirror_source_percent,
            "slippage_pct": runtime.settings.slippage_pct,
            "price_range": [runtime.settings.price_min_cents, runtime.settings.price_max_cents],
            "max_total_usdc": runtime.settings.max_total_usdc,
            "max_per_market_usdc": runtime.settings.max_per_market_usdc,
            "bankroll_usdc": runtime.settings.bankroll_usdc,
            "min_trade_usdc": runtime.settings.min_trade_usdc,
            "cash_usdc": snapshot["cash_usdc"],
            "open_exposure_usdc": snapshot["open_exposure_usdc"],
            "equity_usdc": snapshot["equity_usdc"],
            "realized_pnl_usdc": snapshot["realized_pnl_usdc"],
            "pnl_usdc": round(pnl, 4),
            "positions_open": len(positions),
            "signals_processed": len(history),
            "signals_executed": signals_executed,
            "copied_volume_usdc": round(copied_volume, 4),
            "positions": positions,
            "history": history[-30:][::-1],
            "recent_events": runtime.recent_events[:30],
        }

    def _persist_state(self) -> None:
        payload = {
            "started_at": self.started_at,
            "last_update_at": self.last_update_at,
            "last_error": self.last_error,
            "cycle_count": self.cycle_count,
            "config": asdict(self.config),
            "copies": [self._persisted_runtime(runtime) for runtime in self.copies.values()],
        }
        path = self.reports_dir / "copy_live_state.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _restore_state(self) -> None:
        path = self.reports_dir / "copy_live_state.json"
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        self.started_at = str(payload.get("started_at") or self.started_at)
        self.last_update_at = str(payload.get("last_update_at") or "")
        self.last_error = sanitize_text(payload.get("last_error"))
        self.cycle_count = int(payload.get("cycle_count") or 0)
        for item in payload.get("copies", []):
            runtime = self._runtime_from_snapshot(item)
            self.copies[runtime.copy_id] = runtime

    def _persisted_runtime(self, runtime: CopyRuntime) -> dict[str, Any]:
        return {
            "copy_id": runtime.copy_id,
            "active": runtime.active,
            "created_at": runtime.created_at,
            "updated_at": runtime.updated_at,
            "last_poll_at": runtime.last_poll_at,
            "last_source_trade_at": runtime.last_source_trade_at,
            "last_error": runtime.last_error,
            "source_name": runtime.source_name,
            "source_pseudonym": runtime.source_pseudonym,
            "settings": asdict(runtime.settings),
            "state": runtime.state.snapshot(),
            "recent_events": runtime.recent_events[: self.config.event_history_limit],
            "seen_trade_keys": runtime.seen_trade_keys[: self.config.state_history_limit],
            "source_holdings": [asdict(item) for item in runtime.source_holdings.values()],
        }

    def _runtime_from_snapshot(self, payload: dict[str, Any]) -> CopyRuntime:
        settings = self._settings_from_payload(payload.get("settings", {}))
        state = PaperCopyState(settings=settings)
        state_snapshot = payload.get("state", {})
        state.cash_usdc = safe_float(state_snapshot.get("cash_usdc"), default=settings.bankroll_usdc)
        state.realized_pnl_usdc = safe_float(state_snapshot.get("realized_pnl_usdc"))
        state.positions = {}
        for item in state_snapshot.get("positions", []):
            state.positions[str(item.get("asset_id") or "")] = self._restore_position(item)
        state.history = []
        for item in state_snapshot.get("history", []):
            state.history.append(self._restore_record(item))
        source_holdings = {
            str(item.get("asset_id") or ""): SourceHolding(
                market_id=str(item.get("market_id") or ""),
                asset_id=str(item.get("asset_id") or ""),
                question=sanitize_text(item.get("question")),
                outcome=sanitize_text(item.get("outcome")),
                shares=safe_float(item.get("shares")),
                price=safe_float(item.get("price")),
            )
            for item in payload.get("source_holdings", [])
            if str(item.get("asset_id") or "")
        }
        runtime = CopyRuntime(
            copy_id=str(payload.get("copy_id") or f"copy-{int(time.time() * 1000)}"),
            settings=settings,
            state=state,
            active=bool(payload.get("active", True)),
            created_at=str(payload.get("created_at") or now_iso()),
            updated_at=str(payload.get("updated_at") or now_iso()),
            last_poll_at=str(payload.get("last_poll_at") or ""),
            last_source_trade_at=str(payload.get("last_source_trade_at") or ""),
            last_error=sanitize_text(payload.get("last_error")),
            source_name=sanitize_text(payload.get("source_name")),
            source_pseudonym=sanitize_text(payload.get("source_pseudonym")),
            recent_events=list(payload.get("recent_events") or [])[: self.config.event_history_limit],
            seen_trade_keys=list(payload.get("seen_trade_keys") or [])[: self.config.state_history_limit],
            source_holdings=source_holdings,
        )
        self._reconcile_bankroll(runtime)
        return runtime

    def _restore_position(self, payload: dict[str, Any]) -> PaperPosition:
        return PaperPosition(
            market_id=str(payload.get("market_id") or ""),
            asset_id=str(payload.get("asset_id") or ""),
            question=sanitize_text(payload.get("question")),
            outcome=sanitize_text(payload.get("outcome")),
            shares=safe_float(payload.get("shares")),
            avg_price=safe_float(payload.get("avg_price")),
            opened_usdc=safe_float(payload.get("cost_basis")),
            last_mark_price=safe_float(payload.get("mark_price")),
        )

    def _restore_record(self, payload: dict[str, Any]) -> ExecutionRecord:
        trade_payload = payload.get("trade", {})
        decision_payload = payload.get("decision", {})
        return ExecutionRecord(
            trade=SourceTrade(
                market_id=str(trade_payload.get("market_id") or ""),
                asset_id=str(trade_payload.get("asset_id") or ""),
                question=sanitize_text(trade_payload.get("question")),
                outcome=sanitize_text(trade_payload.get("outcome")),
                action=TradeAction(str(trade_payload.get("action") or "BUY")),
                source_price=safe_float(trade_payload.get("source_price")),
                market_price=safe_float(trade_payload.get("market_price")),
                source_usdc_size=safe_float(trade_payload.get("source_usdc_size")),
                timestamp=str(trade_payload.get("timestamp") or ""),
                transaction_hash=str(trade_payload.get("transaction_hash") or ""),
                source_position_before_shares=self._maybe_float(trade_payload.get("source_position_before_shares")),
                source_position_after_shares=self._maybe_float(trade_payload.get("source_position_after_shares")),
            ),
            decision=ExecutionDecision(
                accepted=bool(decision_payload.get("accepted", False)),
                action=str(decision_payload.get("action") or ""),
                reason=str(decision_payload.get("reason") or ""),
                requested_usdc=safe_float(decision_payload.get("requested_usdc")),
                executed_usdc=safe_float(decision_payload.get("executed_usdc")),
                execution_price=safe_float(decision_payload.get("execution_price")),
                shares=safe_float(decision_payload.get("shares")),
                total_open_exposure=safe_float(decision_payload.get("total_open_exposure")),
                market_open_exposure=safe_float(decision_payload.get("market_open_exposure")),
            ),
        )

    @staticmethod
    def _maybe_float(value: Any) -> float | None:
        if value in ("", None):
            return None
        return safe_float(value)

    @staticmethod
    def _capital_base_usdc(state: PaperCopyState) -> float:
        # Initial capital contributed = cash + open cost basis - realized PnL.
        return state.cash_usdc + state.open_exposure_usdc - state.realized_pnl_usdc

    def _reconcile_bankroll(self, runtime: CopyRuntime) -> None:
        target_bankroll = runtime.settings.bankroll_usdc
        current_bankroll = self._capital_base_usdc(runtime.state)
        bankroll_delta = target_bankroll - current_bankroll
        if abs(bankroll_delta) <= 1e-9:
            return
        if bankroll_delta < 0 and runtime.state.cash_usdc + bankroll_delta < -1e-9:
            runtime.last_error = "cannot_reduce_bankroll_below_available_cash"
            return
        runtime.state.cash_usdc += bankroll_delta

    def _settings_from_payload(
        self,
        payload: dict[str, Any],
        fallback: CopySettings | None = None,
    ) -> CopySettings:
        current = fallback or CopySettings(copy_name="", wallet_to_follow="")
        copy_name = sanitize_text(payload.get("copy_name") or current.copy_name).strip()
        wallet = str(payload.get("wallet_to_follow") or current.wallet_to_follow).strip()
        if not copy_name:
            raise ValueError("copy_name_required")
        if not wallet.startswith("0x") or len(wallet) != 42:
            raise ValueError("wallet_to_follow_invalid")
        mode_raw = str(payload.get("mode") or current.mode.value)
        mode = CopyMode(mode_raw)
        settings = CopySettings(
            copy_name=copy_name,
            wallet_to_follow=wallet.lower(),
            mode=mode,
            fixed_amount_usdc=safe_float(payload.get("fixed_amount_usdc"), default=current.fixed_amount_usdc),
            mirror_source_percent=safe_float(payload.get("mirror_source_percent"), default=current.mirror_source_percent),
            slippage_pct=safe_float(payload.get("slippage_pct"), default=current.slippage_pct),
            price_min_cents=safe_float(payload.get("price_min_cents"), default=current.price_min_cents),
            price_max_cents=safe_float(payload.get("price_max_cents"), default=current.price_max_cents),
            max_total_usdc=safe_float(payload.get("max_total_usdc"), default=current.max_total_usdc),
            max_per_market_usdc=safe_float(payload.get("max_per_market_usdc"), default=current.max_per_market_usdc),
            bankroll_usdc=safe_float(payload.get("bankroll_usdc"), default=current.bankroll_usdc or 100.0),
            min_trade_usdc=safe_float(payload.get("min_trade_usdc"), default=current.min_trade_usdc or 1.0),
        )
        if settings.price_min_cents < 0 or settings.price_max_cents > 100 or settings.price_min_cents > settings.price_max_cents:
            raise ValueError("price_range_invalid")
        if settings.max_total_usdc <= 0:
            raise ValueError("max_total_invalid")
        if settings.max_per_market_usdc <= 0:
            raise ValueError("max_per_market_invalid")
        if settings.bankroll_usdc <= 0:
            raise ValueError("bankroll_invalid")
        if settings.min_trade_usdc <= 0:
            raise ValueError("min_trade_invalid")
        if settings.mode is CopyMode.FIXED_USDC and settings.fixed_amount_usdc <= 0:
            raise ValueError("fixed_amount_invalid")
        if settings.mode is CopyMode.MIRROR_SOURCE_PERCENT and settings.mirror_source_percent <= 0:
            raise ValueError("mirror_source_percent_invalid")
        return settings


def build_server(manager: CopyLiveManager) -> ThreadingHTTPServer:
    class CopyLiveHandler(BaseHTTPRequestHandler):
        server_version = "CopyBotLive/0.1"

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003 - stdlib signature
            return

        def do_GET(self) -> None:  # noqa: N802 - stdlib signature
            parsed = urlparse(self.path)
            if parsed.path == "/":
                body = render_live_html(manager.config.host, manager.config.port).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if parsed.path == "/api/state":
                body = json.dumps(manager.get_state(), ensure_ascii=False).encode("utf-8")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            if parsed.path == "/events":
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                version = -1
                try:
                    while True:
                        version, snapshot = manager.wait_for_update(version, timeout=25.0)
                        frame = f"data: {json.dumps(snapshot, ensure_ascii=False)}\n\n".encode("utf-8")
                        self.wfile.write(frame)
                        self.wfile.flush()
                        if manager.should_stop:
                            return
                except (BrokenPipeError, ConnectionResetError):
                    return

            self.send_error(HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802 - stdlib signature
            parsed = urlparse(self.path)
            try:
                payload = self._read_json()
                if parsed.path == "/api/copies/add":
                    result = manager.add_copy(payload)
                    self._send_json({"ok": True, "copy": result})
                    return
                if parsed.path == "/api/copies/update":
                    result = manager.update_copy(str(payload.get("copy_id") or ""), payload)
                    self._send_json({"ok": True, "copy": result})
                    return
                if parsed.path == "/api/copies/toggle":
                    result = manager.toggle_copy(str(payload.get("copy_id") or ""))
                    self._send_json({"ok": True, "copy": result})
                    return
                if parsed.path == "/api/copies/reset":
                    result = manager.reset_copy(str(payload.get("copy_id") or ""))
                    self._send_json({"ok": True, "copy": result})
                    return
                if parsed.path == "/api/copies/delete":
                    manager.delete_copy(str(payload.get("copy_id") or ""))
                    self._send_json({"ok": True})
                    return
            except KeyError:
                self._send_json({"ok": False, "error": "copy_not_found"}, status=HTTPStatus.NOT_FOUND)
                return
            except ValueError as exc:
                self._send_json({"ok": False, "error": sanitize_text(str(exc))}, status=HTTPStatus.BAD_REQUEST)
                return
            self.send_error(HTTPStatus.NOT_FOUND)

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0:
                return {}
            raw_body = self.rfile.read(length)
            if not raw_body:
                return {}
            return json.loads(raw_body.decode("utf-8"))

        def _send_json(self, payload: dict[str, Any], status: int = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return ThreadingHTTPServer((manager.config.host, manager.config.port), CopyLiveHandler)


def run_live_server(config: LiveConfig | None = None) -> None:
    live_config = config or LiveConfig()
    manager = CopyLiveManager(live_config)
    manager.start_background_loop()
    server = build_server(manager)
    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        manager.stop()
        server.server_close()
