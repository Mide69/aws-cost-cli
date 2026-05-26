from __future__ import annotations

import boto3
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional


def get_client(profile: Optional[str] = None, region: str = "us-east-1"):
    session = boto3.Session(profile_name=profile) if profile else boto3.Session()
    return session.client("ce", region_name=region)


def _granularity(start: date, end: date) -> str:
    return "DAILY" if (end - start).days <= 31 else "MONTHLY"


# ── generic dimension breakdown ───────────────────────────────────────────────

def get_cost_by_dimension(
    client,
    dimension: str,
    start: date,
    end: date,
    ce_filter: Optional[dict] = None,
) -> list[dict]:
    """Cost totals grouped by any Cost Explorer dimension (SERVICE, REGION, LINKED_ACCOUNT…)."""
    kwargs: dict = dict(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity=_granularity(start, end),
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "DIMENSION", "Key": dimension}],
    )
    if ce_filter:
        kwargs["Filter"] = ce_filter

    response = client.get_cost_and_usage(**kwargs)

    totals: dict[str, float] = {}
    unit = "USD"
    for period in response["ResultsByTime"]:
        for group in period["Groups"]:
            key = group["Keys"][0]
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            unit = group["Metrics"]["UnblendedCost"]["Unit"]
            totals[key] = totals.get(key, 0.0) + cost

    return sorted(
        [{"name": k, "cost": v, "unit": unit} for k, v in totals.items() if v > 0],
        key=lambda x: x["cost"],
        reverse=True,
    )


def get_cost_by_tag(client, tag_key: str, start: date, end: date) -> list[dict]:
    """Cost totals grouped by a resource tag key."""
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity=_granularity(start, end),
        Metrics=["UnblendedCost"],
        GroupBy=[{"Type": "TAG", "Key": tag_key}],
    )

    totals: dict[str, float] = {}
    unit = "USD"
    for period in response["ResultsByTime"]:
        for group in period["Groups"]:
            key = group["Keys"][0] or f"(untagged)"
            cost = float(group["Metrics"]["UnblendedCost"]["Amount"])
            unit = group["Metrics"]["UnblendedCost"]["Unit"]
            totals[key] = totals.get(key, 0.0) + cost

    return sorted(
        [{"name": k, "cost": v, "unit": unit} for k, v in totals.items() if v > 0],
        key=lambda x: x["cost"],
        reverse=True,
    )


def get_total(client, start: date, end: date) -> dict:
    """Single total cost for a period with no grouping."""
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity=_granularity(start, end),
        Metrics=["UnblendedCost"],
    )
    total = sum(
        float(p["Total"]["UnblendedCost"]["Amount"])
        for p in response["ResultsByTime"]
    )
    unit = (
        response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Unit"]
        if response["ResultsByTime"]
        else "USD"
    )
    return {"cost": total, "unit": unit}


def with_comparison(
    current: list[dict],
    client,
    start: date,
    end: date,
    dimension: str,
) -> list[dict]:
    """Attach prev-period cost and % change to each row in current."""
    delta = end - start
    prev = get_cost_by_dimension(client, dimension, start - delta, start)
    prev_map = {r["name"]: r["cost"] for r in prev}

    for row in current:
        prev_cost = prev_map.get(row["name"], 0.0)
        row["prev_cost"] = prev_cost
        row["change_pct"] = (
            (row["cost"] - prev_cost) / prev_cost * 100
            if prev_cost > 0
            else None
        )
    return current


# ── monthly summary ───────────────────────────────────────────────────────────

def get_monthly_summary(client, months: int = 6) -> list[dict]:
    """Total cost per month for the last N months (includes current partial month)."""
    today = date.today()
    start = today.replace(day=1) - relativedelta(months=months - 1)
    end = today.replace(day=1) + relativedelta(months=1)

    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="MONTHLY",
        Metrics=["UnblendedCost"],
    )
    return [
        {
            "period": p["TimePeriod"]["Start"][:7],
            "cost": float(p["Total"]["UnblendedCost"]["Amount"]),
            "unit": p["Total"]["UnblendedCost"]["Unit"],
            "estimated": p.get("Estimated", False),
        }
        for p in response["ResultsByTime"]
    ]


# ── daily spend ───────────────────────────────────────────────────────────────

def get_daily_spend(client, start: date, end: date) -> list[dict]:
    """Day-by-day cost totals for a date range."""
    response = client.get_cost_and_usage(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
    )
    return [
        {
            "date": p["TimePeriod"]["Start"],
            "cost": float(p["Total"]["UnblendedCost"]["Amount"]),
            "unit": p["Total"]["UnblendedCost"]["Unit"],
            "estimated": p.get("Estimated", False),
        }
        for p in response["ResultsByTime"]
    ]


# ── forecast ──────────────────────────────────────────────────────────────────

def get_forecast(client, period: str = "MONTHLY") -> dict:
    """Cost forecast for the remainder of the current month or year."""
    today = date.today()
    if period == "MONTHLY":
        start = today
        end = today.replace(day=1) + relativedelta(months=1)
    else:
        start = today
        end = date(today.year + 1, 1, 1)

    if start >= end:
        return {"error": "No remaining days in the forecast period."}

    response = client.get_cost_forecast(
        TimePeriod={"Start": start.isoformat(), "End": end.isoformat()},
        Granularity=period,
        Metric="UNBLENDED_COST",
    )

    mean = float(response["Total"]["Amount"])
    intervals = response.get("ForecastResultsByTime", [])
    first = intervals[0] if intervals else {}
    lower = float(first.get("PredictionIntervalLowerBound", mean))
    upper = float(first.get("PredictionIntervalUpperBound", mean))

    return {
        "mean": mean,
        "unit": response["Total"]["Unit"],
        "lower": lower,
        "upper": upper,
        "period_start": start.isoformat(),
        "period_end": (end - timedelta(days=1)).isoformat(),
    }


# ── anomalies ─────────────────────────────────────────────────────────────────

def get_anomalies(client, days: int = 30, threshold: float = 10.0) -> list[dict]:
    """Cost anomalies detected in the last N days with impact above threshold."""
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
