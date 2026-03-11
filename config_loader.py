from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ConfigError(Exception):
    pass


@dataclass
class AppConfig:
    azdo_org_url: str
    azdo_project: str
    azdo_pat: str
    capture_root: Path
    step_name_max_length: int


REQUIRED_KEYS = {
    "AZDO_ORG_URL",
    "AZDO_PROJECT",
    "AZDO_PAT",
    "CAPTURE_ROOT",
    "STEP_NAME_MAX_LENGTH",
}


def load_config(path: Path) -> AppConfig:
    if not path.exists():
        raise ConfigError(f"Missing config file: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in config file: {exc}") from exc

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise ConfigError(f"Missing config keys: {', '.join(sorted(missing))}")

    step_name_max_length = data["STEP_NAME_MAX_LENGTH"]
    if not isinstance(step_name_max_length, int) or step_name_max_length <= 0:
        raise ConfigError("STEP_NAME_MAX_LENGTH must be a positive integer")

    values = {
        "AZDO_ORG_URL": str(data["AZDO_ORG_URL"]).strip(),
        "AZDO_PROJECT": str(data["AZDO_PROJECT"]).strip(),
        "AZDO_PAT": str(data["AZDO_PAT"]).strip(),
        "CAPTURE_ROOT": str(data["CAPTURE_ROOT"]).strip(),
    }

    for key, value in values.items():
        if not value:
            raise ConfigError(f"{key} must not be empty")

    return AppConfig(
        azdo_org_url=values["AZDO_ORG_URL"],
        azdo_project=values["AZDO_PROJECT"],
        azdo_pat=values["AZDO_PAT"],
        capture_root=Path(values["CAPTURE_ROOT"]),
        step_name_max_length=step_name_max_length,
    )
