"""Master 4-Pillar AEO & Agent-Readiness Scoring Engine (0 - 100 Points)."""

from typing import Dict, Any, List
from pydantic import BaseModel

from aeoforge.scorer.citability import score_citability
from aeoforge.scorer.navigability import score_navigability
from aeoforge.scorer.protocols import score_protocols
from aeoforge.scorer.api_discovery import score_api_and_data
from aeoforge.models.meta_client import MetaAIClient


class AEOAuditResult(BaseModel):
    url: str
    overall_score: float
    grade: str
    status: str
    pillars: Dict[str, Any]
    visual_analysis: Dict[str, Any]
    key_strengths: List[str]
    critical_blockers: List[str]
    action_plan: List[str]


def calculate_grade(score: float) -> tuple[str, str]:
    if score >= 90:
        return "A+", "Agent-Native (Fully optimized for AI agents & answer engines)"
    elif score >= 80:
        return "A", "Highly Ready (Strong machine legibility and citation signals)"
    elif score >= 70:
        return "B", "Moderately Ready (Minor navigation friction and missing protocols)"
    elif score >= 50:
        return "C", "Needs Optimization (Significant agent obstacles and token bloat)"
    else:
        return "F", "Agent-Inaccessible (Severe blocker traps and zero structured discovery)"


class AEOScoringEngine:
    """Master evaluator combining all 4 pillars with Meta AI reasoning."""

    def __init__(self):
        self.meta_client = MetaAIClient()

    async def audit(
        self,
        url: str,
        html: str,
        text_content: str,
        raw_html_tokens: int,
        text_tokens: int,
        traps: list,
        interactive_marks: list,
        a11y_tree: str,
        screenshot_b64: str = None
    ) -> AEOAuditResult:
        """Run complete 4-pillar audit plus Meta Llama 3.2 Vision evaluation."""
        # 1. Evaluate Pillar A (Citability)
        p_a = score_citability(html, text_content)

        # 2. Evaluate Pillar B (Navigability)
        p_b = score_navigability(html, raw_html_tokens, text_tokens, traps, interactive_marks)

        # 3. Evaluate Pillar C (Protocols)
        p_c = await score_protocols(url)

        # 4. Evaluate Pillar D (API & Data)
        p_d = score_api_and_data(html)

        # 5. Meta AI Vision analysis
        visual_analysis = await self.meta_client.analyze_visual_navigation(
            screenshot_base64=screenshot_b64,
            a11y_tree=a11y_tree,
            traps=traps
        )

        total_score = round(p_a["score"] + p_b["score"] + p_c["score"] + p_d["score"], 1)
        grade, status = calculate_grade(total_score)

        # Extract strengths and blockers
        strengths = []
        blockers = []
        action_plan = []

        all_feedback = p_a["feedback"] + p_b["feedback"] + p_c["feedback"] + p_d["feedback"]
        for fb in all_feedback:
            if any(pos in fb.lower() for pos in ["detected", "excellent", "high", "valid", "strong"]):
                strengths.append(fb)
            elif any(neg in fb.lower() for neg in ["missing", "blocker", "poor", "heavy", "disallows", "weak"]):
                blockers.append(fb)

        # Prioritize actionable remediation steps
        if not p_c["details"]["has_llms_txt"]:
            action_plan.append("Generate and publish an /llms.txt file at domain root using `aeoforge spec`.")
        if traps:
            action_plan.append(f"Resolve {len(traps)} navigation trap(s): implement automated dismissal or remove full-page blocker modals.")
        if not p_d["details"]["schema_types"]:
            action_plan.append("Inject Schema.org JSON-LD (WebSite, Organization, FAQPage) to enable entity citation.")
        if not p_a["details"]["has_answer_capsule"]:
            action_plan.append("Add concise (35-65 word) factual definition capsules directly beneath H2/H3 headings.")

        return AEOAuditResult(
            url=url,
            overall_score=total_score,
            grade=grade,
            status=status,
            pillars={
                "pillar_a_citability": p_a,
                "pillar_b_navigability": p_b,
                "pillar_c_protocols": p_c,
                "pillar_d_structured_data": p_d
            },
            visual_analysis=visual_analysis,
            key_strengths=strengths[:5],
            critical_blockers=blockers[:5],
            action_plan=action_plan or ["Maintain current high-grade agent accessibility."]
        )
