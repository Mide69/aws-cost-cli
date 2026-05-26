from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

_CONFIG_DIR = Path.home() / ".aws-cost-cli"
_BUDGET_FILE = _CONFIG_DIR / "budgets.json"


def _load() -> dict:
    if not _BUDGET_FILE.exists():
        return {}
    return json.loads(_BUDGET_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    _CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    _BUDGET_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")


def set_budget(name: str, amount: float) -> None:
    data = _load()
    data[name] = {"amount": amount}
    _save(data)


def delete_budget(name: str) -> bool:
    data = _load()
    if name not in data:
        return False
    del data[name]
    _save(data)
    return True


def list_budgets() -> dict:
    return _load()
