from __future__ import annotations

import argparse
import json
from pathlib import Path

from copy_bot_dev import CopyMode, CopySettings, SourceTrade, TradeAction, run_paper_copy


DEMO_TRADES = [
    {
        "market_id": "atl-68-69f-mar13",
        "asset_id": "atl-no-68-69f",
        "question": "Will the highest temperature in Atlanta be between 68-69°F on March 13?",
        "outcome": "NO",
        "action": "BUY",
        "source_price": 0.52,
        "market_price": 0.53,
        "source_usdc_size": 250.0,
        "timestamp": "2026-03-13T18:00:00Z",
    },
    {
        "market_id": "atl-68-69f-mar13",
        "asset_id": "atl-no-68-69f",
        "question": "Will the highest temperature in Atlanta be between 68-69°F on March 13?",
        "outcome": "NO",
        "action": "BUY",
        "source_price": 0.52,
        "market_price": 0.58,
        "source_usdc_size": 250.0,
        "timestamp": "2026-03-13T18:01:00Z",
    },
    {
        "market_id": "sea-42-43f-mar13",
        "asset_id": "sea-no-42-43f",
        "question": "Will the highest temperature in Seattle be between 42-43°F on March 13?",
        "outcome": "NO",
        "action": "BUY",
        "source_price": 0.89,
        "market_price": 0.89,
        "source_usdc_size": 400.0,
        "timestamp": "2026-03-13T18:02:00Z",
    },
    {
        "market_id": "sea-42-43f-mar13",
        "asset_id": "sea-no-42-43f",
        "question": "Will the highest temperature in Seattle be between 42-43°F on March 13?",
        "outcome": "NO",
        "action": "SELL",
        "source_price": 0.91,
        "market_price": 0.90,
        "source_usdc_size": 200.0,
        "timestamp": "2026-03-13T18:10:00Z",
        "source_position_before_shares": 1000.0,
        "source_position_after_shares": 500.0,
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Paper copy bot simulator")
    parser.add_argument("--scenario", help="Path to a JSON file with trade events")
    parser.add_argument("--json-out", help="Optional path to write final JSON state")
    parser.add_argument("--copy-name", default="Paper Copy")
    parser.add_argument("--wallet", default="0x0000000000000000000000000000000000000000")
    parser.add_argument(
        "--mode",
        choices=[mode.value for mode in CopyMode],
        default=CopyMode.FIXED_USDC.value,
    )
    parser.add_argument("--bankroll", type=float, default=100.0)
    parser.add_argument("--fixed-amount", type=float, default=10.0)
    parser.add_argument("--mirror-percent", type=float, default=10.0)
    parser.add_argument("--slippage-pct", type=float, default=3.0)
    parser.add_argument("--price-min-cents", type=float, default=0.0)
    parser.add_argument("--price-max-cents", type=float, default=100.0)
    parser.add_argument("--max-total", type=float, default=100.0)
    parser.add_argument("--max-per-market", type=float, default=20.0)
    parser.add_argument("--min-trade", type=float, default=1.0)
    return parser.parse_args()


def load_trades(path: str | None) -> list[SourceTrade]:
    payload = DEMO_TRADES
    if path:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        SourceTrade(
            market_id=item["market_id"],
            asset_id=item["asset_id"],
            question=item["question"],
            outcome=item["outcome"],
            action=TradeAction(item["action"]),
            source_price=float(item["source_price"]),
            market_price=float(item["market_price"]),
            source_usdc_size=float(item["source_usdc_size"]),
            timestamp=item.get("timestamp", ""),
            transaction_hash=item.get("transaction_hash", ""),
            source_position_before_shares=_to_float(item.get("source_position_before_shares")),
            source_position_after_shares=_to_float(item.get("source_position_after_shares")),
        )
        for item in payload
    ]


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)


def main() -> None:
    args = parse_args()
    settings = CopySettings(
        copy_name=args.copy_name,
        wallet_to_follow=args.wallet,
        mode=CopyMode(args.mode),
        fixed_amount_usdc=args.fixed_amount,
        mirror_source_percent=args.mirror_percent,
        slippage_pct=args.slippage_pct,
        price_min_cents=args.price_min_cents,
        price_max_cents=args.price_max_cents,
        max_total_usdc=args.max_total,
        max_per_market_usdc=args.max_per_market,
        bankroll_usdc=args.bankroll,
        min_trade_usdc=args.min_trade,
    )

    state = run_paper_copy(settings=settings, trades=load_trades(args.scenario))
    snapshot = state.snapshot()
    output = {
        "summary": {
            "copy_name": snapshot["copy_name"],
            "wallet_to_follow": snapshot["wallet_to_follow"],
            "cash_usdc": snapshot["cash_usdc"],
            "open_exposure_usdc": snapshot["open_exposure_usdc"],
            "equity_usdc": snapshot["equity_usdc"],
            "realized_pnl_usdc": snapshot["realized_pnl_usdc"],
            "positions_open": len(snapshot["positions"]),
            "events_processed": len(snapshot["history"]),
        },
        "positions": snapshot["positions"],
        "history": snapshot["history"],
    }
    print(json.dumps(output, indent=2, ensure_ascii=False))

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(snapshot, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
