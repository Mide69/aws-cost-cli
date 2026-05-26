import pytest
from unittest.mock import patch
from pathlib import Path
import json
import tempfile
import os

from aws_cost_cli import budget as _budget


@pytest.fixture(autouse=True)
def tmp_budget_dir(tmp_path, monkeypatch):
    """Redirect budget storage to a temp directory for each test."""
    monkeypatch.setattr(_budget, "_CONFIG_DIR", tmp_path)
    monkeypatch.setattr(_budget, "_BUDGET_FILE", tmp_path / "budgets.json")


def test_empty_list():
    assert _budget.list_budgets() == {}


def test_set_and_list():
    _budget.set_budget("total", 500.0)
    _budget.set_budget("Amazon EC2", 200.0)
    result = _budget.list_budgets()
    assert result["total"]["amount"] == 500.0
    assert result["Amazon EC2"]["amount"] == 200.0


def test_overwrite_budget():
    _budget.set_budget("total", 100.0)
    _budget.set_budget("total", 999.0)
    assert _budget.list_budgets()["total"]["amount"] == 999.0


def test_delete_existing():
    _budget.set_budget("total", 500.0)
    assert _budget.delete_budget("total") is True
    assert "total" not in _budget.list_budgets()


def test_delete_nonexistent():
    assert _budget.delete_budget("nope") is False
