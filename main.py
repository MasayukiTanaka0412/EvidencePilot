from __future__ import annotations

import logging
from pathlib import Path

from cli import EvidencePilotCLI
from config_loader import ConfigError, load_config


def setup_logging() -> None:
    logging.basicConfig(
        filename="evidence_pilot.log",
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def main() -> int:
    setup_logging()
    print("Evidence Pilot")

    try:
        config = load_config(Path("config.json"))
    except ConfigError as exc:
        print(f"Configuration error: {exc}")
        return 1

    cli = EvidencePilotCLI(config)
    cli.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
