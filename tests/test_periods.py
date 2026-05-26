from datetime import date, timedelta
import pytest
from aws_cost_cli import periods


def test_mtd_starts_first_of_month():
    s, e = periods.resolve("mtd")
    assert s.day == 1
    assert s.month == date.today().month
    assert e >= date.today()


def test_yesterday_is_one_day():
    s, e = periods.resolve("yesterday")
    assert (e - s).days == 1
    assert s == date.today() - timedelta(days=1)


def test_7d_span():
    s, e = periods.resolve("7d")
    assert (e - s).days == 7


def test_30d_span():
    s, e = periods.resolve("30d")
    assert (e - s).days == 30


def test_last_month_is_full_month():
    s, e = periods.resolve("last-month")
    assert s.day == 1
    assert e.day == 1
    assert s.month != e.month or s.year != e.year
    assert 28 <= (e - s).days <= 31


def test_ytd_starts_jan_1():
    s, e = periods.resolve("ytd")
    assert s == date(date.today().year, 1, 1)


def test_3m_starts_two_months_ago():
    s, e = periods.resolve("3m")
    assert s.day == 1
    assert s <= date.today().replace(day=1)


def test_yyyymm_parses_correctly():
    s, e = periods.resolve("2026-03")
    assert s == date(2026, 3, 1)
    assert e == date(2026, 4, 1)


def test_custom_start_end_overrides_period():
    s, e = periods.resolve("mtd", start="2026-01-10", end="2026-01-20")
    assert s == date(2026, 1, 10)
    assert e == date(2026, 1, 21)  # end is exclusive


def test_unknown_period_raises():
    with pytest.raises(ValueError, match="Unknown period"):
        periods.resolve("last-quarter")


def test_label_full_month():
    lbl = periods.label(date(2026, 3, 1), date(2026, 4, 1))
    assert lbl == "March 2026"


def test_label_single_day():
    lbl = periods.label(date(2026, 5, 10), date(2026, 5, 11))
    assert lbl == "2026-05-10"


def test_label_range():
    lbl = periods.label(date(2026, 5, 1), date(2026, 5, 8))
    assert "2026-05-01" in lbl and "2026-05-07" in lbl
