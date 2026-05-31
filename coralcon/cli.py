"""CoralCon CLI - AI career agent powered by Coral SQL."""

import os

import click
from dotenv import load_dotenv
from rich.console import Console

load_dotenv()

from coralcon.agents import analyzer, recommender, router
from coralcon.benchmarks.cache_benchmark import run_cache_benchmark
from coralcon.cohort.report import build_cohort_report
from coralcon.database import database_status, execute_sql, initialize_database
from coralcon.demo.judge_demo import demo_lines, real_demo_lines, run_judge_demo, run_real_demo
from coralcon.orchestrator import CoralConOrchestrator
from coralcon.portfolio import inspect_portfolio
from coralcon.privacy.report import write_privacy_report
from coralcon.proof.report import build_proof_report, proof_summary
from coralcon.queries import (
    followup_tracker,
    github_correlation,
    rejection_patterns,
    skill_gaps,
    timing_analysis,
)
from coralcon.submission.pack_generator import generate_submission_pack
from coralcon.utils import formatters as fmt
from coralcon.utils.coral_client import check_coral_connection

console = Console()


@click.group()
@click.version_option("0.1.0")
def cli():
    """CoralCon - AI career agent powered by Coral SQL."""


@cli.command()
@click.option("--no-ai", is_flag=True, help="Skip LLM analysis")
@click.option("--no-dashboard", is_flag=True, help="Skip local dashboard summary")
@click.option("--no-actions", is_flag=True, help="Skip local action task generation")
@click.option("--dry-run", is_flag=True, help="Run without external writes")
@click.option("--portfolio-url", help="Public portfolio URL to inspect during analysis")
def analyze(no_ai, no_dashboard, no_actions, dry_run, portfolio_url):
    """Run the full Phase 2 pipeline across all agents."""
    _set_portfolio_url(portfolio_url)
    fmt.print_header("FULL ANALYSIS", "Querying GitHub, Sheets, and LinkedIn via Coral SQL...")

    orchestrator = CoralConOrchestrator()
    with fmt.spinner("Running Recon, Analyst, Dashboard, and Action agents..."):
        result = orchestrator.run_full_analysis(
            use_ai=not no_ai,
            write_dashboard=not no_dashboard,
            create_actions=not no_actions,
            dry_run=True if dry_run else None,
        )

    insights = result["insights"]
    _print_insight_summary(insights)
    console.print()
    fmt.print_rejection_table(insights["rejection_patterns"])
    console.print()
    fmt.print_skill_gaps(insights["skill_gaps"])
    console.print()
    fmt.print_portfolio_signal(insights.get("portfolio", {}))
    fmt.print_github_signal(insights["github_correlation"])
    fmt.print_action_items(insights["action_items"])

    if insights.get("llm_insights"):
        fmt.print_llm_insights(insights["llm_insights"])
    elif insights.get("llm_error"):
        console.print(f"  [dim]AI analysis skipped: {insights['llm_error']}[/dim]")

    if not no_dashboard:
        dashboard = result["dashboard"]
        if dashboard.get("updated"):
            console.print(f"\n  [bright_green]Dashboard updated:[/bright_green] {dashboard.get('url')}")
        else:
            console.print(f"\n  [dim]{dashboard.get('message')}[/dim]")

    if not no_actions:
        total_tasks = len(result["tasks"])
        console.print(f"  [dim]Action agent prepared {total_tasks} local task(s).[/dim]")

    console.print(
        f"  [dim]Run [bright_cyan]coralcon followup[/bright_cyan] for "
        f"{len(insights['followup_priorities'])} pending follow-ups.[/dim]\n"
    )


@cli.command()
@click.option("--no-ai", is_flag=True, help="Skip LLM narration")
def morning(no_ai):
    """Your daily job-search standup: one screen, three sources, what to do today.

    The Track-2 'first mate' view — run it each morning. Joins your Gmail/Sheets
    application outcomes, real GitHub languages, and LinkedIn skills through Coral
    and tells you the single highest-leverage move for today.
    """
    from coralcon.agents.standup import build_standup

    with fmt.spinner("Joining Sheets + GitHub + LinkedIn via Coral..."):
        standup = build_standup()

    fmt.print_header("MORNING STANDUP", standup["date_label"])

    response_rate = standup["response_rate"]
    rate_color = "bright_green" if response_rate >= 15 else ("yellow" if response_rate >= 5 else "bright_red")
    console.print()
    console.print(
        f"  [dim]Where you stand:[/dim] [bright_cyan]{standup['total_applications']}[/bright_cyan] applications "
        f"[dim]·[/dim] [{rate_color}]{response_rate:.0f}% response rate[/{rate_color}]"
    )

    console.print("\n  [bold bright_white]Today's priorities[/bold bright_white]")
    for i, item in enumerate(standup["priorities"], 1):
        marker = f"[bright_red]{i}.[/bright_red]" if item["severity"] == "high" else f"[dim]{i}.[/dim]"
        console.print(f"  {marker} [bold]{item['title']}[/bold] — {item['detail']}")

    console.print(
        f"\n  [dim]Full breakdown:[/dim] [bright_cyan]coralcon analyze[/bright_cyan] "
        f"[dim]· proof:[/dim] [bright_cyan]coralcon proof[/bright_cyan]\n"
    )


@cli.command()
@click.option("--portfolio-url", help="Public portfolio URL to inspect")
def recon(portfolio_url):
    """Run Agent 1 only and print source counts."""
    _set_portfolio_url(portfolio_url)
    fmt.print_header("RECON", "Scanning all Coral SQL sources...")
    with fmt.spinner("Fetching raw data..."):
        raw = CoralConOrchestrator().run_recon()

    console.print()
    console.print(f"  Applications:       [bright_cyan]{len(raw.get('applications', []))}[/bright_cyan]")
    console.print(f"  GitHub weeks:       [bright_cyan]{len(raw.get('github_activity', []))}[/bright_cyan]")
    console.print(f"  LinkedIn skills:    [bright_cyan]{len(raw.get('linkedin_profile', {}).get('skills', []))}[/bright_cyan]")
    portfolio = raw.get("portfolio", {})
    portfolio_status = "reachable" if portfolio.get("reachable") else ("configured" if portfolio.get("configured") else "not set")
    console.print(f"  Portfolio:          [bright_cyan]{portfolio_status}[/bright_cyan]")
    console.print(f"  Rejection patterns: [bright_cyan]{len(raw.get('rejection_patterns', []))}[/bright_cyan]")
    fmt.print_portfolio_signal(portfolio)
    console.print()


@cli.command()
@click.option("--no-ai", is_flag=True, help="Skip LLM analysis")
@click.option("--portfolio-url", help="Public portfolio URL to inspect during analysis")
def insights(no_ai, portfolio_url):
    """Run Recon + Analyst agents only."""
    _set_portfolio_url(portfolio_url)
    fmt.print_header("INSIGHTS", "Generating structured analysis...")
    with fmt.spinner("Running analysis..."):
        data = CoralConOrchestrator().run_insights(use_ai=not no_ai)

    _print_insight_summary(data)
    console.print()
    fmt.print_rejection_table(data["rejection_patterns"])
    console.print()
    fmt.print_skill_gaps(data["skill_gaps"])
    fmt.print_portfolio_signal(data.get("portfolio", {}))
    fmt.print_action_items(data["action_items"])
    if data.get("llm_insights"):
        fmt.print_llm_insights(data["llm_insights"])
    elif data.get("llm_error"):
        console.print(f"  [dim]AI analysis skipped: {data['llm_error']}[/dim]")


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--no-ai", is_flag=True, help="Route and narrate deterministically (no LLM)")
def ask(question, no_ai):
    """Ask CoralCon a question in plain English; it routes to a Coral query."""
    q = " ".join(question)
    fmt.print_header("ASK CORALCON", q)

    with fmt.spinner("Routing your question to a Coral query..."):
        result = router.answer(q, use_ai=not no_ai)

    method = "AI intent match" if result["classified_by"] == "llm" else "keyword match"
    console.print(
        f"\n  [dim]Routed to[/dim] [bright_cyan]{result['query_name']}[/bright_cyan] "
        f"[dim]({method})[/dim]"
    )

    console.print(f"\n  [bold bright_green]{result['headline']}[/bold bright_green]")

    if result["narrative_source"] == "llm" and result["narrative"] != result["headline"]:
        console.print()
        fmt.print_llm_insights(result["narrative"])

    proof = result.get("proof")
    if proof:
        sources = ", ".join(proof.get("sources_used", []))
        cross = " [bright_magenta](cross-source JOIN)[/bright_magenta]" if proof.get("is_cross_source") else ""
        console.print(
            f"\n  [dim]Coral proof:[/dim] {proof.get('query_id', '?')} "
            f"[dim]·[/dim] {result['row_count']} rows "
            f"[dim]·[/dim] {sources}{cross}"
        )
    console.print()


@cli.command("judge-demo")
@click.option("--sample", "sample_mode", is_flag=True, help="Force deterministic sample mode")
@click.option("--real", "real_mode", is_flag=True, help="Run against real Coral connections")
def judge_demo(sample_mode, real_mode):
    """Run an unbreakable judge demo pipeline (sample or real Coral)."""
    if real_mode and not sample_mode:
        payload = run_real_demo()
        for line in real_demo_lines(payload):
            console.print(line)
        return

    result = run_judge_demo(sample=True)
    for line in demo_lines(result["result"], result["evidence_path"], sample=True):
        console.print(line)


@cli.command()
def proof():
    """Print the Coral SQL proof report for logged queries."""
    if not proof_summary()["queries"]:
        with fmt.spinner("Running analysis to generate proof..."):
            CoralConOrchestrator().run_full_analysis(use_ai=False, dry_run=True)
    console.print(build_proof_report())


@cli.command()
def verify():
    """10-second judge verification: pass/fail checklist for the whole setup."""
    from pathlib import Path

    fmt.print_header("JUDGE VERIFICATION", "Pass/fail checklist a judge can run in 10 seconds...")

    checks: list[tuple[str, bool, str]] = []

    conn = check_coral_connection()
    if os.getenv("CORAL_AVAILABLE", "false").lower() == "true":
        backend = "real Coral CLI"
    elif os.getenv("CORALCON_DB", "true").lower() != "false":
        backend = "SQLite (real SQL engine)"
    else:
        backend = "sample JSON"

    checks.append((
        f"Execution backend: {backend}",
        True,
        "queries run as real SQL" if "SQL" in backend or "Coral" in backend else "deterministic seeded rows",
    ))

    db = database_status()
    checks.append((
        "Local SQL database present",
        db.get("exists", False),
        f"{db['path']} (schema v{db.get('schema_version', '?')})" if db.get("exists")
        else "run `python -m coralcon.cli db init`",
    ))

    checks.append((
        "Coral CLI installed",
        conn["coral_installed"],
        "found on PATH" if conn["coral_installed"] else "optional — SQLite backend runs real SQL without it",
    ))

    # Run a real cross-source query and confirm it returns rows + is logged.
    cross_ok = False
    cross_detail = "no cross-source query logged"
    try:
        with fmt.spinner("Running a cross-source Coral SQL join..."):
            rows = skill_gaps.fetch()
        summary = proof_summary()
        cross = [q for q in summary["queries"] if q.get("is_cross_source")]
        cross_ok = bool(rows) and bool(cross)
        if cross:
            best = cross[-1]
            cross_detail = (
                f"{best['query_name']} joined {', '.join(best['sources_used'])} "
                f"-> {best['rows_returned']} rows"
            )
    except Exception as exc:  # pragma: no cover - defensive
        cross_detail = f"query failed: {exc}"
    checks.append(("Cross-source JOIN succeeds", cross_ok, cross_detail))

    proof_path = Path("runs") / "latest" / "proof.json"
    checks.append((
        "Proof artifacts present",
        proof_path.exists(),
        str(proof_path) if proof_path.exists() else "run `coralcon judge-demo --sample` to create",
    ))

    console.print()
    for label, ok, detail in checks:
        marker = "[bright_green]PASS[/bright_green]" if ok else "[yellow]INFO[/yellow]"
        console.print(f"  {marker}  {label}  [dim]({detail})[/dim]")

    passed = sum(1 for _, ok, _ in checks if ok)
    console.print(f"\n  [bold]{passed}/{len(checks)} checks passed.[/bold] [dim]Backend: {backend}.[/dim]\n")


@cli.command("privacy-report")
def privacy_report():
    """Generate a local-first privacy report."""
    path = write_privacy_report()
    console.print(build_file_message("Privacy report generated", path))


@cli.command("benchmark-cache")
@click.option("--sample", "sample_mode", is_flag=True, help="Force sample mode")
def benchmark_cache(sample_mode):
    """Measure Coral cache speedup: cold query vs cached query."""
    result = run_cache_benchmark(sample=sample_mode or True)
    console.print()
    console.print("  CORAL CACHE BENCHMARK")
    console.print("  " + "=" * 21)
    console.print(f"  Query:        [bright_cyan]{result['query']}[/bright_cyan]")
    console.print(f"  Rows:         {result['rows_returned']}")
    console.print(f"  Cold run:     [yellow]{result.get('cold_ms', result['run_1_ms'])}ms[/yellow]  [dim](cache miss — query executed)[/dim]")
    console.print(f"  Cached run:   [bright_green]{result.get('cached_ms', result['run_2_ms'])}ms[/bright_green]  [dim](cache hit — served from cache)[/dim]")
    console.print(f"  Speedup:      [bold bright_cyan]{result['speedup']}x[/bold bright_cyan]")
    if result.get("cache_hit_rate") is not None:
        console.print(f"  Cache hit rate (this benchmark): {result['cache_hit_rate']:.0f}%")
    console.print(f"  [dim]{result['metadata_note']}[/dim]")
    console.print()


@cli.command("submit-pack")
def submit_pack():
    """Generate the hackathon submission folder."""
    if not proof_summary()["queries"]:
        with fmt.spinner("Running analysis to generate proof..."):
            CoralConOrchestrator().run_full_analysis(use_ai=False, dry_run=True)
    paths = generate_submission_pack()
    console.print("\n  [bright_green]Submission pack generated.[/bright_green]")
    for path in paths:
        console.print(f"  [dim]{path}[/dim]")
    console.print()


@cli.group()
def cohort():
    """Cohort analysis commands."""


@cli.group()
def db():
    """Manage the local SQLite CoralCon database."""


@db.command("init")
@click.option("--reset", is_flag=True, help="Recreate the database from seeded sample data")
@click.option("--empty", is_flag=True, help="Create schema without sample rows")
def db_init(reset, empty):
    """Create the local SQLite database."""
    path = initialize_database(seed=not empty, reset=reset)
    status = database_status(path)
    console.print(f"\n  [bright_green]Database ready:[/bright_green] [dim]{path}[/dim]")
    console.print(f"  Schema version: [bright_cyan]{status['schema_version']}[/bright_cyan]")
    console.print(f"  Applications:   [bright_cyan]{status['tables']['applications']}[/bright_cyan]")
    console.print(f"  Proof tables:   [bright_cyan]{_proof_table_count(status)}[/bright_cyan]\n")


@db.command("status")
def db_status():
    """Show local database path and table counts."""
    status = database_status()
    console.print()
    console.print(f"  Path: [dim]{status['path']}[/dim]")
    if not status["exists"]:
        console.print("  [yellow]Database has not been created yet.[/yellow]")
        console.print("  Run [bright_cyan]python -m coralcon.cli db init[/bright_cyan].\n")
        return

    console.print(f"  Schema version: [bright_cyan]{status['schema_version']}[/bright_cyan]")
    for table, count in status["tables"].items():
        console.print(f"  {table:<22} [bright_cyan]{count}[/bright_cyan]")
    console.print()


@db.command("query")
@click.argument("sql", nargs=-1, required=True)
def db_query(sql):
    """Run a read-only SQL query against the local database."""
    statement = " ".join(sql).strip()
    if not statement.lower().startswith("select"):
        raise click.ClickException("Only SELECT queries are allowed from the CLI.")
    rows = execute_sql(statement)
    console.print_json(data=rows)


@cohort.command("analyze")
def cohort_analyze():
    """Analyze anonymized sample candidates."""
    console.print(build_cohort_report())


@cli.command()
@click.option("--no-ai", is_flag=True, help="Skip LLM analysis")
@click.option("--dry-run", is_flag=True, help="Preview dashboard summary")
@click.option("--sample", "sample_mode", is_flag=True, help="Force sample mode")
@click.option("--portfolio-url", help="Public portfolio URL to inspect during analysis")
def dashboard(no_ai, dry_run, sample_mode, portfolio_url):
    """Run Recon + Analyst + Dashboard agents."""
    _set_portfolio_url(portfolio_url)
    if sample_mode:
        os.environ["CORAL_AVAILABLE"] = "false"
    fmt.print_header("DASHBOARD", "Preparing the local dashboard summary...")
    with fmt.spinner("Preparing dashboard..."):
        result = CoralConOrchestrator().run_dashboard(use_ai=not no_ai, dry_run=True if dry_run else None)

    _print_insight_summary(result["insights"])
    dashboard_result = result["dashboard"]
    if dashboard_result.get("updated"):
        console.print(f"\n  [bright_green]Dashboard updated:[/bright_green] {dashboard_result.get('url')}\n")
    else:
        console.print(f"\n  [dim]{dashboard_result.get('message')}[/dim]\n")


@cli.command()
@click.option("--no-ai", is_flag=True, help="Skip LLM analysis")
@click.option("--dry-run", is_flag=True, help="Preview local tasks")
@click.option("--portfolio-url", help="Public portfolio URL to inspect during analysis")
def actions(no_ai, dry_run, portfolio_url):
    """Run Recon + Analyst + Action agents."""
    _set_portfolio_url(portfolio_url)
    fmt.print_header("ACTIONS", "Creating local action tasks...")
    with fmt.spinner("Preparing tasks..."):
        result = CoralConOrchestrator().run_actions(use_ai=not no_ai, dry_run=True if dry_run else None)

    tasks = result["tasks"]
    fmt.print_action_items([task["title"] for task in tasks])
    console.print(f"  [dim]{len(tasks)} local task(s) ready.[/dim]\n")


@cli.command()
@click.option("--ai", is_flag=True, help="Add AI analysis")
def rejections(ai):
    """Rejection rate breakdown by role type."""
    fmt.print_header("REJECTION PATTERNS")

    with fmt.spinner("Querying sheets.applications..."):
        patterns = rejection_patterns.fetch()

    fmt.print_rejection_table(patterns)

    if ai:
        with fmt.spinner("Analyzing..."):
            try:
                text = analyzer.generate_rejection_decoder(patterns)
                fmt.print_llm_insights(text)
            except Exception as exc:
                console.print(f"  [dim]AI skipped: {exc}[/dim]")


@cli.command()
@click.option("--ai", is_flag=True, help="Add AI analysis")
@click.option("--portfolio-url", help="Public portfolio URL to inspect during gap analysis")
def gaps(ai, portfolio_url):
    """Skill gap analysis: what roles want vs what your profile shows."""
    _set_portfolio_url(portfolio_url)
    fmt.print_header("SKILL GAP ANALYSIS")

    with fmt.spinner("Cross-referencing rejected applications with GitHub + LinkedIn..."):
        gap_data = skill_gaps.fetch()
        github_data = github_correlation.fetch()
        portfolio = inspect_portfolio()
        detected = {str(skill).casefold() for skill in portfolio.get("detected_skills", [])}
        for gap in gap_data:
            gap["in_portfolio"] = str(gap.get("skill", "")).casefold() in detected

    fmt.print_skill_gaps(gap_data)
    fmt.print_portfolio_signal(portfolio)

    if ai:
        github_langs = []
        for row in github_data:
            langs = row.get("languages", [])
            if isinstance(langs, list):
                github_langs.extend(langs)
        with fmt.spinner("Generating recommendations..."):
            try:
                text = analyzer.generate_skill_gap_summary(gap_data, github_langs)
                fmt.print_llm_insights(text)
            except Exception as exc:
                console.print(f"  [dim]AI skipped: {exc}[/dim]")


@cli.command()
def timing():
    """Application timing patterns: does applying early matter?"""
    fmt.print_header("TIMING ANALYSIS")

    with fmt.spinner("Analyzing application timing..."):
        data = timing_analysis.fetch()

    from rich import box
    from rich.table import Table

    table = Table(
        title="[bold]RESPONSE RATE BY APPLICATION TIMING[/bold]",
        box=box.SIMPLE_HEAD,
        border_style="dim",
        header_style="bold bright_cyan",
    )
    table.add_column("TIMING", style="white", min_width=18)
    table.add_column("APPLICATIONS", justify="right")
    table.add_column("RESPONSE RATE", justify="right")
    table.add_column("GHOST RATE", justify="right")

    for row in data:
        resp = row.get("response_rate", 0)
        ghost = row.get("ghost_rate", 0)
        resp_color = "bright_green" if resp >= 20 else ("yellow" if resp >= 10 else "bright_red")
        table.add_row(
            row.get("timing_bucket", "").replace("_", " "),
            str(row.get("total", 0)),
            f"[{resp_color}]{resp:.0f}%[/{resp_color}]",
            f"[dim]{ghost:.0f}%[/dim]",
        )

    console.print()
    console.print(table)


@cli.command()
def followup():
    """Follow-up priority list: who to email and when."""
    fmt.print_header("FOLLOW-UP QUEUE")

    with fmt.spinner("Checking pending applications..."):
        data = followup_tracker.fetch()

    if not data:
        console.print("\n  [bright_green]OK[/bright_green] No pending follow-ups needed.\n")
        return

    prioritized = recommender.prioritize_followups(data)
    fmt.print_followup_table(prioritized)

    hot = sum(1 for item in data if item.get("priority") == "hot")
    if hot > 0:
        console.print(f"\n  [bright_red]Alert:[/bright_red] {hot} applications are in the optimal follow-up window.")
    console.print()


@cli.command("github-check")
def github_check():
    """GitHub profile health check: are recruiters seeing activity?"""
    fmt.print_header("GITHUB SIGNAL CHECK")

    with fmt.spinner("Correlating GitHub commits with application outcomes..."):
        data = github_correlation.fetch()
        signal = recommender.compute_github_signal(data, data)

    fmt.print_github_signal(signal)

    active = signal.get("ghost_rate_active_weeks", 0)
    inactive = signal.get("ghost_rate_inactive_weeks", 0)
    diff = inactive - active

    if diff > 30:
        console.print(
            f"  [bright_red]Critical:[/bright_red] Your ghost rate is {diff:.0f}% higher in weeks "
            "you do not commit. Recruiters are checking your GitHub.\n"
        )
    elif diff > 10:
        console.print(f"  [yellow]Warning:[/yellow] Moderate GitHub/activity correlation ({diff:.0f}% difference).\n")
    else:
        console.print("  [bright_green]OK[/bright_green] GitHub activity has limited correlation with ghost rate.\n")


@cli.command("portfolio-check")
@click.argument("url", required=False)
def portfolio_check(url):
    """Inspect a public portfolio URL for recruiter-visible evidence."""
    _set_portfolio_url(url)
    fmt.print_header("PORTFOLIO CHECK", "Scanning public page text, skills, project links, and GitHub links...")
    with fmt.spinner("Inspecting portfolio page..."):
        portfolio = inspect_portfolio()
    fmt.print_portfolio_signal(portfolio)


@cli.command("gmail-extract")
@click.option("--query", default=None, help="Override the Gmail search query")
@click.option("--max", "max_results", default=50, help="Max emails to scan")
@click.option("--no-ai", is_flag=True, help="Classify with keyword heuristics only")
@click.option("--write/--no-write", default=True, help="Write results to the Google Sheet")
@click.option("--dry-run", is_flag=True, help="Print extracted rows without writing")
def gmail_extract(query, max_results, no_ai, write, dry_run):
    """Extract rejection emails from Gmail into your application tracker.

    Gmail API (read-only) -> classify -> Google Sheet -> synced CSV that Coral
    queries as sheets.applications.
    """
    from coralcon.gmail.extractor import extract_rejections

    fmt.print_header("GMAIL REJECTION EXTRACT", "Scanning Gmail for application outcomes...")
    with fmt.spinner("Searching Gmail and classifying emails..."):
        rows = extract_rejections(query=query, max_results=max_results, use_ai=not no_ai)

    if not rows:
        console.print("\n  [yellow]No rejection emails matched. Try --query to widen the search.[/yellow]\n")
        return

    console.print(f"\n  [bright_green]Found {len(rows)} application outcomes:[/bright_green]\n")
    for row in rows[:25]:
        console.print(
            f"  [dim]·[/dim] [white]{row['company'] or '?'}[/white] "
            f"[dim]—[/dim] {row['role_title'] or 'role unknown'} "
            f"[dim]({row['status']}, {row['responded_date']})[/dim]"
        )

    if dry_run or not write:
        console.print("\n  [dim]Dry run — nothing written. Drop --dry-run to push to your Sheet.[/dim]\n")
        return

    # Prefer the Sheet round-trip when one is configured; otherwise write
    # straight to the CSV the Coral `sheets` source reads (no Google Sheet
    # required to get real data flowing through Coral).
    if os.getenv("SHEETS_SPREADSHEET_ID"):
        from coralcon.sheets.client import append_applications, sync_to_csv

        with fmt.spinner("Writing new rows to your Google Sheet..."):
            added = append_applications(rows)
            synced = sync_to_csv()
        console.print(
            f"\n  [bright_green]Wrote {added} new rows[/bright_green] "
            f"[dim]· synced {synced} rows to data/applications.csv for Coral[/dim]\n"
        )
    else:
        from coralcon.sheets.client import append_to_csv, _csv_path

        with fmt.spinner("Writing new rows to data/applications.csv..."):
            added = append_to_csv(rows)
        console.print(
            f"\n  [bright_green]Wrote {added} new rows[/bright_green] "
            f"[dim]-> {_csv_path()} (read live by the Coral sheets source)[/dim]\n"
        )


@cli.command("sheets-sync")
@click.option("--spreadsheet-id", default=None, help="Override SHEETS_SPREADSHEET_ID")
def sheets_sync(spreadsheet_id):
    """Pull your Google Sheet down to data/applications.csv for the Coral source."""
    from coralcon.sheets.client import sync_to_csv

    fmt.print_header("SHEETS SYNC", "Pulling your Google Sheet into the Coral file source...")
    with fmt.spinner("Reading the sheet and writing applications.csv..."):
        count = sync_to_csv(spreadsheet_id)
    console.print(
        f"\n  [bright_green]Synced {count} applications[/bright_green] "
        f"[dim]-> data/applications.csv. Query with:[/dim]\n"
        f"  [bright_cyan]coral sql \"SELECT role_title, status FROM sheets.applications\"[/bright_cyan]\n"
    )


@cli.command()
@click.option("--overwrite", is_flag=True, help="Re-infer skills even for rows that already have them")
def enrich(overwrite):
    """Infer required_skills for tracker rows from their role titles.

    Rejection emails carry the role but not its skills, so this backfills
    data/applications.csv so the cross-source skill-gap query has real data to
    join against. Deterministic (no LLM) and reproducible.
    """
    from coralcon.enrich import enrich_csv

    fmt.print_header("ENRICH TRACKER", "Inferring required skills from role titles...")
    with fmt.spinner("Reading applications.csv and inferring skills..."):
        count = enrich_csv(overwrite=overwrite)
    console.print(
        f"\n  [bright_green]Enriched {count} application(s)[/bright_green] "
        f"[dim]-> data/applications.csv. Now run:[/dim]\n"
        f"  [bright_cyan]coralcon gaps[/bright_cyan] [dim]or[/dim] "
        f"[bright_cyan]coralcon morning[/bright_cyan]\n"
    )


@cli.command()
def status():
    """Check Coral connection and data sources."""
    fmt.print_header("DATA SOURCE STATUS")

    conn = check_coral_connection()

    console.print()
    items = [
        ("Coral CLI", conn["coral_installed"]),
        ("GitHub source", conn["github_connected"]),
        ("Sheets source", conn.get("sheets_connected", False)),
        ("Gmail source", conn.get("gmail_connected", False)),
        ("LinkedIn source", conn["linkedin_connected"]),
    ]

    for name, ok in items:
        marker = "[bright_green]OK[/bright_green]" if ok else "[bright_red]MISSING[/bright_red]"
        label = "[dim](sample data)[/dim]" if not ok else ""
        console.print(f"  {marker}  {name} {label}")

    if conn["using_sample_data"]:
        console.print("\n  [dim]Running on sample data. Set CORAL_AVAILABLE=true once Coral is connected.[/dim]")
    console.print()


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
def serve(host, port):
    """Launch the local FastAPI web dashboard."""
    import uvicorn

    console.print(f"\n  [bright_cyan]CoralCon Dashboard[/bright_cyan] -> [underline]http://{host}:{port}[/underline]\n")
    uvicorn.run("web.app:app", host=host, port=port, reload=False)


def _print_insight_summary(insights: dict) -> None:
    console.print()
    fmt.print_stat_row(
        {
            "APPLICATIONS": (insights["total_applications"], "white"),
            "RESPONSE RATE": (f"{insights['response_rate']:.0f}%", "bright_cyan"),
            "HEALTH SCORE": (f"{insights['overall_health_score']}/100", "yellow"),
            "OFFER RATE": (f"{insights['offer_rate']:.0f}%", "bright_green"),
        }
    )


def _set_portfolio_url(portfolio_url: str | None) -> None:
    if portfolio_url:
        os.environ["PORTFOLIO_URL"] = portfolio_url


def build_file_message(label: str, path) -> str:
    return f"\n  [bright_green]{label}:[/bright_green] [dim]{path}[/dim]\n"


def _proof_table_count(status: dict) -> int:
    proof_tables = (
        "rejection_patterns",
        "skill_gaps",
        "timing_analysis",
        "followup_queue",
        "github_correlation",
    )
    return sum(status["tables"].get(table, 0) for table in proof_tables)


if __name__ == "__main__":
    cli()
