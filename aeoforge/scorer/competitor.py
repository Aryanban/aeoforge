"""Head-to-Head AEO Competitor Analysis & Outranking Engine.
Audits target website and competitor website simultaneously, performs metric gap analysis,
and synthesizes a tactical AEO Outranking Blueprint.
"""

from typing import Dict, Any, List
from pydantic import BaseModel

from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.scorer.engine import AEOScoringEngine, AEOAuditResult


class MetricComparison(BaseModel):
    metric_name: str
    target_value: str
    competitor_value: str
    delta: str
    winner: str  # "target", "competitor", "tie"
    advantage_explanation: str


class CompetitorComparisonResult(BaseModel):
    target_url: str
    competitor_url: str
    target_score: float
    competitor_score: float
    score_delta: float
    target_grade: str
    competitor_grade: str
    winner_url: str
    metrics: List[MetricComparison]
    competitor_advantages: List[str]
    target_advantages: List[str]
    outranking_blueprint: List[str]


async def compare_competitors(
    target_url: str,
    competitor_url: str,
    headless: bool = True
) -> CompetitorComparisonResult:
    """Run dual headless audit and compute head-to-head outranking blueprint."""
    navigator = BrowserNavigator(headless=headless)
    scorer = AEOScoringEngine()

    # Audit Target
    t_nav = await navigator.inspect_url(target_url, capture_screenshot=False)
    t_audit = await scorer.audit(
        url=t_nav.final_url,
        html=t_nav.html,
        text_content=t_nav.text_content,
        raw_html_tokens=t_nav.raw_html_tokens,
        text_tokens=t_nav.text_tokens,
        traps=t_nav.traps,
        interactive_marks=t_nav.interactive_marks,
        a11y_tree=t_nav.a11y_tree
    )

    # Audit Competitor
    c_nav = await navigator.inspect_url(competitor_url, capture_screenshot=False)
    c_audit = await scorer.audit(
        url=c_nav.final_url,
        html=c_nav.html,
        text_content=c_nav.text_content,
        raw_html_tokens=c_nav.raw_html_tokens,
        text_tokens=c_nav.text_tokens,
        traps=c_nav.traps,
        interactive_marks=c_nav.interactive_marks,
        a11y_tree=c_nav.a11y_tree
    )

    # 1. Overall Score Comparison
    t_score = t_audit.overall_score
    c_score = c_audit.overall_score
    delta = round(t_score - c_score, 1)

    t_pa = t_audit.pillars["pillar_a_citability"]["details"]
    c_pa = c_audit.pillars["pillar_a_citability"]["details"]
    t_pb = t_audit.pillars["pillar_b_navigability"]["details"]
    c_pb = c_audit.pillars["pillar_b_navigability"]["details"]
    t_pc = t_audit.pillars["pillar_c_protocols"]["details"]
    c_pc = c_audit.pillars["pillar_c_protocols"]["details"]
    t_pd = t_audit.pillars["pillar_d_structured_data"]["details"]
    c_pd = c_audit.pillars["pillar_d_structured_data"]["details"]

    metrics = []

    # Metric: Fact Density
    t_fd = t_pa.get("fact_density_pct", 0)
    c_fd = c_pa.get("fact_density_pct", 0)
    metrics.append(MetricComparison(
        metric_name="Fact Triplet Density",
        target_value=f"{t_fd}%",
        competitor_value=f"{c_fd}%",
        delta=f"{round(t_fd - c_fd, 1)}%",
        winner="target" if t_fd > c_fd else ("competitor" if c_fd > t_fd else "tie"),
        advantage_explanation="Higher fact density yields direct citation capsules in Answer Engines."
    ))

    # Metric: Direct Answer Capsule
    t_cap = t_pa.get("has_answer_capsule", False)
    c_cap = c_pa.get("has_answer_capsule", False)
    metrics.append(MetricComparison(
        metric_name="Direct Answer Capsule",
        target_value="Present" if t_cap else "Missing",
        competitor_value="Present" if c_cap else "Missing",
        delta="Equal" if t_cap == c_cap else ("Advantage Target" if t_cap else "Advantage Competitor"),
        winner="target" if t_cap and not c_cap else ("competitor" if c_cap and not t_cap else "tie"),
        advantage_explanation="Direct answer capsules under H2s are extracted verbatim by Perplexity and Meta AI."
    ))

    # Metric: Token Efficiency
    t_tr = t_pb.get("token_ratio_pct", 0)
    c_tr = c_pb.get("token_ratio_pct", 0)
    metrics.append(MetricComparison(
        metric_name="Text-to-DOM Token Ratio",
        target_value=f"{t_tr}%",
        competitor_value=f"{c_tr}%",
        delta=f"{round(t_tr - c_tr, 1)}%",
        winner="target" if t_tr > c_tr else ("competitor" if c_tr > t_tr else "tie"),
        advantage_explanation="Leaner DOM consumes less LLM context window and reduces agent token cost."
    ))

    # Metric: /llms.txt Protocol
    t_llms = t_pc.get("has_llms_txt", False)
    c_llms = c_pc.get("has_llms_txt", False)
    metrics.append(MetricComparison(
        metric_name="/llms.txt Agent Directory",
        target_value="Present" if t_llms else "Missing",
        competitor_value="Present" if c_llms else "Missing",
        delta="Equal" if t_llms == c_llms else ("Advantage Target" if t_llms else "Advantage Competitor"),
        winner="target" if t_llms and not c_llms else ("competitor" if c_llms and not t_llms else "tie"),
        advantage_explanation="Provides an unauthenticated, zero-bloat markdown directory for autonomous crawlers."
    ))

    # Metric: Structured Schemas
    t_sc = len(t_pd.get("schema_types", []))
    c_sc = len(c_pd.get("schema_types", []))
    metrics.append(MetricComparison(
        metric_name="Schema.org Entity Types",
        target_value=f"{t_sc} types",
        competitor_value=f"{c_sc} types",
        delta=f"{t_sc - c_sc:+d}",
        winner="target" if t_sc > c_sc else ("competitor" if c_sc > t_sc else "tie"),
        advantage_explanation="Explicit entity relationships disambiguate brand mentions in knowledge graphs."
    ))

    # Extract Advantages
    c_adv = []
    t_adv = []

    if c_score > t_score:
        if c_llms and not t_llms:
            c_adv.append("Competitor has published an /llms.txt file, giving them 80% faster discovery by AI agents.")
        if c_cap and not t_cap:
            c_adv.append("Competitor includes direct answer capsules (35-65 words), making them the default answer snippet.")
        if c_fd > t_fd + 15:
            c_adv.append(f"Competitor has {c_fd}% fact density vs your {t_fd}%, ranking higher on semantic factual depth.")
        if c_sc > t_sc:
            c_adv.append(f"Competitor implements {c_sc} Schema.org types ({', '.join(c_pd.get('schema_types', []))}), whereas you have {t_sc}.")
    else:
        t_adv.append("Your site has superior overall agent accessibility and legibility.")
        if t_tr > c_tr:
            t_adv.append(f"Your site has a leaner DOM structure ({t_tr}% vs {c_tr}% text-to-DOM ratio).")

    # Generate Tactical Outranking Blueprint
    blueprint = []
    if not t_llms and c_llms:
        blueprint.append("Immediate Gap: Deploy /llms.txt using AEOForge to neutralize competitor's protocol advantage (+12 pts).")
    elif not t_llms:
        blueprint.append("First-Mover Edge: Neither site has /llms.txt. Publish yours first to capture AI crawler preference (+12 pts).")

    if not t_cap:
        blueprint.append("Snippet Takeover: Inject 35-65 word factual definition capsules directly below your H2 tags. Answer engines will switch their citation capsule to your domain.")

    if t_sc < c_sc or t_sc == 0:
        blueprint.append(f"Entity Graph Defense: Inject Schema.org JSON-LD (WebSite, FAQPage, Organization). Match or exceed competitor's {c_sc} schemas.")

    if t_tr < c_tr:
        blueprint.append("DOM Pruning: Reduce heavy wrapper elements and client-side hydration wrappers to improve text-to-token efficiency.")

    if not blueprint:
        blueprint.append("Maintain Current Lead: Keep /llms.txt fresh and verify new content conforms to direct answer capsule guidelines.")

    return CompetitorComparisonResult(
        target_url=target_url,
        competitor_url=competitor_url,
        target_score=t_score,
        competitor_score=c_score,
        score_delta=delta,
        target_grade=t_audit.grade,
        competitor_grade=c_audit.grade,
        winner_url=target_url if t_score >= c_score else competitor_url,
        metrics=metrics,
        competitor_advantages=c_adv or ["None detected. Target website has parity or superior metrics."],
        target_advantages=t_adv or ["Competitor leads in machine protocols and direct answer formatting."],
        outranking_blueprint=blueprint
    )
