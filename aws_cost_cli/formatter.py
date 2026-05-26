from __future__ import annotations

import csv
import io
import json

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()
err_console = Console(stderr=True)


def _fmt(amount: float, unit: str = "USD") -> str:
    symbol = "$" if unit == "USD" else f"{unit} "
    if amount == 0:
        return f"{symbol}0.00"
    if amount < 0.01:
        return f"{symbol}{amount:.6f}"
    return f"{symbol}{amount:,.2f}"


def _change_text(pct: float | None) -> Text:
    if pct is None:
        return Text("new", style="cyan")
    if pct > 0:
        return Text(f"▲ +{pct:.1f}%", style="bold red")
    if pct < 0:
        return Text(f"▼ {pct:.1f}%", style="bold green")
    return Text("── 0.0%", style="dim")


# ── monthly summary ───────────────────────────────────────────────────────────

def print_summary(data: list[dict]) -> None:
    table = Table(title="Monthly Cost Summary", box=box.ROUNDED)
    table.add_column("Month", style="cyan", no_wrap=True)
    table.add_column("Total Cost", justify="right", style="green")
    table.add_column("", style="dim")

    for row in data:
        label = "[dim italic]estimated[/dim italic]" if row.get("estimated") else ""
        table.add_row(row["period"], _fmt(row["cost"], row["unit"]), label)

    console.print(table)


# ── daily spend ───────────────────────────────────────────────────────────────

def print_daily(data: list[dict]) -> None:
    total = sum(r["cost"] for r in data)
    unit = data[0]["unit"] if data else "USD"

    table = Table(title="Daily Spend", box=box.ROUNDED)
    table.add_column("Date", style="cyan", no_wrap=True)
    table.add_column("Cost", justify="right", style="green")
    table.add_column("", style="dim")

    for row in data:
        label = "[dim italic]est.[/dim italic]" if row.get("estimated") else ""
        table.add_row(row["date"], _fmt(row["cost"], row["unit"]), label)

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{_fmt(total, unit)}[/bold]", "")
    console.print(table)


# ── dimension table (services / accounts / regions / tags) ────────────────────

def print_dimension(
    data: list[dict],
    title: str,
    name_col: str,
    compare: bool = False,
) -> None:
    total = sum(r["cost"] for r in data)
    unit = data[0]["unit"] if data else "USD"

    table = Table(title=title, box=box.ROUNDED)
    table.add_column(name_col, style="cyan")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("% of Total", justify="right", style="yellow")
    if compare:
        table.add_column("vs Prev Period", justify="right")

    for row in data:
        pct = (row["cost"] / total * 100) if total > 0 else 0.0
        cells: list = [row["name"], _fmt(row["cost"], row["unit"]), f"{pct:.1f}%"]
        if compare:
            cells.append(_change_text(row.get("change_pct")))
        table.add_row(*cells)

    table.add_section()
    footer: list = [
        "[bold]Total[/bold]",
        f"[bold]{_fmt(total, unit)}[/bold]",
        "[bold]100.0%[/bold]",
    ]
    if compare:
        footer.append("")
    table.add_row(*footer)
    console.print(table)


# ── forecast ──────────────────────────────────────────────────────────────────

def print_forecast(data: dict) -> None:
    if "error" in data:
        err_console.print(f"[yellow]{data['error']}[/yellow]")
        return

    unit = data.get("unit", "USD")
    content = (
        f"[dim]Period:[/dim]   {data['period_start']} → {data['period_end']}\n"
        f"[green]Forecast:[/green]  {_fmt(data['mean'], unit)}\n"
        f"[dim]Range:[/dim]     {_fmt(data['lower'], unit)} – {_fmt(data['upper'], unit)}"
    )
    console.print(Panel(content, title="[bold]Cost Forecast[/bold]", expand=False))


# ── anomalies ─────────────────────────────────────────────────────────────────

def print_anomalies(data: list[dict]) -> None:
    if not data:
        console.print("[green]No cost anomalies detected.[/green]")
        return

    table = Table(title="Cost Anomalies", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Region", style="blue")
    table.add_column("Account", style="magenta", no_wrap=True)
    table.add_column("Start", style="white", no_wrap=True)
    table.add_column("End", style="white", no_wrap=True)
    table.add_column("Actual", justify="right", style="red")
    table.add_column("Expected", justify="right", style="yellow")
    table.add_column("Impact", justify="right", style="bold red")

    for row in data:
        table.add_row(
            row["service"], row["region"], row["account"],
            row["start_date"], row["end_date"],
            _fmt(row["actual_spend"]), _fmt(row["expected_spend"]), _fmt(row["impact"]),
        )

    console.print(table)


# ── budget ────────────────────────────────────────────────────────────────────

def print_budget_list(budgets: dict) -> None:
    if not budgets:
        console.print("[yellow]No budgets configured. Run: aws-cost budget set NAME AMOUNT[/yellow]")
        return

    table = Table(title="Configured Budgets", box=box.ROUNDED)
    table.add_column("Name", style="cyan")
    table.add_column("Monthly Budget", justify="right", style="green")

    for name, cfg in budgets.items():
        table.add_row(name, _fmt(cfg["amount"]))

    console.print(table)


def print_budget_status(budgets: dict, actuals: dict) -> None:
    if not budgets:
        console.print("[yellow]No budgets configured. Run: aws-cost budget set NAME AMOUNT[/yellow]")
        return

    console.print()
    for name, cfg in budgets.items():
        limit = cfg["amount"]
        spent = actuals.get(name, 0.0)
        pct = min(spent / limit, 1.0) if limit > 0 else 0.0
        remaining = max(limit - spent, 0.0)
        over = spent > limit

        color = "green" if pct < 0.75 else ("yellow" if pct < 0.90 else "red")
        filled = int(pct * 30)
        bar = f"[{color}]{'█' * filled}[/{color}]{'░' * (30 - filled)}"
        status = "[bold red] OVER BUDGET[/bold red]" if over else ""

        console.print(
            f"[bold]{name}[/bold]{status}\n"
            f"  {bar}  {pct * 100:.1f}%\n"
            f"  Spent: [bold]{_fmt(spent)}[/bold]"
            f"  /  Budget: {_fmt(limit)}"
            f"  /  Remaining: [{color}]{_fmt(remaining)}[/{color}]\n"
        )


# ── CSV export ────────────────────────────────────────────────────────────────

def to_csv(data: list[dict]) -> str:
    if not data:
        return ""
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(data[0].keys()))
    writer.writeheader()
    writer.writerows(data)
    return buf.getvalue()


# ── JSON ──────────────────────────────────────────────────────────────────────

def print_json(data: object) -> None:
    console.print_json(json.dumps(data, default=str))
