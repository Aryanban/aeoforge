"""Command Line Interface for AEOForge with rich terminal reporting."""

import argparse
import asyncio
import json
import os
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.scorer.engine import AEOScoringEngine
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt
from aeoforge.spec.schema_gen import generate_schema_jsonld
from aeoforge.patcher.ast_patcher import CodebasePatcher
from aeoforge.config import settings

console = Console()


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]⚡ AEOForge[/bold cyan] [bold white]• Autonomous Meta AI Web Agent & AEO Auditor[/bold white]\n"
        "[dim]Meta Global AI Developer Hackathon 2026 | Powered by Meta Llama 3.2 Vision[/dim]",
        border_style="cyan"
    ))


async def run_audit_command(url: str, json_output: bool = False):
    """Execute audit command."""
    if not json_output:
        print_banner()

    navigator = BrowserNavigator(headless=settings.playwright_headless)
    scorer = AEOScoringEngine()

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        task1 = progress.add_task(f"Navigating to {url} and capturing DOM/Visuals...", total=None)
        nav_data = await navigator.inspect_url(url, capture_screenshot=True)

        progress.update(task1, description="Running 4-Pillar AEO & Meta AI visual analysis...")
        audit_result = await scorer.audit(
            url=nav_data.final_url,
            html=nav_data.html,
            text_content=nav_data.text_content,
            raw_html_tokens=nav_data.raw_html_tokens,
            text_tokens=nav_data.text_tokens,
            traps=nav_data.traps,
            interactive_marks=nav_data.interactive_marks,
            a11y_tree=nav_data.a11y_tree,
            screenshot_b64=nav_data.screenshot_base64
        )

    if json_output:
        print(json.dumps(audit_result.model_dump(), indent=2))
        return

    # Print Rich Score Card
    color = "green" if audit_result.overall_score >= 80 else ("yellow" if audit_result.overall_score >= 60 else "red")
    console.print(f"\n[bold]Target URL:[/bold] [underline]{audit_result.url}[/underline]")
    console.print(f"[bold]AEO & Agent Score:[/bold] [{color}]{audit_result.overall_score} / 100 [bold]({audit_result.grade})[/bold][/{color}]")
    console.print(f"[dim]{audit_result.status}[/dim]\n")

    # Table of 4 Pillars
    table = Table(title="📊 The 4-Pillar AEO Breakdown", border_style="dim")
    table.add_column("Pillar", style="bold cyan")
    table.add_column("Score", justify="center")
    table.add_column("Key Metric", style="dim")

    pillars = audit_result.pillars
    table.add_row(
        "Pillar A: Citability & Answerability",
        f"{pillars['pillar_a_citability']['score']} / 25",
        f"Fact Density: {pillars['pillar_a_citability']['details']['fact_density_pct']}%"
    )
    table.add_row(
        "Pillar B: Agent Navigability & Token Cost",
        f"{pillars['pillar_b_navigability']['score']} / 25",
        f"Token Ratio: {pillars['pillar_b_navigability']['details']['token_ratio_pct']}% | Traps: {pillars['pillar_b_navigability']['details']['traps_detected_count']}"
    )
    table.add_row(
        "Pillar C: Machine Protocols & Discovery",
        f"{pillars['pillar_c_protocols']['score']} / 25",
        f"llms.txt: {'✅' if pillars['pillar_c_protocols']['details']['has_llms_txt'] else '❌'}"
    )
    table.add_row(
        "Pillar D: Structured Data & API Exposeability",
        f"{pillars['pillar_d_structured_data']['score']} / 25",
        f"Schemas: {', '.join(pillars['pillar_d_structured_data']['details']['schema_types']) or 'None'}"
    )
    console.print(table)

    # Key Strengths & Blockers
    if audit_result.key_strengths:
        console.print("\n[bold green]✅ Key Strengths:[/bold green]")
        for s in audit_result.key_strengths:
            console.print(f"  • {s}")

    if audit_result.critical_blockers:
        console.print("\n[bold red]⚠️ Critical Agent Blockers & Traps:[/bold red]")
        for b in audit_result.critical_blockers:
            console.print(f"  • {b}")

    # Action Plan
    console.print("\n[bold yellow]🛠️ Priority Remediation Plan:[/bold yellow]")
    for i, a in enumerate(audit_result.action_plan, 1):
        console.print(f"  {i}. {a}")

    console.print(f"\n[dim]Run `aeoforge spec {url}` to auto-generate `agent-spec.json` and `llms.txt`.[/dim]\n")


async def run_spec_command(url: str, out_dir: str = "./output"):
    """Generate agent-spec.json, llms.txt, and schema."""
    print_banner()
    os.makedirs(out_dir, exist_ok=True)

    navigator = BrowserNavigator()
    scorer = AEOScoringEngine()

    console.print(f"[cyan]Generating Machine-to-Machine Handshake for [bold]{url}[/bold]...[/cyan]")
    nav_data = await navigator.inspect_url(url, capture_screenshot=False)
    audit = await scorer.audit(
        url=nav_data.final_url,
        html=nav_data.html,
        text_content=nav_data.text_content,
        raw_html_tokens=nav_data.raw_html_tokens,
        text_tokens=nav_data.text_tokens,
        traps=nav_data.traps,
        interactive_marks=nav_data.interactive_marks,
        a11y_tree=nav_data.a11y_tree
    )

    endpoints = audit.pillars["pillar_d_structured_data"]["details"].get("discovered_endpoints", [])
    spec = generate_agent_spec(
        url=nav_data.final_url,
        aeo_score=audit.overall_score,
        html=nav_data.html,
        traps=nav_data.traps,
        interactive_marks=nav_data.interactive_marks,
        discovered_endpoints=endpoints
    )
    llms_txt = generate_llms_txt(
        url=nav_data.final_url,
        title=nav_data.title,
        text_content=nav_data.text_content,
        interactive_marks=nav_data.interactive_marks
    )
    schema = generate_schema_jsonld(
        url=nav_data.final_url,
        title=nav_data.title,
        description=nav_data.text_content[:150],
        html=nav_data.html
    )

    # Save files
    spec_file = os.path.join(out_dir, "agent-spec.json")
    llms_file = os.path.join(out_dir, "llms.txt")
    schema_file = os.path.join(out_dir, "schema.jsonld")

    with open(spec_file, "w") as f:
        json.dump(spec, f, indent=2)
    with open(llms_file, "w") as f:
        f.write(llms_txt)
    with open(schema_file, "w") as f:
        json.dump(schema, f, indent=2)

    console.print(f"[bold green]✨ Artifacts successfully generated in {out_dir}:[/bold green]")
    console.print(f"  • {spec_file} (Machine-to-Machine Agent Navigation Spec)")
    console.print(f"  • {llms_file} (Spec-compliant llms.txt)")
    console.print(f"  • {schema_file} (Schema.org JSON-LD Entity Graph)\n")


def run_serve_command(host: str, port: int):
    """Launch FastAPI application server."""
    import uvicorn
    print_banner()
    console.print(f"[green]Starting AEOForge API Server on http://{host}:{port}...[/green]")
    uvicorn.run("aeoforge.main:app", host=host, port=port, reload=False)


def main():
    parser = argparse.ArgumentParser(description="AEOForge: Autonomous Meta AI Agent & AEO Auditor")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # audit subcommand
    audit_parser = subparsers.add_parser("audit", help="Audit website for AEO & Agentic Readiness")
    audit_parser.add_argument("url", help="Target website URL to inspect")
    audit_parser.add_argument("--json", action="store_true", help="Output pure JSON")

    # spec subcommand
    spec_parser = subparsers.add_parser("spec", help="Generate agent-spec.json and llms.txt")
    spec_parser.add_argument("url", help="Target website URL")
    spec_parser.add_argument("--out-dir", default="./output", help="Directory to save generated artifacts")

    # patch subcommand
    patch_parser = subparsers.add_parser("patch", help="Auto-patch local codebase with llms.txt & JSON-LD")
    patch_parser.add_argument("target_dir", help="Path to local website codebase directory")
    patch_parser.add_argument("--url", default="https://example.com", help="Domain URL")

    # serve subcommand
    serve_parser = subparsers.add_parser("serve", help="Run AEOForge REST API server")
    serve_parser.add_argument("--host", default=settings.aeoforge_host, help="Bind host")
    serve_parser.add_argument("--port", type=int, default=settings.aeoforge_port, help="Bind port")

    args = parser.parse_args()

    if args.command == "audit":
        asyncio.run(run_audit_command(args.url, json_output=args.json))
    elif args.command == "spec":
        asyncio.run(run_spec_command(args.url, out_dir=args.out_dir))
    elif args.command == "patch":
        print_banner()
        patcher = CodebasePatcher(args.target_dir)
        console.print(f"[cyan]Patching codebase at {args.target_dir}...[/cyan]")
        dummy_llms = f"# {args.url}\n> Autonomous AI directory generated by AEOForge.\n"
        dummy_spec = {"$schema": "https://aeoforge.dev/schemas/agent-spec-v1.json", "domain": args.url}
        dummy_schema = {"@context": "https://schema.org", "@type": "WebSite", "url": args.url}
        res = patcher.patch_all(dummy_llms, dummy_spec, dummy_schema)
        for r in res:
            console.print(f"  • {r.get('artifact', 'file')}: [bold green]{r.get('action')}[/bold green] -> {r.get('file')}")
    elif args.command == "serve":
        run_serve_command(args.host, args.port)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
