"""Spec package for AEOForge."""
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt, generate_llms_full_txt
from aeoforge.spec.schema_gen import generate_schema_jsonld

__all__ = [
    "generate_agent_spec",
    "generate_llms_txt",
    "generate_llms_full_txt",
    "generate_schema_jsonld"
]
