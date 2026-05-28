from __future__ import annotations

import argparse
from pathlib import Path

from smart_home.server import run_server


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description="Run the Smart Home Security prototype.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument(
        "--db",
        default=str(project_root / "data" / "smart_home.sqlite"),
        help="SQLite database path.",
    )
    args = parser.parse_args()

    run_server(
        host=args.host,
        port=args.port,
        db_path=Path(args.db),
        static_dir=Path(__file__).resolve().parent / "web",
    )


if __name__ == "__main__":
    main()
