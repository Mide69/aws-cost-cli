from __future__ import annotations

import json
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()
err_console = Console(stderr=True)


def _fmt(amount: float, unit: str = "USD") -> str:
    symbol = "$" if unit == "USD" else f"{unit} "
    if amount == 0:
        return f"{symbol}0.00"
    if amount < 0.01:
        return f"{symbol}{amount:.6f}"
    return f"{symbol}{amount:,.2f}"


def print_summary(data: list[dict]) -> None:
    table = Table(title="Monthly Cost Summary", box=box.ROUNDED, show_header=True)
    table.add_column("Month", style="cyan", no_wrap=True)
    table.add_column("Total Cost", justify="right", style="green")
    table.add_column("", style="dim")

    for row in data:
        label = "[dim italic]estimated[/dim italic]" if row.get("estimated") else ""
        table.add_row(row["period"], _fmt(row["cost"], row["unit"]), label)

    console.print(table)


def print_services(data: list[dict], month: str) -> None:
    total = sum(r["cost"] for r in data)
    unit = data[0]["unit"] if data else "USD"

    table = Table(title=f"Cost by Service — {month}", box=box.ROUNDED)
    table.add_column("Service", style="cyan")
    table.add_column("Cost", justify="right", style="green")
    table.add_column("% of Total", justify="right", style="yellow")

    for row in data:
        pct = (row["cost"] / total * 100) if total > 0 else 0.0
        table.add_row(row["service"], _fmt(row["cost"], row["unit"]), f"{pct:.1f}%")

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{_fmt(total, unit)}[/bold]", "[bold]100.0%[/bold]")
    console.print(table)


def print_accounts(data: list[dict], month: str) -> None:
    total = sum(r["cost"] for r in data)
    unit = data[0]["unit"] if data else "USD"

    table = Table(title=f"Cost by Account — {month}", box=box.ROUNDED)
    table.add_column("Account ID", style="cyan", no_wrap=True)
    table.add_column("Cost", justify="right", style="green")
    table.add_column("% of Total", justify="right", style="yellow")

    for row in data:
        pct = (row["cost"] / total * 100) if total > 0 else 0.0
        table.add_row(row["account"], _fmt(row["cost"], row["unit"]), f"{pct:.1f}%")

    table.add_section()
    table.add_row("[bold]Total[/bold]", f"[bold]{_fmt(total, unit)}[/bold]", "[bold]100.0%[/bold]")
    console.print(table)


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
            row["service"],
            row["region"],
            row["account"],
            row["start_date"],
            row["end_date"],
            _fmt(row["actual_spend"]),
            _fmt(row["expected_spend"]),
            _fmt(row["impact"]),
        )

    console.print(table)


def print_json(data: object) -> None:
    console.print_json(json.dumps(data, default=str))
