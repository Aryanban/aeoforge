"""Meta AI & Llama Stack client for Llama 3.2 Vision and text reasoning models."""

import json
import logging
from typing import Dict, Any, Optional
import httpx

from aeoforge.config import settings
from aeoforge.models.prompts import META_VISION_AUDIT_SYSTEM_PROMPT, META_CITABILITY_SYSTEM_PROMPT

logger = logging.getLogger("aeoforge.models")


class MetaAIClient:
    """Client for Meta Model API, Local Ollama, and Llama Stack orchestrator."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        api_base: Optional[str] = None,
        llama_stack_endpoint: Optional[str] = None,
        ollama_endpoint: Optional[str] = None,
        ollama_model: Optional[str] = None
    ):
        self.api_key = api_key or settings.meta_model_api_key
        self.model_name = model_name or settings.meta_model_name
        self.api_base = api_base or settings.meta_model_api_base
        self.llama_stack_endpoint = llama_stack_endpoint or settings.llama_stack_endpoint
        self.ollama_endpoint = ollama_endpoint or settings.ollama_endpoint
        self.ollama_model = ollama_model or settings.ollama_model_name

    async def _resolve_ollama_model(self) -> tuple[Optional[str], bool]:
        """Resolve available Ollama model and whether it supports vision."""
        # shortcut: fast 1.5s discovery of local models; fallback to settings name if offline
        try:
            async with httpx.AsyncClient(timeout=1.5) as client:
                res = await client.get(f"{self.ollama_endpoint}/api/tags")
                if res.status_code != 200:
                    return None, False
                models = res.json().get("models", [])
                if not models:
                    return None, False

                # Exact or prefix match with configured model
                for m in models:
                    name = m.get("name", "")
                    if name == self.ollama_model or name.startswith(self.ollama_model.split(":")[0]):
                        caps = m.get("capabilities", [])
                        has_vision = "vision" in caps or "vision" in name.lower()
                        return name, has_vision

                # Fallback to any installed Llama model
                llama_models = [m for m in models if "llama" in m.get("name", "").lower()]
                target = llama_models[0] if llama_models else models[0]
                name = target.get("name", "")
                caps = target.get("capabilities", [])
                has_vision = "vision" in caps or "vision" in name.lower()
                return name, has_vision
        except Exception:
            return None, False

    async def _check_ollama_available(self) -> bool:
        """Check if local Ollama server is running."""
        model, _ = await self._resolve_ollama_model()
        return model is not None

    async def analyze_visual_navigation(
        self,
        screenshot_base64: Optional[str],
        a11y_tree: str,
        traps: list
    ) -> Dict[str, Any]:
        """Perform multimodal visual audit using Meta Model API, Local Ollama, or heuristic fallback."""
        # Path 1: Cloud Meta Model API
        if self.api_key and screenshot_base64:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                messages = [
                    {"role": "system", "content": META_VISION_AUDIT_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Evaluate this webpage screenshot with Set-of-Mark tags.\nAccessibility Tree:\n{a11y_tree[:2000]}"
                            },
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{screenshot_base64}"}
                            }
                        ]
                    }
                ]
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json={
                            "model": self.model_name,
                            "messages": messages,
                            "temperature": 0.1,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        content = data["choices"][0]["message"]["content"]
                        return json.loads(content)
            except Exception as e:
                logger.warning(f"Meta Model API call failed: {e}")

        # Path 2: 100% Local Ollama (Meta Llama 3.2 on-device)
        if settings.use_ollama:
            resolved_model, has_vision = await self._resolve_ollama_model()
            if resolved_model:
                try:
                    user_msg: Dict[str, Any] = {
                        "role": "user",
                        "content": f"Evaluate this webpage screenshot and accessibility tree with Set-of-Mark tags:\nAccessibility Tree:\n{a11y_tree[:2500]}"
                    }
                    if has_vision and screenshot_base64:
                        user_msg["images"] = [screenshot_base64]

                    async with httpx.AsyncClient(timeout=45.0) as client:
                        resp = await client.post(
                            f"{self.ollama_endpoint}/api/chat",
                            json={
                                "model": resolved_model,
                                "messages": [
                                    {"role": "system", "content": META_VISION_AUDIT_SYSTEM_PROMPT},
                                    user_msg
                                ],
                                "format": "json",
                                "stream": False
                            }
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("message", {}).get("content", "{}")
                            parsed = json.loads(content)
                            if "visual_navigability_score" in parsed:
                                return parsed
                except Exception as e:
                    logger.warning(f"Local Ollama vision/nav call failed: {e}")

        # Path 3: Local deterministic heuristic fallback
        score = 85
        blockers = []
        for t in traps:
            blockers.append(f"{t['name']} detected at selector: {t['active_selector']}")
            score -= 15 if t["severity"] == "critical" else 8

        score = max(20, min(100, score))
        return {
            "visual_navigability_score": score,
            "identified_visual_blockers": blockers or ["None detected. Clean layout."],
            "element_grounding_accuracy": 92 if not traps else 75,
            "agent_navigation_advice": (
                "Bypass modal overlays before primary action." if traps
                else "Use direct accessibility tree nodes for element interaction."
            )
        }

    async def analyze_citability(self, text_sample: str) -> Dict[str, Any]:
        """Analyze text sample for AEO citation potential."""
        # Cloud Meta Model API
        if self.api_key:
            try:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                messages = [
                    {"role": "system", "content": META_CITABILITY_SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this text:\n\n{text_sample[:3000]}"}
                ]
                async with httpx.AsyncClient(timeout=20.0) as client:
                    resp = await client.post(
                        f"{self.api_base}/chat/completions",
                        headers=headers,
                        json={
                            "model": self.model_name,
                            "messages": messages,
                            "temperature": 0.1,
                            "response_format": {"type": "json_object"}
                        }
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        return json.loads(data["choices"][0]["message"]["content"])
            except Exception:
                pass

        # Local Ollama
        if settings.use_ollama:
            resolved_model, _ = await self._resolve_ollama_model()
            if resolved_model:
                try:
                    async with httpx.AsyncClient(timeout=30.0) as client:
                        resp = await client.post(
                            f"{self.ollama_endpoint}/api/chat",
                            json={
                                "model": resolved_model,
                                "messages": [
                                    {"role": "system", "content": META_CITABILITY_SYSTEM_PROMPT},
                                    {"role": "user", "content": f"Analyze this text:\n\n{text_sample[:3000]}"}
                                ],
                                "format": "json",
                                "stream": False
                            }
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            content = data.get("message", {}).get("content", "{}")
                            parsed = json.loads(content)
                            if "citability_score" in parsed:
                                return parsed
                except Exception:
                    pass

        # Heuristic calculation
        import re
        sentences = [s.strip() for s in re.split(r'[.!?]+', text_sample) if len(s.strip()) > 15]
        fact_triplet_count = sum(1 for s in sentences if any(w in s.lower() for w in [" is ", " are ", " was ", " provides ", " allows ", " includes "]))
        
        has_capsule = any(30 <= len(s.split()) <= 65 for s in sentences)
        score = min(100, max(30, int((fact_triplet_count / max(1, len(sentences))) * 100)))

        return {
            "citability_score": score,
            "fact_triplet_count": fact_triplet_count,
            "has_direct_answer_capsule": has_capsule,
            "recommended_aeo_snippet": sentences[0] if sentences else "Clear definition snippet required."
        }
