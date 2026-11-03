"""FastAPI Application Server for AEOForge."""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Query
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


class CrawlRequest(BaseModel):
    url: str
    max_pages: int = 3


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


@app.post("/api/v1/crawl")
async def crawl_endpoint(request: CrawlRequest):
    """Run BFS multi-page crawl and audit sitewide AEO."""
    from urllib.parse import urlparse, urljoin
    try:
        navigator = BrowserNavigator(headless=settings.playwright_headless)
        scorer = AEOScoringEngine()

        visited_urls = set()
        queue = [request.url]
        parsed_entry = urlparse(request.url)
        results = []

        while queue and len(visited_urls) < min(request.max_pages, 10):
            current_url = queue.pop(0)
            if current_url in visited_urls:
                continue
            visited_urls.add(current_url)

            nav_data = await navigator.inspect_url(current_url, capture_screenshot=False)
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
            results.append({
                "url": current_url,
                "title": nav_data.title,
                "overall_score": audit.overall_score,
                "grade": audit.grade,
                "status": audit.status,
                "blockers": audit.critical_blockers,
                "token_ratio": nav_data.token_ratio
            })

            # Internal links discovery
            for m in nav_data.interactive_marks:
                href = m.get("href")
                if href and not href.startswith("#") and not href.startswith("mailto:"):
                    full_url = urljoin(current_url, href)
                    if urlparse(full_url).netloc == parsed_entry.netloc and full_url not in visited_urls:
                        queue.append(full_url)

        avg_score = round(sum(r["overall_score"] for r in results) / max(1, len(results)), 1)
        grade, status = calculate_grade(avg_score)

        return {
            "root_url": request.url,
            "pages_crawled": len(results),
            "sitewide_score": avg_score,
            "sitewide_grade": grade,
            "sitewide_status": status,
            "pages": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


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
        return {
            "status": "success",
            "target_dir": request.target_dir,
            "patched_files": res
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Patch failed: {str(e)}")


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
