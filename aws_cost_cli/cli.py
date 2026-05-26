from __future__ import annotations

import sys
import time
from datetime import date

import click
from rich import box
from rich.console import Console
from rich.table import Table

from . import budget as _budget
from . import cost_explorer, formatter
from . import notify as _notify
from . import periods

err = Console(stderr=True)

# ── reusable option decorators ────────────────────────────────────────────────

_period_opt = click.option(
    "--period", default="mtd", show_default=True,
    help=f"Time period: {periods.PERIOD_HELP}",
)
_start_opt = click.option("--start", default=None, metavar="YYYY-MM-DD", help="Custom start (overrides --period).")
_end_opt   = click.option("--end",   default=None, metavar="YYYY-MM-DD", help="Custom end   (overrides --period).")
_top_opt   = click.option("--top",   default=None, type=int, metavar="N", help="Show only the top N results.")
_cmp_opt   = click.option("--compare", is_flag=True, help="Compare with the previous equivalent period.")


def _resolve(period, start, end):
    try:
        return periods.resolve(period, start, end)
    except ValueError as exc:
        err.print(f"[red]{exc}[/red]")
        sys.exit(1)


def _emit(ctx, data, table_fn, *args, **kwargs):
    """Route output to table, JSON, or CSV based on --format."""
    fmt = ctx.obj["format"]
    if fmt == "json":
        formatter.print_json(data)
    elif fmt == "csv":
        click.echo(formatter.to_csv(data), nl=False)
    else:
        table_fn(data, *args, **kwargs)


# ── main group ────────────────────────────────────────────────────────────────

@click.group()
@click.version_option(package_name="aws-cost-cli")
@click.option("--profile", default=None, help="AWS named profile.")
@click.option("--region", default="us-east-1", show_default=True, help="AWS region.")
@click.option(
    "--format", "output_format",
    default="table",
    type=click.Choice(["table", "json", "csv"]),
    show_default=True,
    help="Output format.",
)
@click.pass_context
def main(ctx, profile, region, output_format):
    """AWS Cost CLI — analyze and monitor your AWS spending.

    \b
    Quick start:
      aws-cost summary
      aws-cost services --period last-month --compare
      aws-cost forecast
      aws-cost anomalies
    """
    ctx.ensure_object(dict)
    try:
        ctx.obj["client"] = cost_explorer.get_client(profile=profile, region=region)
    except Exception as exc:
        err.print(f"[red]Failed to initialize AWS client: {exc}[/red]")
        sys.exit(1)
    ctx.obj["format"] = output_format


# ── summary ───────────────────────────────────────────────────────────────────

@main.command()
@click.option("--months", default=6, show_default=True, help="Number of months to show.")
@click.pass_context
def summary(ctx, months):
    """Monthly cost totals for the last N months."""
    try:
        data = cost_explorer.get_monthly_summary(ctx.obj["client"], months=months)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    _emit(ctx, data, formatter.print_summary)


# ── daily ─────────────────────────────────────────────────────────────────────

@main.command()
@_period_opt
@_start_opt
@_end_opt
@click.pass_context
def daily(ctx, period, start, end):
    """Day-by-day cost breakdown for a period."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_daily_spend(ctx.obj["client"], s, e)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    _emit(ctx, data, formatter.print_daily)


# ── services ──────────────────────────────────────────────────────────────────

@main.command()
@_period_opt
@_start_opt
@_end_opt
@_top_opt
@_cmp_opt
@click.pass_context
def services(ctx, period, start, end, top, compare):
    """Cost breakdown by AWS service."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], "SERVICE", s, e)
        if compare:
            data = cost_explorer.with_comparison(data, ctx.obj["client"], s, e, "SERVICE")
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    _emit(ctx, data, formatter.print_dimension,
          f"Cost by Service — {periods.label(s, e)}", "Service", compare)


# ── accounts ──────────────────────────────────────────────────────────────────

@main.command()
@_period_opt
@_start_opt
@_end_opt
@_top_opt
@_cmp_opt
@click.pass_context
def accounts(ctx, period, start, end, top, compare):
    """Cost breakdown by linked AWS account (requires AWS Organizations)."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], "LINKED_ACCOUNT", s, e)
        if compare:
            data = cost_explorer.with_comparison(data, ctx.obj["client"], s, e, "LINKED_ACCOUNT")
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    _emit(ctx, data, formatter.print_dimension,
          f"Cost by Account — {periods.label(s, e)}", "Account ID", compare)


# ── regions ───────────────────────────────────────────────────────────────────

@main.command()
@_period_opt
@_start_opt
@_end_opt
@_top_opt
@_cmp_opt
@click.pass_context
def regions(ctx, period, start, end, top, compare):
    """Cost breakdown by AWS region."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], "REGION", s, e)
        if compare:
            data = cost_explorer.with_comparison(data, ctx.obj["client"], s, e, "REGION")
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    _emit(ctx, data, formatter.print_dimension,
          f"Cost by Region — {periods.label(s, e)}", "Region", compare)


# ── tags ──────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--tag-key", required=True, help="Tag key to group by, e.g. Environment or Team.")
@_period_opt
@_start_opt
@_end_opt
@_top_opt
@click.pass_context
def tags(ctx, tag_key, period, start, end, top):
    """Cost breakdown by a resource tag key."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_cost_by_tag(ctx.obj["client"], tag_key, s, e)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    _emit(ctx, data, formatter.print_dimension,
          f"Cost by Tag '{tag_key}' — {periods.label(s, e)}", tag_key, False)


# ── compare ───────────────────────────────────────────────────────────────────

@main.command()
@_period_opt
@_start_opt
@_end_opt
@_top_opt
@click.option(
    "--by", "dimension",
    default="SERVICE",
    type=click.Choice(["SERVICE", "REGION", "LINKED_ACCOUNT"]),
    show_default=True,
    help="Dimension to compare.",
)
@click.pass_context
def compare(ctx, period, start, end, top, dimension):
    """Compare spend against the previous equivalent period."""
    s, e = _resolve(period, start, end)
    try:
        data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], dimension, s, e)
        data = cost_explorer.with_comparison(data, ctx.obj["client"], s, e, dimension)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    dim_label = {"SERVICE": "Service", "REGION": "Region", "LINKED_ACCOUNT": "Account"}[dimension]
    _emit(ctx, data, formatter.print_dimension,
          f"Comparison — {periods.label(s, e)} vs previous", dim_label, True)


# ── forecast ──────────────────────────────────────────────────────────────────

@main.command()
@click.option(
    "--period", "forecast_period",
    default="MONTHLY",
    type=click.Choice(["MONTHLY", "YEARLY"]),
    show_default=True,
    help="Forecast the rest of this month or this year.",
)
@click.pass_context
def forecast(ctx, forecast_period):
    """Cost forecast for the rest of the current month or year."""
    try:
        data = cost_explorer.get_forecast(ctx.obj["client"], period=forecast_period)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)

    if ctx.obj["format"] == "json":
        formatter.print_json(data)
    else:
        formatter.print_forecast(data)


# ── anomalies ─────────────────────────────────────────────────────────────────

@main.command()
@click.option("--days", default=30, show_default=True, help="Look-back window in days.")
@click.option("--threshold", default=10.0, show_default=True, help="Minimum cost impact ($) to include.")
@click.pass_context
def anomalies(ctx, days, threshold):
    """Detect cost anomalies using AWS Cost Anomaly Detection."""
    try:
        data = cost_explorer.get_anomalies(ctx.obj["client"], days=days, threshold=threshold)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    _emit(ctx, data, formatter.print_anomalies)


# ── budget group ──────────────────────────────────────────────────────────────

@main.group(name="budget")
def budget_group():
    """Set and track monthly spend budgets."""


@budget_group.command("set")
@click.argument("name")
@click.argument("amount", type=float)
def budget_set(name, amount):
    """Set a monthly budget. NAME is 'total' or an AWS service name."""
    _budget.set_budget(name, amount)
    err.print(f"[green]Budget saved:[/green] [bold]{name}[/bold] = ${amount:,.2f} / month")


@budget_group.command("list")
def budget_list():
    """List all configured budgets."""
    formatter.print_budget_list(_budget.list_budgets())


@budget_group.command("delete")
@click.argument("name")
def budget_delete(name):
    """Remove a budget by name."""
    if _budget.delete_budget(name):
        err.print(f"[green]Deleted budget:[/green] {name}")
    else:
        err.print(f"[yellow]No budget named '{name}' found.[/yellow]")


@budget_group.command("status")
@click.pass_context
def budget_status(ctx):
    """Show MTD spend vs your configured budgets with progress bars."""
    budgets = _budget.list_budgets()
    if not budgets:
        err.print("[yellow]No budgets configured. Run: aws-cost budget set NAME AMOUNT[/yellow]")
        return
    try:
        today = date.today()
        s, e = today.replace(day=1), today
        service_data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], "SERVICE", s, e)
        total_data   = cost_explorer.get_total(ctx.obj["client"], s, e)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)

    actuals = {row["name"]: row["cost"] for row in service_data}
    actuals["total"] = total_data["cost"]
    formatter.print_budget_status(budgets, actuals)


# ── notify group ──────────────────────────────────────────────────────────────

@main.group(name="notify")
def notify_group():
    """Send cost reports to external services."""


@notify_group.command("slack")
@click.option(
    "--webhook",
    envvar="AWS_COST_SLACK_WEBHOOK",
    required=True,
    help="Slack Incoming Webhook URL. Or set AWS_COST_SLACK_WEBHOOK env var.",
)
@_period_opt
@_top_opt
@click.pass_context
def notify_slack(ctx, webhook, period, top):
    """Send a cost-by-service summary to a Slack channel."""
    s, e = _resolve(period, None, None)
    try:
        data = cost_explorer.get_cost_by_dimension(ctx.obj["client"], "SERVICE", s, e)
    except Exception as exc:
        err.print(f"[red]{exc}[/red]"); sys.exit(1)
    if top:
        data = data[:top]
    blocks = _notify.build_cost_blocks("AWS Cost Report", data, periods.label(s, e))
    try:
        _notify.slack(webhook, blocks)
        err.print("[green]Slack message sent.[/green]")
    except Exception as exc:
        err.print(f"[red]Failed to send Slack message: {exc}[/red]"); sys.exit(1)


# ── watch ─────────────────────────────────────────────────────────────────────

@main.command()
@click.option("--interval", default=60, show_default=True, help="Refresh interval in seconds.")
@_period_opt
@_top_opt
@click.pass_context
def watch(ctx, interval, period, top):
    """Live-refresh cost by service. Press Ctrl+C to exit."""
    from rich.live import Live

    client = ctx.obj["client"]

    def _build():
        s, e = _resolve(period, None, None)
        data = cost_explorer.get_cost_by_dimension(client, "SERVICE", s, e)
        if top:
            data = data[:top]
        total = sum(r["cost"] for r in data)
        unit  = data[0]["unit"] if data else "USD"
        t = Table(
            title=f"Live Cost — {periods.label(s, e)}  [dim](every {interval}s, Ctrl+C to stop)[/dim]",
            box=box.ROUNDED,
        )
        t.add_column("Service", style="cyan")
        t.add_column("Cost", justify="right", style="green")
        t.add_column("% of Total", justify="right", style="yellow")
        for row in data:
            pct = (row["cost"] / total * 100) if total > 0 else 0.0
            t.add_row(row["name"], formatter._fmt(row["cost"], row["unit"]), f"{pct:.1f}%")
        t.add_section()
        t.add_row("[bold]Total[/bold]", f"[bold]{formatter._fmt(total, unit)}[/bold]", "[bold]100.0%[/bold]")
        return t

    err.print(f"[dim]Fetching... press Ctrl+C to stop.[/dim]")
    try:
        with Live(_build(), refresh_per_second=1, screen=False) as live:
            while True:
                time.sleep(interval)
                live.update(_build())
    except KeyboardInterrupt:
        pass
