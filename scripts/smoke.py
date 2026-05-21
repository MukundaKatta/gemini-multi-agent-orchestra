"""Real Vertex AI smoke test for gemini-multi-agent-orchestra.

Runs the 3-agent supervisor (researcher → analyst → writer) end-to-end
through Gemini 2.5 Flash on the Bright Data MCP stub and verifies:

  - the writer emits all 4 labeled sections
    (ANSWER / EVIDENCE / SCORING / HANDOFF TRACE)
  - the HANDOFF TRACE names all 3 sub-agents (researcher, analyst, writer)
  - at least one verbatim quote from a scraped page made it through
  - the canned coding-agent URLs are cited (anthropic / openai / google)

Usage:
    GOOGLE_CLOUD_PROJECT=careersavvy-mukunda \\
    GOOGLE_GENAI_USE_VERTEXAI=true \\
    GOOGLE_CLOUD_LOCATION=us-central1 \\
    .venv/bin/python scripts/smoke.py
"""
from __future__ import annotations

import os
import sys

os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "careersavvy-mukunda")
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", "true")
os.environ.setdefault("GOOGLE_CLOUD_LOCATION", "us-central1")

from gemini_multi_agent_orchestra.runner import ask  # noqa: E402


QUESTION = (
    "Rank the top 3 AI coding agents launched in May 2026 by adoption "
    "and cite their announcement URLs verbatim. Walk the orchestra: "
    "researcher searches and scrapes, analyst scores each source, "
    "writer composes the final 4-section report."
)


# At least one of these verbatim quotes from the scraped pages must
# survive the researcher → analyst → writer handoff into the final
# EVIDENCE section.
VERBATIM_FRAGMENTS = [
    "480,000 weekly active developers",
    "310,000 weekly active developers",
    "215,000 weekly active developers",
]


def main() -> int:
    print("== gemini-multi-agent-orchestra smoke ==")
    print(f"project={os.environ.get('GOOGLE_CLOUD_PROJECT')}")
    print(f"location={os.environ.get('GOOGLE_CLOUD_LOCATION')}")
    print(f"vertexai={os.environ.get('GOOGLE_GENAI_USE_VERTEXAI')}")
    print()
    print(f"> {QUESTION}")
    print()

    resp = ask(QUESTION, stub=True)
    print("--- FINAL TEXT (writer) ---")
    print(resp.final_text or "(no final text)")
    print("--- END FINAL TEXT ---")
    print(f"events: {len(resp.events)}")
    print(f"sub-agents seen: {sorted(resp.by_author.keys())}")

    text  = resp.final_text or ""
    upper = text.upper()
    handoff_section = ""
    if "HANDOFF TRACE" in upper:
        handoff_section = text[upper.index("HANDOFF TRACE"):]

    checks = {
        "has ANSWER section":          "ANSWER" in upper,
        "has EVIDENCE section":        "EVIDENCE" in upper,
        "has SCORING section":         "SCORING" in upper,
        "has HANDOFF TRACE section":   "HANDOFF TRACE" in upper,
        "HANDOFF TRACE names researcher":
            "researcher" in handoff_section.lower(),
        "HANDOFF TRACE names analyst":
            "analyst" in handoff_section.lower(),
        "HANDOFF TRACE names writer":
            "writer" in handoff_section.lower(),
        "at least one verbatim adoption quote survives":
            any(frag in text for frag in VERBATIM_FRAGMENTS),
        "cites anthropic.com URL":     "anthropic.com" in text.lower(),
        "cites openai.com URL":        "openai.com" in text.lower(),
        "cites developers.google.com URL":
            "developers.google.com" in text.lower(),
    }
    print()
    print("--- CHECKS ---")
    for label, ok in checks.items():
        print(f"  [{'PASS' if ok else 'FAIL'}] {label}")
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
