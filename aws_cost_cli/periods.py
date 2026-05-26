from __future__ import annotations

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Tuple

PERIOD_HELP = "yesterday | 7d | 30d | mtd | last-month | 3m | 6m | ytd | YYYY-MM"


def resolve(
    period: str = "mtd",
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Tuple[date, date]:
    """Return (start, end) as an exclusive-end date pair.

    Custom --start / --end always take precedence over the period label.
    """
    if start or end:
        from datetime import datetime
        s = datetime.strptime(start, "%Y-%m-%d").date() if start else date.today().replace(day=1)
        e = datetime.strptime(end, "%Y-%m-%d").date() if end else date.today()
        return s, e + timedelta(days=1)

    today = date.today()

    if period == "yesterday":
        d = today - timedelta(days=1)
        return d, today

    if period == "7d":
        return today - timedelta(days=7), today

    if period == "30d":
        return today - timedelta(days=30), today

    if period == "mtd":
        return today.replace(day=1), today + timedelta(days=1)

    if period == "last-month":
        first_this = today.replace(day=1)
        first_last = first_this - relativedelta(months=1)
        return first_last, first_this

    if period == "3m":
        start_d = today.replace(day=1) - relativedelta(months=2)
        return start_d, today + timedelta(days=1)

    if period == "6m":
        start_d = today.replace(day=1) - relativedelta(months=5)
        return start_d, today + timedelta(days=1)

    if period == "ytd":
        return date(today.year, 1, 1), today + timedelta(days=1)

    if len(period) == 7 and period[4] == "-":
        from datetime import datetime
        s = datetime.strptime(period, "%Y-%m").date()
        return s, s + relativedelta(months=1)

    raise ValueError(f"Unknown period '{period}'. Valid: {PERIOD_HELP}")


def label(start: date, end: date) -> str:
    """Human-readable description of a date range."""
    excl_end = end - timedelta(days=1)
    if start == excl_end:
        return start.isoformat()
    if start.day == 1 and end.day == 1 and 28 <= (end - start).days <= 31:
        return start.strftime("%B %Y")
    return f"{start.isoformat()} → {excl_end.isoformat()}"
