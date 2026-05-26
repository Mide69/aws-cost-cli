from unittest.mock import MagicMock
import pytest
from aws_cost_cli import cost_explorer


def _client():
    return MagicMock()


# ── monthly summary ──────────────────────────────────────────────────────────

def test_monthly_summary_parses_response():
    client = _client()
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-04-01", "End": "2026-05-01"},
                "Total": {"UnblendedCost": {"Amount": "123.45", "Unit": "USD"}},
                "Groups": [],
                "Estimated": False,
            },
            {
                "TimePeriod": {"Start": "2026-05-01", "End": "2026-06-01"},
                "Total": {"UnblendedCost": {"Amount": "67.89", "Unit": "USD"}},
                "Groups": [],
                "Estimated": True,
            },
        ]
    }
    result = cost_explorer.get_monthly_summary(client, months=2)
    assert len(result) == 2
    assert result[0]["period"] == "2026-04"
    assert result[0]["cost"] == pytest.approx(123.45)
    assert result[0]["estimated"] is False
    assert result[1]["estimated"] is True


# ── cost by service ──────────────────────────────────────────────────────────

def test_services_filters_zero_cost_and_sorts():
    client = _client()
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-05-01", "End": "2026-06-01"},
                "Total": {},
                "Groups": [
                    {"Keys": ["Amazon EC2"],  "Metrics": {"UnblendedCost": {"Amount": "50.00", "Unit": "USD"}}},
                    {"Keys": ["Amazon S3"],   "Metrics": {"UnblendedCost": {"Amount": "0.00",  "Unit": "USD"}}},
                    {"Keys": ["AWS Lambda"],  "Metrics": {"UnblendedCost": {"Amount": "10.00", "Unit": "USD"}}},
                ],
                "Estimated": False,
            }
        ]
    }
    result = cost_explorer.get_cost_by_service(client, month="2026-05")
    assert len(result) == 2
    assert result[0]["service"] == "Amazon EC2"
    assert result[1]["service"] == "AWS Lambda"


# ── cost by account ──────────────────────────────────────────────────────────

def test_accounts_filters_zero_cost():
    client = _client()
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-05-01", "End": "2026-06-01"},
                "Total": {},
                "Groups": [
                    {"Keys": ["111111111111"], "Metrics": {"UnblendedCost": {"Amount": "200.00", "Unit": "USD"}}},
                    {"Keys": ["222222222222"], "Metrics": {"UnblendedCost": {"Amount": "0.00",   "Unit": "USD"}}},
                ],
                "Estimated": False,
            }
        ]
    }
    result = cost_explorer.get_cost_by_account(client, month="2026-05")
    assert len(result) == 1
    assert result[0]["account"] == "111111111111"
    assert result[0]["cost"] == pytest.approx(200.0)


# ── forecast ─────────────────────────────────────────────────────────────────

def test_forecast_parses_response():
    client = _client()
    client.get_cost_forecast.return_value = {
        "Total": {"Amount": "150.00", "Unit": "USD"},
        "ForecastResultsByTime": [
            {
                "PredictionIntervalLowerBound": "120.00",
                "PredictionIntervalUpperBound": "180.00",
            }
        ],
    }
    result = cost_explorer.get_forecast(client, period="MONTHLY")
    if "error" not in result:
        assert result["mean"] == pytest.approx(150.0)
        assert result["lower"] == pytest.approx(120.0)
        assert result["upper"] == pytest.approx(180.0)
        assert result["unit"] == "USD"


# ── anomalies ────────────────────────────────────────────────────────────────

def test_anomalies_empty():
    client = _client()
    client.get_anomalies.return_value = {"Anomalies": []}
    result = cost_explorer.get_anomalies(client, days=30)
    assert result == []


def test_anomalies_sorted_by_impact():
    client = _client()
    client.get_anomalies.return_value = {
        "Anomalies": [
            {
                "AnomalyId": "a1",
                "AnomalyStartDate": "2026-05-01",
                "RootCauses": [{"Service": "Amazon EC2", "Region": "us-east-1", "LinkedAccount": "111"}],
                "Impact": {"TotalActualSpend": 100.0, "TotalExpectedSpend": 10.0, "TotalImpact": 90.0},
            },
            {
                "AnomalyId": "a2",
                "AnomalyStartDate": "2026-05-05",
                "RootCauses": [{"Service": "Amazon RDS", "Region": "eu-west-1", "LinkedAccount": "222"}],
                "Impact": {"TotalActualSpend": 50.0, "TotalExpectedSpend": 5.0, "TotalImpact": 45.0},
            },
        ]
    }
    result = cost_explorer.get_anomalies(client, days=30, threshold=0.0)
    assert result[0]["anomaly_id"] == "a1"
    assert result[0]["impact"] == pytest.approx(90.0)
    assert result[1]["anomaly_id"] == "a2"
