"""Rich-based CLI output formatters."""

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

console = Console()

CYAN = "bright_cyan"
GREEN = "bright_green"
RED = "bright_red"
AMBER = "yellow"
DIM = "dim"


def print_header(title: str, subtitle: str = ""):
    text = Text()
    text.append("CORALCON", style=f"bold {CYAN}")
    text.append(f" - {title}", style="bold white")
    if subtitle:
        text.append(f"\n{subtitle}", style=DIM)
    console.print(Panel(text, border_style=CYAN, padding=(0, 2)))


def print_stat_row(stats: dict):
    items = []
    for label, (value, color) in stats.items():
        text = Text()
        text.append(f"{value}", style=f"bold {color}")
        text.append(f" {label}", style=DIM)
        items.append(Panel(text, border_style="dim white", padding=(0, 1)))
    console.print(Columns(items))


def print_rejection_table(patterns: list[dict]):
    table = Table(
        title="[bold]REJECTION BY ROLE[/bold]",
        box=box.SIMPLE_HEAD,
        border_style=DIM,
        header_style=f"bold {CYAN}",
        show_lines=False,
    )
    table.add_column("ROLE", style="white", min_width=22)
    table.add_column("APPLIED", justify="right", style="white")
    table.add_column("REJECTED", justify="right")
    table.add_column("GHOSTED", justify="right")
    table.add_column("RATE", justify="right", min_width=8)
    table.add_column("SIGNAL", min_width=18)

    for pattern in patterns:
        rate = pattern.get("rejection_rate", 0)
        color = RED if rate >= 70 else (AMBER if rate >= 40 else GREEN)
        bar_len = int(rate / 10)
        bar = "#" * bar_len + "." * (10 - bar_len)
        table.add_row(
            pattern.get("role_title", ""),
            str(pattern.get("total", 0)),
            str(pattern.get("rejected", 0)),
            str(pattern.get("ghosted", 0)),
            f"[{color}]{rate:.0f}%[/{color}]",
            f"[{color}]{bar}[/{color}]",
        )
    console.print(table)


def print_skill_gaps(gaps: list[dict]):
    table = Table(
        title="[bold]SKILL GAP ANALYSIS[/bold]",
        box=box.SIMPLE_HEAD,
        border_style=DIM,
        header_style=f"bold {CYAN}",
        show_lines=False,
    )
    table.add_column("SKILL", style="white", min_width=20)
    table.add_column("REQUIRED IN", justify="right")
    table.add_column("IN GITHUB", justify="center")
    table.add_column("IN LINKEDIN", justify="center")
    table.add_column("IN PORTFOLIO", justify="center")
    table.add_column("PRIORITY", justify="center")

    priority_colors = {"critical": RED, "high": AMBER, "medium": "white"}

    for gap in gaps:
        priority = gap.get("priority", "medium")
        color = priority_colors.get(priority, "white")
        table.add_row(
            gap.get("skill", ""),
            f"{gap.get('times_required', 0)} rejections",
            "[green]yes[/green]" if gap.get("in_github") else "[red]no[/red]",
            "[green]yes[/green]" if gap.get("in_linkedin") else "[red]no[/red]",
            "[green]yes[/green]" if gap.get("in_portfolio") else "[red]no[/red]",
            f"[{color}]{priority.upper()}[/{color}]",
        )
    console.print(table)


def print_portfolio_signal(portfolio: dict):
    console.print()
    console.print(f"  [bold {CYAN}]PORTFOLIO SIGNAL[/bold {CYAN}]")
    console.print(f"  [dim]{'-' * 50}[/dim]")
    if not portfolio.get("configured"):
        console.print("  [dim]No portfolio URL configured. Pass --portfolio-url or set PORTFOLIO_URL.[/dim]\n")
        return
    marker = f"[{GREEN}]reachable[/{GREEN}]" if portfolio.get("reachable") else f"[{RED}]not reachable[/{RED}]"
    console.print(f"  URL:    [white]{portfolio.get('url') or 'N/A'}[/white]")
    console.print(f"  Status: {marker} ({portfolio.get('status_code') or 'no status'})")
    if portfolio.get("title"):
        console.print(f"  Title:  [white]{portfolio.get('title')}[/white]")
    skills = portfolio.get("detected_skills", [])
    console.print(f"  Skills detected: [{CYAN}]{len(skills)}[/{CYAN}] {', '.join(skills[:10]) if skills else ''}")
    console.print(f"  Project links:   [white]{len(portfolio.get('project_links', []))}[/white]")
    console.print(f"  GitHub links:    [white]{len(portfolio.get('github_links', []))}[/white]")
    if portfolio.get("error"):
        console.print(f"  [dim]{portfolio.get('error')}[/dim]")
    console.print()


def print_followup_table(followups: list[dict]):
    table = Table(
        title="[bold]FOLLOW-UP QUEUE[/bold]",
        box=box.SIMPLE_HEAD,
        border_style=DIM,
        header_style=f"bold {CYAN}",
        show_lines=False,
    )
    table.add_column("COMPANY", style="white", min_width=20)
    table.add_column("ROLE", style=DIM, min_width=22)
    table.add_column("APPLIED", style=DIM)
    table.add_column("WAITING", justify="right")
    table.add_column("ACTION")

    priority_colors = {"hot": RED, "warm": AMBER, "cold": DIM}

    for followup in followups:
        days = followup.get("days_waiting", 0)
        priority = followup.get("priority", "cold")
        color = priority_colors.get(priority, DIM)
        table.add_row(
            followup.get("company", ""),
            followup.get("role_title", ""),
            followup.get("applied_date", ""),
            f"[{color}]{days}d[/{color}]",
            followup.get("recommended_action", ""),
        )
    console.print(table)


def print_action_items(items: list[str]):
    console.print()
    console.print(f"  [bold {CYAN}]ACTION ITEMS[/bold {CYAN}]")
    console.print(f"  [dim]{'-' * 50}[/dim]")
    for index, item in enumerate(items, 1):
        console.print(f"  [{AMBER}]{index}.[/{AMBER}] {item}")
    console.print()


def print_github_signal(signal: dict):
    console.print()
    console.print(f"  [bold {CYAN}]GITHUB SIGNAL[/bold {CYAN}]")
    console.print(f"  [dim]{'-' * 50}[/dim]")
    active_ghost = signal.get("ghost_rate_active_weeks", 0)
    inactive_ghost = signal.get("ghost_rate_inactive_weeks", 0)
    console.print(f"  Active weeks ghost rate:   [{GREEN}]{active_ghost:.0f}%[/{GREEN}]")
    console.print(f"  Inactive weeks ghost rate: [{RED}]{inactive_ghost:.0f}%[/{RED}]")
    console.print(f"  Top language: [{CYAN}]{signal.get('top_language', 'N/A')}[/{CYAN}]")
    console.print(f"  Total repos:  [white]{signal.get('total_repos', 0)}[/white]")
    console.print()


def print_llm_insights(text: str):
    console.print(
        Panel(
            text,
            title=f"[bold {CYAN}]AI ANALYSIS[/bold {CYAN}]",
            border_style=CYAN,
            padding=(1, 2),
        )
    )


def spinner(message: str):
    return Progress(
        SpinnerColumn(spinner_name="dots", style=CYAN),
        TextColumn(f"[dim]{message}[/dim]"),
        transient=True,
    )
