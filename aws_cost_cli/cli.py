from __future__ import annotations

import sys
from datetime import date

import click
from rich.console import Console

from . import cost_explorer, formatter

err = Console(stderr=True)


@click.group()
@click.version_option(package_name="aws-cost-cli")
@click.option("--profile", default=None, help="AWS named profile to use.")
@click.option("--region", default="us-east-1", show_default=True, help="AWS region for the Cost Explorer endpoint.")
@click.option(
    "--format", "output_format",
    default="table",
    type=click.Choice(["table", "json"]),
    show_default=True,
    help="Output format.",
)
@click.pass_context
def main(ctx: click.Context, profile: str, region: str, output_format: str) -> None:
    """AWS Cost CLI — analyze and monitor your AWS spending."""
    ctx.ensure_object(dict)
    try:
        ctx.obj["client"] = cost_explorer.get_client(profile=profile, region=region)
    except Exception as exc:
        err.print(f"[red]Failed to initialize AWS client: {exc}[/red]")
        sys.exit(1)
    ctx.obj["format"] = output_format


@main.command()
@click.option("--months", default=6, show_default=True, help="Number of months to display (includes current month).")
@click.pass_context
def summary(ctx: click.Context, months: int) -> None:
    """Show total monthly cost for the last N months."""
    try:
        data = cost_explorer.get_monthly_summary(ctx.obj["client"], months=months)
    except Exception as exc:
        err.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_summary(data)


@main.command()
@click.option(
    "--month", default=None, metavar="YYYY-MM",
    help="Month to analyze. Defaults to the current month.",
)
@click.pass_context
def services(ctx: click.Context, month: str) -> None:
    """Show cost breakdown by AWS service."""
    display_month = month or date.today().strftime("%Y-%m")
    try:
        data = cost_explorer.get_cost_by_service(ctx.obj["client"], month=month)
    except Exception as exc:
        err.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_services(data, display_month)


@main.command()
@click.option(
    "--month", default=None, metavar="YYYY-MM",
    help="Month to analyze. Defaults to the current month.",
)
@click.pass_context
def accounts(ctx: click.Context, month: str) -> None:
    """Show cost breakdown by linked AWS account (requires AWS Organizations)."""
    display_month = month or date.today().strftime("%Y-%m")
    try:
        data = cost_explorer.get_cost_by_account(ctx.obj["client"], month=month)
    except Exception as exc:
        err.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_accounts(data, display_month)


@main.command()
@click.option(
    "--period",
    default="MONTHLY",
    type=click.Choice(["MONTHLY", "YEARLY"]),
    show_default=True,
    help="Forecast period: remaining days of this month or this year.",
)
@click.pass_context
def forecast(ctx: click.Context, period: str) -> None:
    """Show cost forecast for the rest of the current month or year."""
    try:
        data = cost_explorer.get_forecast(ctx.obj["client"], period=period)
    except Exception as exc:
        err.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_forecast(data)


@main.command()
@click.option("--days", default=30, show_default=True, help="Look-back window in days.")
@click.option(
    "--threshold", default=10.0, show_default=True,
    help="Minimum cost impact in USD to include in results.",
)
@click.pass_context
def anomalies(ctx: click.Context, days: int, threshold: float) -> None:
    """Detect cost anomalies using AWS Cost Anomaly Detection."""
    try:
        data = cost_explorer.get_anomalies(ctx.obj["client"], days=days, threshold=threshold)
    except Exception as exc:
        err.print(f"[red]Error: {exc}[/red]")
        sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_anomalies(data)
