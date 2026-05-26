from __future__ import annotations

import boto3
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional


def get_client(profile: Optional[str] = None, region: str = "us-east-1"):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("ce", region_name=region)


def _first_of_month(d: date) -> date:
    return d.replace(day=1)


def _next_month(d: date) -> date:
    return _first_of_month(d) + relativedelta(months=1)


def get_monthly_summary(client, months: int = 6) -> list[dict]:
    """Total cost per month for the last N months (including current partial month)."""
    today = date.today()
    start = _first_of_month(today) - relativedelta(months=months - 1)
    end = _next_month(today)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )

    return [
        {
            "period": period["TimePeriod"]["Start"][:7],
            "cost": float(period["Total"]["UnblendedCost"]["Amount"]),
            "unit": period["Total"]["UnblendedCost"]["Unit"],
            "estimated": period.get("Estimated", False),
        }
        for period in response["ResultsByTime"]
    ]


def get_cost_by_service(client, month: Optional[str] = None) -> list[dict]:
    """Cost breakdown by AWS service for a given month (default: current month)."""
    today = date.today()
    if month:
        from datetime import datetime
        start = datetime.strptime(month, "%Y-%m").date()
    else:
        start = _first_of_month(today)

    end = _next_month(start)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
    )

    results = []
    for period in response["ResultsByTime"]:
        for group in period["Groups"]:
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0:
                results.append({
                    "service": group["Keys"][0],
                    "cost": cost,
                    "unit": group["Metrics"]["UnblendedCost"]["Unit"],
                })

    return sorted(results, key=lambda x: x["cost"], reverse=True)


def get_cost_by_account(client, month: Optional[str] = None) -> list[dict]:
    """Cost breakdown by linked AWS account for a given month (default: current month)."""
    today = date.today()
    if month:
        from datetime import datetime
        start = datetime.strptime(month, "%Y-%m").date()
    else:
        start = _first_of_month(today)

    end = _next_month(start)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": "LINKED_ACCOUNT"}],
    )

    results = []
    for period in response["ResultsByTime"]:
        for group in period["Groups"]:
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if cost > 0:
                results.append({
                    "account": group["Keys"][0],
                    "cost": cost,
                    "unit": group["Metrics"]["UnblendedCost"]["Unit"],
                })

    return sorted(results, key=lambda x: x["cost"], reverse=True)


def get_forecast(client, period: str = "MONTHLY") -> dict:
    """Cost forecast for the remainder of the current month or year."""
    today = date.today()

    if period == "MONTHLY":
        start = today
        end = _next_month(today)
    else:  # YEARLY
        start = today
        end = date(today.year + 1, 1, 1)

    if start >= end:
        return {"error": "No remaining days in the forecast period."}

    response = client.get_cost_forecast(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity=period,
        Metric="UNBLENDED_COST",
    )

    intervals = response.get("ForecastResultsByTime", [])
    lower = float(intervals[0]["PredictionIntervalLowerBound"]) if intervals else float(response["Total"]["Amount"])
    upper = float(intervals[0]["PredictionIntervalUpperBound"]) if intervals else float(response["Total"]["Amount"])

    return {
        "mean": float(response["Total"]["Amount"]),
        "unit": response["Total"]["Unit"],
        "lower": lower,
        "upper": upper,
        "period_start": start.isoformat(),
        "period_end": (end - timedelta(days=1)).isoformat(),
    }


def get_anomalies(client, days: int = 30, threshold: float = 10.0) -> list[dict]:
    """Cost anomalies detected in the last N days with impact above threshold ($)."""
    end = date.today()
    start = end - timedelta(days=days)

    response = client.get_anomalies(
        DateInterval={"StartDate": start.isoformat(), "EndDate": end.isoformat()},
        TotalImpact={"NumericOperator": "GREATER_THAN", "StartValue": threshold},
    )

    results = []
    for anomaly in response.get("Anomalies", []):
        impact = anomaly.get("Impact", {})
        root = anomaly.get("RootCauses", [{}])[0]
        results.append({
            "anomaly_id": anomaly["AnomalyId"],
            "service": root.get("Service", "Unknown"),
            "region": root.get("Region", "Unknown"),
            "account": root.get("LinkedAccount", "Unknown"),
            "start_date": anomaly["AnomalyStartDate"],
            "end_date": anomaly.get("AnomalyEndDate", "Ongoing"),
            "actual_spend": float(impact.get("TotalActualSpend", 0)),
            "expected_spend": float(impact.get("TotalExpectedSpend", 0)),
            "impact": float(impact.get("TotalImpact", 0)),
        })

    return sorted(results, key=lambda x: x["impact"], reverse=True)
