"""FastAPI Application Server for AEOForge."""

import asyncio
import io
import json
import os
import zipfile
from pathlib import Path
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, HttpUrl

from aeoforge import __version__
from aeoforge.config import settings
from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.scorer.engine import AEOScoringEngine, AEOAuditResult, calculate_grade
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt, generate_llms_full_txt
from aeoforge.spec.schema_gen import generate_schema_jsonld
from aeoforge.utils.deobfuscator import extract_obfuscated_emails, deobfuscate_cloudflare_email
from aeoforge.patcher.ast_patcher import CodebasePatcher
from aeoforge.models.meta_client import MetaAIClient
from aeoforge.scorer.competitor import compare_competitors, CompetitorComparisonResult
from aeoforge.storage import storage

app = FastAPI(
    title="AEOForge API",
    description="Autonomous Meta AI Agent for Web Agent-Readiness, AEO Auditing & Machine Navigation Specs",
    version=__version__
)

# Enable CORS for Next.js frontend dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AuditRequest(BaseModel):
    url: str
    capture_screenshot: bool = True


class CompareRequest(BaseModel):
    target_url: str
    competitor_url: str


class BundleExportRequest(BaseModel):
    url: str
    agent_spec: Optional[Dict[str, Any]] = None
    llms_txt: Optional[str] = None
    llms_full_txt: Optional[str] = None
    schema_jsonld: Optional[Dict[str, Any]] = None
    waf_rules: Optional[Dict[str, str]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 10


class BatchAuditRequest(BaseModel):
    urls: List[str]
    capture_screenshot: bool = False


class PatchRequest(BaseModel):
    target_dir: str
    url: str = "https://example.com"
    agent_spec: Optional[Dict[str, Any]] = None
    llms_txt: Optional[str] = None
    schema_jsonld: Optional[Dict[str, Any]] = None


class SpecRequest(BaseModel):
    url: str


class DeobfuscateRequest(BaseModel):
    cf_hex: Optional[str] = None
    html: Optional[str] = None


class ModelConfigRequest(BaseModel):
    provider: str  # "ollama" | "cloud"
    model: Optional[str] = None
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    api_base: Optional[str] = None


@app.get("/health")
async def health_check():
    """Health check endpoint returning system status."""
    return {
        "status": "healthy",
        "version": __version__,
        "engine": "AEOForge",
        "model": settings.meta_model_name,
        "environment": settings.aeoforge_env
    }


@app.get("/api/v1/system-status")
async def system_status_endpoint():
    """Returns local Ollama and cloud model availability status."""
    client = MetaAIClient()
    ollama_model, has_vis = await client._resolve_ollama_model()
    return {
        "ollama_available": ollama_model is not None,
        "ollama_model": ollama_model,
        "ollama_has_vision": has_vis,
        "meta_api_configured": bool(settings.meta_model_api_key),
        "active_mode": "local_ollama" if ollama_model else ("meta_cloud" if settings.meta_model_api_key else "heuristics"),
        "version": __version__
    }


@app.get("/api/v1/models")
async def list_models_endpoint():
    """List available local and cloud AI models."""
    client = MetaAIClient()
    return await client.get_system_info()


@app.post("/api/v1/models/config")
async def update_model_config_endpoint(request: ModelConfigRequest):
    """Update active model, provider, or API key with live connection test."""
    client = MetaAIClient()
    res = await client.update_config(request.model_dump())
    return res


@app.get("/api/v1/tools")
async def get_agent_tools_endpoint():
    """Return tool schemas formatted for OpenAI, Anthropic, and MCP agent harnesses."""
    from aeoforge.mcp_server import MCP_TOOLS

    openai_tools = []
    anthropic_tools = []
    for t in MCP_TOOLS:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"]
            }
        })
        anthropic_tools.append({
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["inputSchema"]
        })

    return {
        "status": "ready",
        "version": __version__,
        "supported_harnesses": ["MCP (Model Context Protocol)", "OpenAI Function Calling", "Anthropic Tool Use", "LangChain", "Cursor", "Windsurf"],
        "mcp_tools": MCP_TOOLS,
        "openai_tools": openai_tools,
        "anthropic_tools": anthropic_tools
    }


@app.post("/api/v1/audit", response_model=AEOAuditResult)
async def audit_endpoint(request: AuditRequest):
    """Run full visual, semantic, and protocol audit on a target URL."""
    try:
        navigator = BrowserNavigator(headless=settings.playwright_headless)
        scorer = AEOScoringEngine()

        nav_data = await navigator.inspect_url(request.url, capture_screenshot=request.capture_screenshot)
        result = await scorer.audit(
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
        result.title = nav_data.title

        # Persist to SQLite and compute domain progression metrics
        try:
            audit_id, prog = storage.save_audit(nav_data.final_url, result.model_dump())
            result.audit_id = audit_id
            result.progression = prog
        except Exception as store_err:
            print(f"[Warning] Failed to persist audit to SQLite storage: {store_err}")

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


@app.post("/api/v1/compare", response_model=CompetitorComparisonResult)
async def compare_endpoint(request: CompareRequest):
    """Run dual headless audit and generate head-to-head AEO outranking blueprint."""
    try:
        result = await compare_competitors(
            target_url=request.target_url,
            competitor_url=request.competitor_url,
            headless=settings.playwright_headless
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Competitor comparison failed: {str(e)}")


@app.post("/api/v1/export-bundle")
async def export_bundle_endpoint(request: BundleExportRequest):
    """Package all AI agent handshake artifacts into a downloadable ZIP archive."""
    try:
        domain = urlparse(request.url).netloc or "site"
        domain_safe = domain.replace(":", "_").replace("/", "_")

        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            # 1. agent-spec.json
            spec_content = json.dumps(request.agent_spec or {"domain": domain}, indent=2)
            z.writestr("agent-spec.json", spec_content)

            # 2. llms.txt
            llms_content = request.llms_txt or f"# {domain}\n> Autonomous AI directory generated by AEOForge.\n"
            z.writestr("llms.txt", llms_content)

            # 3. llms-full.txt
            if request.llms_full_txt:
                z.writestr("llms-full.txt", request.llms_full_txt)

            # 4. schema.jsonld
            schema_content = json.dumps(request.schema_jsonld or {"@context": "https://schema.org"}, indent=2)
            z.writestr("schema.jsonld", schema_content)

            # 5. Cloudflare & Nginx WAF rules
            if request.waf_rules:
                waf_text = f"// Cloudflare Custom Rules Expression\n{request.waf_rules.get('cloudflare', '')}\n\n// Nginx Directive\n{request.waf_rules.get('nginx', '')}\n\n// Vercel Edge Middleware\n{request.waf_rules.get('vercel', '')}\n"
                z.writestr("waf-rules.txt", waf_text)

            # 6. Recommendations
            if request.recommendations:
                rec_lines = [f"# AEOForge Priority Recommendations for {domain}\n"]
                for i, r in enumerate(request.recommendations, 1):
                    rec_lines.append(f"## {i}. {r.get('title', '')} (+{r.get('score_boost', 0)} pts)")
                    rec_lines.append(f"{r.get('description', '')}\n")
                    if r.get('code_snippet'):
                        rec_lines.append(f"```\n{r.get('code_snippet')}\n```\n")
                z.writestr("RECOMMENDATIONS.md", "\n".join(rec_lines))

            # 7. Deployment README
            readme_text = f"""# AEO Handshake Deployment Package for {domain}
Generated by AEOForge (Autonomous Meta AI Agent-Readiness Studio)

## File Manifest:
- `llms.txt`: Place at the root of your public web server (e.g. `https://{domain}/llms.txt`).
- `agent-spec.json`: Place in your root or `.well-known/` directory (`https://{domain}/.well-known/agent-spec.json`).
- `schema.jsonld`: Embed inside your HTML `<head>` as a `<script type="application/ld+json">` tag.
- `waf-rules.txt`: Copy into your Cloudflare Dashboard (Security -> WAF -> Custom Rules) to allow Meta-ExternalAgent, PerplexityBot, and GPTBot.
- `RECOMMENDATIONS.md`: 5-6 prioritized implementation steps to maximize citability.
"""
            z.writestr("README-AEO-DEPLOY.md", readme_text)

        buf.seek(0)
        return Response(
            content=buf.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f'attachment; filename="aeoforge-{domain_safe}-bundle.zip"',
                "Content-Type": "application/zip"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export bundle failed: {str(e)}")


def diagnose_navigation_failure(error_msg: str, http_status: int, url: str) -> tuple[str, str, str]:
    """Diagnose crawl failure and return (category, technical_reason, actionable_remediation)."""
    err_low = (error_msg or "").lower()
    if http_status == 403 or "403" in err_low or "challenge" in err_low or "turnstile" in err_low or "bot" in err_low or "cloudflare" in err_low:
        return (
            "WAF_BOT_CHALLENGE",
            f"HTTP 403 Forbidden: Cloudflare Bot Fight Mode or WAF Challenge intercepted the crawler at {url}.",
            "Configure Cloudflare WAF Custom Rule to bypass bot challenges for user-agents Meta-ExternalAgent and PerplexityBot, or enable Stealth Chrome mode."
        )
    if http_status == 401 or "401" in err_low or "unauthorized" in err_low:
        return (
            "AUTH_REQUIRED",
            f"HTTP 401 Unauthorized: Endpoint at {url} requires HTTP Basic or Bearer Authentication.",
            "Provide authorization credentials or remove staging authentication wall for verified AI crawler bots."
        )
    if http_status == 404 or "404" in err_low:
        return (
            "ROUTE_NOT_FOUND",
            f"HTTP 404 Not Found: Discovered link {url} does not exist on origin server.",
            "Update broken internal navigation links or configure 301 redirects to active documentation."
        )
    if http_status == 429 or "429" in err_low or "too many requests" in err_low:
        return (
            "RATE_LIMITED",
            f"HTTP 429 Too Many Requests: Origin server throttled concurrent crawler requests at {url}.",
            "Increase origin rate limits or introduce request delay jitter."
        )
    if http_status >= 500:
        return (
            "SERVER_ERROR",
            f"HTTP {http_status} Server Error: Origin backend crashed or timed out at {url}.",
            "Check origin server application logs and gateway timeout thresholds."
        )
    if "err_name_not_resolved" in err_low or "nodename nor servname" in err_low or "getaddrinfo" in err_low:
        return (
            "DNS_FAILURE",
            f"DNS Resolution Failed: Hostname cannot be resolved via DNS for {url}.",
            "Verify domain spelling and confirm public DNS A/AAAA records are active."
        )
    if "err_connection_refused" in err_low or "connection refused" in err_low:
        return (
            "CONNECTION_REFUSED",
            f"Connection Refused: Target server at {url} actively rejected connection (port closed or firewall DROP).",
            "Verify server port is open and listening for incoming HTTP/HTTPS traffic."
        )
    if "timeout" in err_low or "timed out" in err_low:
        return (
            "TIMEOUT",
            f"Navigation Timed Out: Server at {url} failed to respond within 30 seconds.",
            "Check origin latency, disable heavy third-party tracking scripts, or increase crawler timeout."
        )
    if "err_cert" in err_low or "ssl" in err_low or "certificate" in err_low:
        return (
            "SSL_CERT_ERROR",
            f"SSL/TLS Certificate Error: Invalid or untrusted certificate at {url}.",
            "Renew or reconfigure the SSL/TLS certificate with a trusted Certificate Authority (e.g. Let's Encrypt)."
        )
    return (
        "NAVIGATION_ERROR",
        f"Navigation Obstacle: {error_msg} at {url}.",
        "Check origin connectivity and crawler user-agent permissions."
    )


@app.post("/api/v1/crawl")
async def crawl_endpoint(request: CrawlRequest):
    """Run BFS multi-page crawl with per-page diagnostics, partial insight tracking, and failure attribution."""
    from urllib.parse import urlparse, urljoin
    target_url = request.url.strip()
    if not target_url.startswith("http://") and not target_url.startswith("https://"):
        target_url = "https://" + target_url

    budget = max(1, min(request.max_pages, 1000))

    try:
        navigator = BrowserNavigator(headless=settings.playwright_headless, timeout_ms=30000)
        scorer = AEOScoringEngine()

        visited_urls = set()
        queue = [target_url]
        parsed_entry = urlparse(target_url)
        results = []
        failed_pages = []
        step = 0

        while queue and len(visited_urls) < budget:
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)
            step += 1

            try:
                # Capture screenshot for entry page or small budget crawls for instant perception rendering
                capture_ss = (step == 0) or (budget <= 5)
                nav_data = await navigator.inspect_url(current_url, capture_screenshot=capture_ss)

                # Check if navigation encountered a hard failure or block
                if nav_data.navigation_error or getattr(nav_data, "http_status", 200) >= 400:
                    status_code = getattr(nav_data, "http_status", 0)
                    err_text = nav_data.navigation_error or f"HTTP {status_code} Error"
                    cat, reason, fix = diagnose_navigation_failure(err_text, status_code, current_url)
                    failed_pages.append({
                        "url": current_url,
                        "step": step,
                        "category": cat,
                        "reason": reason,
                        "status_code": status_code,
                        "recommendation": fix
                    })
                    continue

                # Run scoring on successfully fetched page
                audit = await scorer.audit(
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
                audit.title = nav_data.title
                p = audit.pillars
                results.append({
                    "url": current_url,
                    "final_url": nav_data.final_url,
                    "title": nav_data.title or current_url,
                    "overall_score": audit.overall_score,
                    "grade": audit.grade,
                    "status": audit.status,
                    "citability": p.get("pillar_a_citability", {}).get("score", 0),
                    "navigability": p.get("pillar_b_navigability", {}).get("score", 0),
                    "protocols": p.get("pillar_c_protocols", {}).get("score", 0),
                    "structured_data": p.get("pillar_d_structured_data", {}).get("score", 0),
                    "blockers": audit.critical_blockers,
                    "token_ratio": nav_data.token_ratio,
                    "traps_count": len(nav_data.traps),
                    "top_deduction": f"-{audit.deductions[0]['points_lost']} pts: {audit.deductions[0]['title']}" if (audit.deductions and len(audit.deductions) > 0) else "None",
                    "screenshot_base64": nav_data.screenshot_base64,
                    "interactive_marks": nav_data.interactive_marks,
                    "traps": nav_data.traps,
                    "visual_analysis": audit.visual_analysis,
                    "deductions": audit.deductions,
                    "key_strengths": audit.key_strengths,
                    "critical_blockers": audit.critical_blockers,
                    "full_audit": audit.model_dump()
                })

                # Internal links discovery
                for m in nav_data.interactive_marks:
                    href = m.get("href")
                    if href and not href.startswith("#") and not href.startswith("mailto:") and not href.startswith("javascript:"):
                        full_url = urljoin(current_url, href)
                        parsed_link = urlparse(full_url)
                        if parsed_link.netloc == parsed_entry.netloc and full_url not in visited_urls and full_url not in queue:
                            queue.append(full_url)

            except Exception as e:
                cat, reason, fix = diagnose_navigation_failure(str(e), 0, current_url)
                failed_pages.append({
                    "url": current_url,
                    "step": step,
                    "category": cat,
                    "reason": reason,
                    "status_code": 0,
                    "recommendation": fix
                })

        # Calculate outcomes and cumulative insights
        crawled_count = len(results)
        failed_count = len(failed_pages)

        if crawled_count == 0:
            crawl_status = "failed"
            first_fail = failed_pages[0] if failed_pages else {
                "category": "INACCESSIBLE",
                "reason": "Could not establish initial connection to origin host",
                "recommendation": "Check target URL spelling, SSL certificate, and origin uptime."
            }
            termination_reason = f"Crawl failed on entry URL ({target_url}). {first_fail['reason']}"
            avg_score = 0.0
            grade, status = "F", "Inaccessible / Blocked"
        elif crawled_count >= budget:
            crawl_status = "completed"
            termination_reason = f"Full Budget Reached: Successfully crawled and audited all {crawled_count} of {budget} requested pages."
            avg_score = round(sum(r["overall_score"] for r in results) / crawled_count, 1)
            grade, status = calculate_grade(avg_score)
        elif failed_count > 0:
            crawl_status = "partial"
            last_fail = failed_pages[-1]
            pct = round((crawled_count / budget) * 100, 1)
            termination_reason = f"Partial Crawl: Audited {crawled_count} of {budget} requested pages ({pct}%). Crawl stopped on step #{last_fail['step']} ({last_fail['url']}) due to: {last_fail['reason']}"
            avg_score = round(sum(r["overall_score"] for r in results) / crawled_count, 1)
            grade, status = calculate_grade(avg_score)
        else:
            crawl_status = "completed"
            termination_reason = f"Queue Exhausted: Audited all {crawled_count} discoverable internal pages on domain without errors."
            avg_score = round(sum(r["overall_score"] for r in results) / crawled_count, 1)
            grade, status = calculate_grade(avg_score)

        # Cumulative 4-Pillar Insights up to that point
        avg_citability = round(sum(r.get("citability", 0) for r in results) / max(1, crawled_count), 1) if results else 0.0
        avg_navigability = round(sum(r.get("navigability", 0) for r in results) / max(1, crawled_count), 1) if results else 0.0
        avg_protocols = round(sum(r.get("protocols", 0) for r in results) / max(1, crawled_count), 1) if results else 0.0
        avg_structured = round(sum(r.get("structured_data", 0) for r in results) / max(1, crawled_count), 1) if results else 0.0

        all_blockers = []
        for r in results:
            for b in r.get("blockers", []):
                if b not in all_blockers:
                    all_blockers.append(b)

        return {
            "root_url": target_url,
            "crawl_status": crawl_status,
            "budget_requested": budget,
            "pages_crawled": crawled_count,
            "pages_failed": failed_count,
            "completion_pct": round((crawled_count / budget) * 100, 1) if budget > 0 else 0.0,
            "termination_reason": termination_reason,
            "sitewide_score": avg_score,
            "sitewide_grade": grade,
            "sitewide_status": status,
            "insights": {
                "avg_citability": avg_citability,
                "avg_navigability": avg_navigability,
                "avg_protocols": avg_protocols,
                "avg_structured_data": avg_structured,
                "total_blockers_detected": len(all_blockers),
                "blockers": all_blockers[:6],
                "active_queue_left": len(queue)
            },
            "pages": results,
            "failed_pages": failed_pages
        }
    except Exception as e:
        cat, reason, fix = diagnose_navigation_failure(str(e), 0, target_url)
        return {
            "root_url": target_url,
            "crawl_status": "failed",
            "budget_requested": budget,
            "pages_crawled": 0,
            "pages_failed": 1,
            "completion_pct": 0.0,
            "termination_reason": f"Crawl failed on entry URL ({target_url}). {reason}",
            "sitewide_score": 0.0,
            "sitewide_grade": "F",
            "sitewide_status": "Blocked / Inaccessible",
            "insights": {
                "avg_citability": 0.0,
                "avg_navigability": 0.0,
                "avg_protocols": 0.0,
                "avg_structured_data": 0.0,
                "total_blockers_detected": 1,
                "blockers": [reason],
                "active_queue_left": 0
            },
            "pages": [],
            "failed_pages": [{
                "url": target_url,
                "step": 1,
                "category": cat,
                "reason": reason,
                "status_code": 0,
                "recommendation": fix
            }]
        }


@app.post("/api/v1/audit-batch")
async def audit_batch_endpoint(request: BatchAuditRequest):
    """Audit a custom list of user-provided URLs concurrently and synthesize a comparative AEO score matrix."""
    if not request.urls:
        raise HTTPException(status_code=400, detail="URL list cannot be empty")

    clean_urls = []
    for u in request.urls:
        u_str = u.strip()
        if u_str:
            if not u_str.startswith("http://") and not u_str.startswith("https://"):
                u_str = "https://" + u_str
            if u_str not in clean_urls:
                clean_urls.append(u_str)

    clean_urls = clean_urls[:50]  # Cap concurrent batch at 50 URLs
    sem = asyncio.Semaphore(5)

    async def audit_single(target_url: str):
        async with sem:
            try:
                nav = BrowserNavigator(timeout_ms=25000)
                nav_data = await nav.inspect_url(target_url, capture_screenshot=request.capture_screenshot)
                scorer = AEOScoringEngine()
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
                audit.title = nav_data.title
                p = audit.pillars
                top_ded = audit.deductions[0] if (audit.deductions and len(audit.deductions) > 0) else None
                return {
                    "url": target_url,
                    "final_url": nav_data.final_url,
                    "title": nav_data.title or target_url,
                    "overall_score": audit.overall_score,
                    "grade": audit.grade,
                    "status": audit.status,
                    "citability": p.get("pillar_a_citability", {}).get("score", 0),
                    "navigability": p.get("pillar_b_navigability", {}).get("score", 0),
                    "protocols": p.get("pillar_c_protocols", {}).get("score", 0),
                    "structured_data": p.get("pillar_d_structured_data", {}).get("score", 0),
                    "traps_count": len(nav_data.traps),
                    "deductions_count": len(audit.deductions or []),
                    "top_deduction": f"-{top_ded['points_lost']} pts: {top_ded['title']}" if top_ded else "None",
                    "full_audit": audit.model_dump()
                }
            except Exception as e:
                return {
                    "url": target_url,
                    "error": str(e),
                    "overall_score": 0.0,
                    "grade": "F",
                    "status": "Failed"
                }

    results = await asyncio.gather(*(audit_single(u) for u in clean_urls))
    valid_results = [r for r in results if "error" not in r]
    avg_score = round(sum(r["overall_score"] for r in valid_results) / max(1, len(valid_results)), 1) if valid_results else 0.0
    grade, status = calculate_grade(avg_score)

    return {
        "count": len(results),
        "pages_audited": len(results),
        "valid_count": len(valid_results),
        "average_score": avg_score,
        "average_grade": grade,
        "sitewide_grade": grade,
        "average_status": status,
        "results": results,
        "pages": results
    }


@app.post("/api/v1/spec")
async def spec_endpoint(request: SpecRequest):
    """Generate agent-spec.json, llms.txt, and Schema.org JSON-LD for an agent."""
    try:
        navigator = BrowserNavigator(headless=settings.playwright_headless)
        scorer = AEOScoringEngine()

        nav_data = await navigator.inspect_url(request.url, capture_screenshot=False)
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
        llms_full_txt = generate_llms_full_txt(
            url=nav_data.final_url,
            title=nav_data.title,
            text_content=nav_data.text_content
        )
        schema = generate_schema_jsonld(
            url=nav_data.final_url,
            title=nav_data.title,
            description=nav_data.text_content[:150],
            html=nav_data.html
        )

        return {
            "url": nav_data.final_url,
            "aeo_score": audit.overall_score,
            "agent_spec": spec,
            "llms_txt": llms_txt,
            "llms_full_txt": llms_full_txt,
            "schema_jsonld": schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Spec generation failed: {str(e)}")


@app.post("/api/v1/patch")
async def patch_endpoint(request: PatchRequest):
    """Auto-patch local codebase with llms.txt, agent-spec.json, and Schema.org JSON-LD."""
    try:
        patcher = CodebasePatcher(request.target_dir)
        llms = request.llms_txt or f"# {request.url}\n> Autonomous AI directory generated by AEOForge.\n"
        spec = request.agent_spec or {"$schema": "https://aeoforge.dev/schemas/agent-spec-v1.json", "domain": request.url}
        schema = request.schema_jsonld or {"@context": "https://schema.org", "@type": "WebSite", "url": request.url}
        res = patcher.patch_all(llms, spec, schema)

        try:
            storage.log_patch(domain=request.url, target_dir=request.target_dir, patched_files=res)
        except Exception:
            pass

        return {
            "status": "success",
            "target_dir": request.target_dir,
            "patched_files": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch failed: {str(e)}")


@app.get("/api/v1/history")
async def get_history_endpoint(domain: Optional[str] = None, limit: int = 25):
    """Retrieve list of past audit summaries from persistent SQLite storage."""
    return storage.list_audits(domain=domain, limit=limit)


@app.get("/api/v1/history/{audit_id}")
async def get_history_detail_endpoint(audit_id: str):
    """Retrieve full audit snapshot by audit ID."""
    res = storage.get_audit(audit_id)
    if not res:
        raise HTTPException(status_code=404, detail="Audit record not found")
    return res


@app.delete("/api/v1/history/{audit_id}")
async def delete_history_endpoint(audit_id: str):
    """Delete single audit from persistent storage."""
    deleted = storage.delete_audit(audit_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Audit not found")
    return {"status": "deleted", "audit_id": audit_id}


@app.delete("/api/v1/history")
async def clear_history_endpoint():
    """Clear all historical audits from persistent storage."""
    count = storage.clear_history()
    return {"status": "cleared", "records_removed": count}


@app.get("/api/v1/progression/{domain:path}")
async def get_domain_progression_endpoint(domain: str):
    """Get progression timeline, score trajectory, and delta metrics for a domain."""
    parsed = urlparse(domain)
    clean_domain = parsed.netloc or parsed.path or domain
    if "://" in clean_domain:
        clean_domain = clean_domain.split("://")[-1]
    clean_domain = clean_domain.split("/")[0]
    return storage.get_domain_progression(clean_domain)


class SettingsPayload(BaseModel):
    settings: Dict[str, Any]


@app.get("/api/v1/settings")
async def get_settings_endpoint():
    """Get stored persistent user preferences & technical setup."""
    all_s = storage.get_all_settings()
    masked = {}
    for k, v in all_s.items():
        if "api_key" in k and isinstance(v, str) and len(v) > 8:
            masked[k] = v[:4] + "••••••••" + v[-4:]
        else:
            masked[k] = v
    return {"settings": masked}


@app.post("/api/v1/settings")
async def save_settings_endpoint(payload: SettingsPayload):
    """Save persistent user configurations and technical setup in SQLite."""
    for k, v in payload.settings.items():
        if isinstance(v, str) and "••••••••" in v:
            continue
        storage.set_setting(k, v)
    return {"status": "saved", "count": len(payload.settings)}


@app.post("/api/v1/deobfuscate-email")
async def deobfuscate_endpoint(request: DeobfuscateRequest):
    """Deobfuscate Cloudflare XOR tokens or HTML email mutations."""
    if request.cf_hex:
        email = deobfuscate_cloudflare_email(request.cf_hex)
        return {"decoded_email": email}
    elif request.html:
        emails = extract_obfuscated_emails(request.html)
        return {"extracted_emails": emails}
    else:
        raise HTTPException(status_code=400, detail="Must provide cf_hex or html")


# Mount static directory for frontend
STATIC_DIR = Path(__file__).parent / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    """Serve the AEOForge Single Page Application frontend."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>AEOForge Engine Running</h1>")
