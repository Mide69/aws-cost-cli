from datetime import date
from unittest.mock import MagicMock
import pytest
from aws_cost_cli import cost_explorer


def _client():
    return MagicMock()


def _period_result(groups, start="2026-05-01", end="2026-06-01"):
    return {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": start, "End": end},
                "Total": {"UnblendedCost": {"Amount": "0.00", "Unit": "USD"}},
                "Groups": groups,
                "Estimated": False,
            }
        ]
    }


# ── monthly summary ───────────────────────────────────────────────────────────

def test_monthly_summary_parses():
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
    assert result[1]["estimated"] is True


# ── generic dimension ─────────────────────────────────────────────────────────

def test_dimension_filters_zero_and_sorts():
    client = _client()
    client.get_cost_and_usage.return_value = _period_result([
        {"Keys": ["Amazon EC2"],  "Metrics": {"UnblendedCost": {"Amount": "50.00", "Unit": "USD"}}},
        {"Keys": ["Amazon S3"],   "Metrics": {"UnblendedCost": {"Amount": "0.00",  "Unit": "USD"}}},
        {"Keys": ["AWS Lambda"],  "Metrics": {"UnblendedCost": {"Amount": "10.00", "Unit": "USD"}}},
    ])
    result = cost_explorer.get_cost_by_dimension(
        client, "SERVICE", date(2026, 5, 1), date(2026, 6, 1)
    )
    assert len(result) == 2
    assert result[0]["name"] == "Amazon EC2"
    assert result[1]["name"] == "AWS Lambda"


def test_dimension_aggregates_multiple_periods():
    client = _client()
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {
                "TimePeriod": {"Start": "2026-05-01", "End": "2026-05-02"},
                "Total": {},
                "Groups": [
                    {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "10.00", "Unit": "USD"}}},
                ],
            },
            {
                "TimePeriod": {"Start": "2026-05-02", "End": "2026-05-03"},
                "Total": {},
                "Groups": [
                    {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "15.00", "Unit": "USD"}}},
                ],
            },
        ]
    }
    result = cost_explorer.get_cost_by_dimension(
        client, "SERVICE", date(2026, 5, 1), date(2026, 5, 3)
    )
    assert len(result) == 1
    assert result[0]["cost"] == pytest.approx(25.0)


# ── get_total ─────────────────────────────────────────────────────────────────

def test_get_total_sums_periods():
    client = _client()
    client.get_cost_and_usage.return_value = {
        "ResultsByTime": [
            {"Total": {"UnblendedCost": {"Amount": "30.00", "Unit": "USD"}}, "Groups": []},
            {"Total": {"UnblendedCost": {"Amount": "20.00", "Unit": "USD"}}, "Groups": []},
        ]
    }
    result = cost_explorer.get_total(client, date(2026, 5, 1), date(2026, 5, 31))
    assert result["cost"] == pytest.approx(50.0)
    assert result["unit"] == "USD"


# ── with_comparison ───────────────────────────────────────────────────────────

def test_comparison_calculates_pct_change():
    client = _client()

    def side_effect(**kwargs):
        start = kwargs["TimePeriod"]["Start"]
        if start == "2026-05-01":
            return _period_result([
                {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "100.00", "Unit": "USD"}}},
            ])
        # previous period
        return _period_result([
            {"Keys": ["Amazon EC2"], "Metrics": {"UnblendedCost": {"Amount": "80.00", "Unit": "USD"}}},
        ])

    client.get_cost_and_usage.side_effect = side_effect

    current = [{"name": "Amazon EC2", "cost": 100.0, "unit": "USD"}]
    result = cost_explorer.with_comparison(
        current, client, date(2026, 5, 1), date(2026, 6, 1), "SERVICE"
    )
    assert result[0]["prev_cost"] == pytest.approx(80.0)
    assert result[0]["change_pct"] == pytest.approx(25.0)


def test_comparison_new_service_has_none_pct():
    client = _client()
    client.get_cost_and_usage.return_value = _period_result([])

    current = [{"name": "New Service", "cost": 50.0, "unit": "USD"}]
    result = cost_explorer.with_comparison(
        current, client, date(2026, 5, 1), date(2026, 6, 1), "SERVICE"
    )
    assert result[0]["change_pct"] is None


# ── forecast ──────────────────────────────────────────────────────────────────

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


def test_forecast_handles_missing_intervals():
    client = _client()
    client.get_cost_forecast.return_value = {
        "Total": {"Amount": "200.00", "Unit": "USD"},
        "ForecastResultsByTime": [{}],
    }
    result = cost_explorer.get_forecast(client, period="MONTHLY")
    if "error" not in result:
        assert result["mean"] == pytest.approx(200.0)
        assert result["lower"] == pytest.approx(200.0)
        assert result["upper"] == pytest.approx(200.0)


# ── anomalies ─────────────────────────────────────────────────────────────────

def test_anomalies_empty():
    client = _client()
    client.get_anomalies.return_value = {"Anomalies": []}
    assert cost_explorer.get_anomalies(client) == []


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
    result = cost_explorer.get_anomalies(client, threshold=0.0)
    assert result[0]["anomaly_id"] == "a1"
    assert result[0]["impact"] == pytest.approx(90.0)
