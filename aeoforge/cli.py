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


def save_html_report(audit_result, nav_data, filepath: str):
    """Generate a self-contained, responsive dark-theme HTML report."""
    score = audit_result.overall_score
    grade = audit_result.grade
    color = "#10b981" if score >= 80 else ("#f59e0b" if score >= 60 else "#ef4444")
    pillars = audit_result.pillars

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AEOForge Audit Report — {audit_result.url}</title>
    <style>
        :root {{ --bg: #0b0f19; --card: #111827; --border: #1f2937; --text: #f9fafb; --dim: #9ca3af; }}
        body {{ margin: 0; padding: 2rem; background: var(--bg); color: var(--text); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }}
        .container {{ max-width: 1000px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; }}
        .badge {{ background: #0668e1; color: white; padding: 4px 10px; border-radius: 9999px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; }}
        .hero {{ display: flex; gap: 2rem; align-items: center; background: var(--card); border: 1px solid var(--border); padding: 2rem; border-radius: 1rem; margin-bottom: 2rem; }}
        .score-circle {{ min-width: 120px; height: 120px; border-radius: 50%; border: 6px solid {color}; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold; color: {color}; }}
        .score-grade {{ font-size: 1rem; color: var(--dim); }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
        .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.25rem; }}
        .card h3 {{ margin-top: 0; font-size: 0.95rem; color: var(--dim); font-weight: 500; }}
        .card .val {{ font-size: 1.5rem; font-weight: bold; margin: 0.5rem 0; color: #38bdf8; }}
        .list-section {{ background: var(--card); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1.5rem; }}
        .list-section h2 {{ margin-top: 0; font-size: 1.15rem; }}
        .item {{ padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.95rem; }}
        .item:last-child {{ border-bottom: none; }}
        .code-box {{ background: #000; border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; font-family: monospace; font-size: 0.85rem; overflow-x: auto; color: #a7f3d0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin: 0; font-size: 1.5rem;">⚡ AEOForge Audit Report</h1>
                <p style="margin: 4px 0 0; color: var(--dim);">{audit_result.url}</p>
            </div>
            <span class="badge">Meta AI Hackathon 2026</span>
        </div>

        <div class="hero">
            <div class="score-circle">
                {score}
                <span class="score-grade">Grade {grade}</span>
            </div>
            <div>
                <h2 style="margin: 0 0 0.5rem;">{audit_result.status}</h2>
                <p style="margin: 0; color: var(--dim); line-height: 1.5;">
                    Visual Guidance: {audit_result.visual_analysis.get('agent_navigation_advice', 'Clean layout.')}
                </p>
            </div>
        </div>

        <div class="grid">
            <div class="card">
                <h3>Pillar A: Citability</h3>
                <div class="val">{pillars['pillar_a_citability']['score']} / 25</div>
                <small style="color: var(--dim);">Fact Density: {pillars['pillar_a_citability']['details']['fact_density_pct']}%</small>
            </div>
            <div class="card">
                <h3>Pillar B: Navigability</h3>
                <div class="val">{pillars['pillar_b_navigability']['score']} / 25</div>
                <small style="color: var(--dim);">Token Ratio: {pillars['pillar_b_navigability']['details']['token_ratio_pct']}%</small>
            </div>
            <div class="card">
                <h3>Pillar C: Protocols</h3>
                <div class="val">{pillars['pillar_c_protocols']['score']} / 25</div>
                <small style="color: var(--dim);">llms.txt: {'Detected' if pillars['pillar_c_protocols']['details']['has_llms_txt'] else 'Missing'}</small>
            </div>
            <div class="card">
                <h3>Pillar D: Structured Data</h3>
                <div class="val">{pillars['pillar_d_structured_data']['score']} / 25</div>
                <small style="color: var(--dim);">Schemas: {len(pillars['pillar_d_structured_data']['details']['schema_types'])}</small>
            </div>
        </div>

        <div class="list-section">
            <h2 style="color: #34d399;">✅ Key Strengths</h2>
            {"".join(f'<div class="item">✓ {s}</div>' for s in audit_result.key_strengths)}
        </div>

        <div class="list-section">
            <h2 style="color: #f87171;">⚠️ Critical Agent Blockers & Traps</h2>
            {"".join(f'<div class="item">✗ {b}</div>' for b in audit_result.critical_blockers) if audit_result.critical_blockers else '<div class="item">Zero critical navigation traps detected.</div>'}
        </div>

        <div class="list-section">
            <h2 style="color: #fbbf24;">🛠️ Priority Remediation Action Plan</h2>
            {"".join(f'<div class="item">{i}. {a}</div>' for i, a in enumerate(audit_result.action_plan, 1))}
        </div>
    </div>
</body>
</html>
"""
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)


async def run_audit_command(url: str, json_output: bool = False, html_output: str = None, crawl: bool = False, max_pages: int = 3):
    """Execute audit command with optional BFS multi-page crawling."""
    if not json_output:
        print_banner()

    navigator = BrowserNavigator(headless=settings.playwright_headless)
    scorer = AEOScoringEngine()
    from urllib.parse import urlparse, urljoin

    crawled_results = []
    visited_urls = set()
    queue = [url]
    parsed_entry = urlparse(url)
    origin = f"{parsed_entry.scheme}://{parsed_entry.netloc}"

    with Progress(
        SpinnerColumn(),
        TextColumn("[bold green]{task.description}"),
        console=console,
        transient=True
    ) as progress:
        while queue and len(visited_urls) < (max_pages if crawl else 1):
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            task1 = progress.add_task(f"Navigating to {current_url}...", total=None)
            nav_data = await navigator.inspect_url(current_url, capture_screenshot=True)

            progress.update(task1, description=f"Auditing AEO for {current_url}...")
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
            crawled_results.append((audit_result, nav_data))

            # If crawling, discover internal links
            if crawl:
                for m in nav_data.interactive_marks:
                    href = m.get("href")
                    if href and not href.startswith("#") and not href.startswith("mailto:"):
                        full_url = urljoin(current_url, href)
                        if urlparse(full_url).netloc == parsed_entry.netloc and full_url not in visited_urls:
                            queue.append(full_url)

    # Use first result for primary display / HTML report
    primary_audit, primary_nav = crawled_results[0]

    if html_output:
        save_html_report(primary_audit, primary_nav, html_output)
        console.print(f"[bold green]✨ Interactive HTML report saved to {html_output}[/bold green]\n")

    if json_output:
        print(json.dumps([r[0].model_dump() for r in crawled_results], indent=2))
        return

    # If crawl mode was used and multiple pages audited, show Sitewide Table
    if len(crawled_results) > 1:
        avg_score = round(sum(r[0].overall_score for r in crawled_results) / len(crawled_results), 1)
        console.print(f"\n[bold cyan]🌐 Sitewide Crawl Summary ({len(crawled_results)} pages audited):[/bold cyan]")
        console.print(f"[bold]Average Domain AEO Score:[/bold] [bold green]{avg_score} / 100[/bold green]\n")

        crawl_table = Table(title="Page-by-Page AEO Breakdown", border_style="cyan")
        crawl_table.add_column("Page URL", style="underline")
        crawl_table.add_column("Score", justify="center")
        crawl_table.add_column("Grade", justify="center")
        crawl_table.add_column("Key Blocker", style="dim")

        for aud, _ in crawled_results:
            first_blocker = aud.critical_blockers[0] if aud.critical_blockers else "None (Clean)"
            color_grade = "green" if aud.overall_score >= 80 else ("yellow" if aud.overall_score >= 60 else "red")
            crawl_table.add_row(
                aud.url,
                f"[{color_grade}]{aud.overall_score}[/{color_grade}]",
                f"[{color_grade}]{aud.grade}[/{color_grade}]",
                first_blocker[:45] + ("..." if len(first_blocker) > 45 else "")
            )
        console.print(crawl_table)
        console.print("")

    # Print Primary Rich Score Card
    color = "green" if primary_audit.overall_score >= 80 else ("yellow" if primary_audit.overall_score >= 60 else "red")
    console.print(f"\n[bold]Target URL:[/bold] [underline]{primary_audit.url}[/underline]")
    console.print(f"[bold]AEO & Agent Score:[/bold] [{color}]{primary_audit.overall_score} / 100 [bold]({primary_audit.grade})[/bold][/{color}]")
    console.print(f"[dim]{primary_audit.status}[/dim]\n")

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
    audit_parser.add_argument("--html", default=None, help="Save interactive HTML report to file")
    audit_parser.add_argument("--crawl", action="store_true", help="Enable multi-page crawl of internal links")
    audit_parser.add_argument("--max-pages", type=int, default=3, help="Maximum pages to crawl (default: 3)")

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
        asyncio.run(run_audit_command(
            args.url,
            json_output=args.json,
            html_output=args.html,
            crawl=args.crawl,
            max_pages=args.max_pages
        ))
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
