"""Benchmark suite for AEOForge metrics.
Runs quantized measurements across all core dimensions and computes reward/penalty scores.
"""

import asyncio
import time
import json
import statistics
from bs4 import BeautifulSoup
from aeoforge.navigator.browser import BrowserNavigator
from aeoforge.navigator.som_grounding import extract_interactive_marks, build_a11y_tree_representation
from aeoforge.scorer.citability import score_citability
from aeoforge.scorer.navigability import score_navigability
from aeoforge.scorer.protocols import score_protocols
from aeoforge.scorer.api_discovery import score_api_and_data
from aeoforge.spec.spec_generator import generate_agent_spec
from aeoforge.spec.llmstxt_gen import generate_llms_txt

SAMPLE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dholera Smart City - High Speed Industrial Hub</title>
    <script src="https://google-analytics.com/analytics.js"></script>
    <script>console.log("analytics tracking");</script>
    <style>body { font-family: sans-serif; } .hero { height: 400px; }</style>
</head>
<body>
    <header>
        <nav role="navigation">
            <a href="/" class="nav-item">Home</a>
            <a href="/projects" class="nav-item">Projects</a>
            <a href="/pricing" class="nav-item">Pricing Plans</a>
            <a href="/contact" class="nav-item">Contact Us</a>
            <button onclick="openModal()" aria-label="Book Site Visit">Book Visit</button>
        </nav>
    </header>
    <main role="main">
        <h1>Dholera Special Investment Region (SIR)</h1>
        <p>
            Dholera Smart City is India's first greenfield industrial smart city located in Gujarat, spanning over 920 square kilometers of planned industrial and residential zones. It provides world-class plug-and-play infrastructure for global manufacturers, semiconductor fabrication units, and solar energy generation plants.
        </p>
        <h2>Infrastructure & Connectivity</h2>
        <p>
            The Ahmedabad-Dholera Expressway is a 109-kilometer four-lane access-controlled highway that connects Ahmedabad to Dholera SIR within 60 minutes. The project includes an international cargo airport, dedicated freight corridors, and a multi-modal logistics hub designed for next-generation manufacturing operations.
        </p>
        <section>
            <h3>Investment Highlights</h3>
            <ul>
                <li>Total planned area is 920 sq km.</li>
                <li>Dholera International Airport enables direct global air cargo.</li>
                <li>Expressway completion provides high-speed expressway connectivity.</li>
            </ul>
        </section>
        <form action="/search" method="GET">
            <label for="q">Search plots</label>
            <input type="text" id="q" name="q" placeholder="Search industrial zones..." />
            <button type="submit">Search</button>
        </form>
    </main>
    <div id="cookieModal" class="modal-overlay fixed inset-0 bg-black/50" style="display:none;">
        <div class="modal-content">
            <p>We use cookies to improve your experience.</p>
            <button class="accept-cookie-btn" onclick="this.parentElement.parentElement.style.display='none'">Accept All</button>
        </div>
    </div>
    <footer>
        <p>&copy; 2026 Dholera Smart City. All rights reserved.</p>
    </footer>
</body>
</html>
"""

async def run_benchmarks():
    print("=" * 60)
    print("AEOFORGE QUANTIZED METRICS BENCHMARK SUITE")
    print("=" * 60)

    results = {}

    # 1. Token Context Reduction Benchmark
    soup = BeautifulSoup(SAMPLE_HTML, "html.parser")
    raw_html_tokens = len(SAMPLE_HTML) // 4
    
    # Measure spec generator tokens
    marks = [
        {"id": 1, "role": "link", "name": "Pricing Plans", "href": "/pricing", "rect": {"x": 10, "y": 20, "width": 80, "height": 30}},
        {"id": 2, "role": "button", "name": "Book Site Visit", "href": None, "rect": {"x": 100, "y": 20, "width": 100, "height": 30}},
        {"id": 3, "role": "input", "name": "Search industrial zones...", "href": None, "rect": {"x": 50, "y": 200, "width": 200, "height": 35}},
    ]
    spec = generate_agent_spec(
        url="https://dholeramap.com",
        aeo_score=85.0,
        html=SAMPLE_HTML,
        traps=[],
        interactive_marks=marks,
        discovered_endpoints=["/api/v1/plots"]
    )
    spec_json = json.dumps(spec)
    spec_tokens = len(spec_json) // 4
    reduction_pct = ((raw_html_tokens - spec_tokens) / raw_html_tokens) * 100

    llms_txt = generate_llms_txt("https://dholeramap.com", "Dholera Smart City", "Dholera Smart City is India's first greenfield industrial smart city.", marks)
    llms_txt_tokens = len(llms_txt) // 4

    results["tokens"] = {
        "raw_html_tokens": raw_html_tokens,
        "agent_spec_tokens": spec_tokens,
        "llms_txt_tokens": llms_txt_tokens,
        "reduction_pct": round(reduction_pct, 2)
    }
    print(f"\n[Metric 1: Token Context]")
    print(f"Raw HTML Tokens: {raw_html_tokens}")
    print(f"Agent-Spec Tokens: {spec_tokens} ({round(reduction_pct, 1)}% reduction)")
    print(f"llms.txt Tokens: {llms_txt_tokens}")

    # 2. Citability & Fact-Triplet Extraction Benchmark
    clean_text = soup.get_text(separator=" ", strip=True)
    t0 = time.perf_counter()
    cit_score = score_citability(SAMPLE_HTML, clean_text)
    cit_latency_ms = (time.perf_counter() - t0) * 1000

    results["citability"] = {
        "score": cit_score["score"],
        "fact_density_pct": cit_score["details"]["fact_density_pct"],
        "has_answer_capsule": cit_score["details"]["has_answer_capsule"],
        "latency_ms": round(cit_latency_ms, 3)
    }
    print(f"\n[Metric 2: Citability & Fact Density]")
    print(f"Score: {cit_score['score']}/25.0")
    print(f"Fact Density: {cit_score['details']['fact_density_pct']}%")
    print(f"Has Answer Capsule: {cit_score['details']['has_answer_capsule']}")
    print(f"Extraction Latency: {round(cit_latency_ms, 3)}ms")

    # 3. Live Headless Navigation & Route Interception Speed
    print(f"\n[Metric 3: Live Navigation Latency]")
    navigator = BrowserNavigator(headless=True, timeout_ms=15000)
    
    # We test on localhost FastAPI instance to measure pure navigation & parsing latency without network jitter
    t_start = time.perf_counter()
    page_data = await navigator.inspect_url("http://127.0.0.1:8000/", capture_screenshot=False)
    nav_duration = time.perf_counter() - t_start

    results["navigation"] = {
        "duration_seconds": round(nav_duration, 3),
        "dom_elements": page_data.dom_element_count,
        "interactive_marks_count": len(page_data.interactive_marks),
        "traps_detected": len(page_data.traps)
    }
    print(f"Navigation + Parsing Duration: {round(nav_duration, 3)}s")
    print(f"DOM Elements: {page_data.dom_element_count}")
    print(f"Interactive Marks: {len(page_data.interactive_marks)}")
    print(f"Traps Detected: {len(page_data.traps)}")

    return results

if __name__ == "__main__":
    asyncio.run(run_benchmarks())
