"""FastAPI Application Server for AEOForge."""

from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from aeoforge import __version__
from aeoforge.config import settings
from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.scorer.engine import AEOScoringEngine, AEOAuditResult
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt, generate_llms_full_txt
from aeoforge.spec.schema_gen import generate_schema_jsonld
from aeoforge.utils.deobfuscator import extract_obfuscated_emails, deobfuscate_cloudflare_email

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
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit failed: {str(e)}")


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
