from __future__ import annotations

import argparse
from pathlib import Path

from copy_bot_dev import LiveConfig, run_live_server


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Copy bot live paper dashboard")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8875)
    parser.add_argument("--refresh-seconds", type=int, default=20)
    parser.add_argument("--activity-limit", type=int, default=200)
    parser.add_argument("--positions-limit", type=int, default=200)
    parser.add_argument(
        "--reports-dir",
        default=str(Path(__file__).resolve().parent / "reports"),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_live_server(
        LiveConfig(
            host=args.host,
            port=args.port,
            refresh_seconds=args.refresh_seconds,
            reports_dir=args.reports_dir,
            activity_limit=args.activity_limit,
            positions_limit=args.positions_limit,
        )
    )


if __name__ == "__main__":
    main()
