"""3-agent supervisor orchestrating researcher + analyst + writer on
Google Cloud Agent Builder (ADK).

Pattern: `SequentialAgent` ("orchestra_supervisor") wraps three
`LlmAgent` sub-agents that hand off through ADK session state via
`output_key`:

  researcher  → gathers verbatim quotes via search_engine + scrape_page
                (writes `research_notes`).
  analyst     → reads `research_notes`, scores each scraped source via
                score_source (writes `scoring_log`).
  writer      → reads both, composes the final 4-section report
                (ANSWER / EVIDENCE / SCORING / HANDOFF TRACE).

Bright Data MCP server is the stub by default; a real Bright Data
account swaps in via `BRIGHTDATA_API_TOKEN` with no agent-code change.
"""

from __future__ import annotations

import os
import sys
from typing import Any


try:
    from google.adk.agents import LlmAgent, SequentialAgent
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
    from mcp import StdioServerParameters
    _ADK_AVAILABLE = True
except ImportError:  # pragma: no cover
    _ADK_AVAILABLE = False


# ---------------------------------------------------------------------------
# Sub-agent prompts
# ---------------------------------------------------------------------------


RESEARCHER_PROMPT = """\
You are the RESEARCHER sub-agent in a 3-agent orchestra. Your job is to
gather verbatim source material; you do NOT score and you do NOT write
the final answer.

Workflow (do every step, in order):

1. Call `search_engine` with a query that captures the user's question.
   The query MUST include the phrase "AI coding agents" and the words
   "May 2026" so the SERP returns canonical announcement pages. A good
   query is literally `"Top 3 AI coding agents launched in May 2026"`.
2. From the SERP, pick the top 3 results (rank 1, 2, 3). They will be
   first-party vendor announcement pages.
3. For each pick, call `scrape_page(url)` to fetch the full text. The
   `text_excerpt` field is byte-accurate — keep it verbatim.
4. Stop after 3 scrapes. Do NOT score; the analyst handles that.
5. NEVER invent URLs. Only quote text that came back from a real
   `scrape_page` call. If the SERP looks empty, retry once with the
   exact query `"Top 3 AI coding agents launched in May 2026"`.

Output EXACTLY this structure (plain text, no markdown headers):

RESEARCH NOTES (researcher)
SERP QUERY: <the query you sent>
PICKED:
  - <url 1>
  - <url 2>
  - <url 3>
VERBATIM EXCERPTS:
  [url 1]
  <full text_excerpt copied byte-for-byte from scrape_page>

  [url 2]
  <full text_excerpt copied byte-for-byte from scrape_page>

  [url 3]
  <full text_excerpt copied byte-for-byte from scrape_page>

HANDOFF: analyst, please score these 3 sources by adoption signal.

Strict rules:
- Quotes MUST be copied byte-for-byte from `scrape_page` tool output.
- Do NOT invent URLs. Only use URLs that came back from `search_engine`.
- Do NOT call `score_source` or `web_data_lookup`. Those belong to the
  analyst.
"""


ANALYST_PROMPT = """\
You are the ANALYST sub-agent in a 3-agent orchestra. The researcher's
notes (with 3 picked URLs + verbatim excerpts) are in session state as
`research_notes`. Your job is to score the 3 sources.

Workflow:

1. Read `research_notes` from session state. It contains 3 URLs with
   verbatim excerpts.
2. For each URL, extract the adoption signal from the excerpt (e.g.
   "weekly active developers", launch date, IDE coverage).
3. For each URL, call `score_source(url, score, reason)` with:
   - `score` in [0, 10], higher = stronger adoption / authority.
   - `reason` ≤ 20 words, cites the verbatim number you used.
4. Optionally call `web_data_lookup("coding_agent", "<slug>")` for
   canonical adoption rows (slugs: claude-code-2, codex-3,
   gemini-code-assist) — only if the excerpt is ambiguous.

Output EXACTLY this structure:

SCORING (analyst)
For each URL, one line:
  <url>  →  score=<0-10>  ·  <reason citing verbatim number>

RANKED LOG (from score_source):
<paste the `rank_log` array returned by your last score_source call,
one line per entry: <rank>. <url>  score=<n>  reason=<text>>

HANDOFF: writer, please compose the final 4-section report.

Strict rules:
- Call `score_source` exactly 3 times (once per researcher pick).
- Do NOT scrape new URLs. Use only the URLs already in `research_notes`.
- The reason MUST quote a verbatim number from the researcher's excerpt.
"""


WRITER_PROMPT = """\
You are the WRITER sub-agent in a 3-agent orchestra. The researcher's
notes are in session state as `research_notes`. The analyst's scoring
log is in session state as `scoring_log`. Your job is to compose the
final user-facing report.

Workflow:

1. Read both `research_notes` and `scoring_log`.
2. Rank the 3 sources by the analyst's score (highest first).
3. Compose the final report in EXACTLY this 4-section format. Use the
   labels verbatim — judges and tests grep for them.

Output EXACTLY this structure (no markdown, plain labeled sections):

ANSWER:
1. <vendor + product name> — <one-line summary with verbatim launch date>
2. <vendor + product name> — <one-line summary with verbatim launch date>
3. <vendor + product name> — <one-line summary with verbatim launch date>

EVIDENCE:
[<url 1>]
"<verbatim quote from research_notes, copied byte-for-byte>"

[<url 2>]
"<verbatim quote from research_notes, copied byte-for-byte>"

[<url 3>]
"<verbatim quote from research_notes, copied byte-for-byte>"

SCORING:
<url 1>  →  score=<n>  ·  <analyst reason>
<url 2>  →  score=<n>  ·  <analyst reason>
<url 3>  →  score=<n>  ·  <analyst reason>

HANDOFF TRACE:
researcher → gathered verbatim quotes from 3 URLs via search_engine + scrape_page
analyst    → scored each URL via score_source with adoption-cited reasons
writer     → composed this ranked report (you)

Strict rules:
- ANSWER is exactly 3 ranked bullets, ordered by analyst score (highest first).
- EVIDENCE quotes MUST be copied byte-for-byte from `research_notes`.
  No paraphrasing. No invented quotes.
- SCORING numbers MUST match the analyst's `scoring_log` exactly.
- HANDOFF TRACE MUST name all three sub-agents (researcher / analyst /
  writer) on its own lines.
- Do NOT call any tools. All required data is already in session state.
"""


# ---------------------------------------------------------------------------
# Tool wiring
# ---------------------------------------------------------------------------


def _bright_data_toolset(stub: bool = True) -> Any:
    if not _ADK_AVAILABLE:
        raise ImportError(
            "google-adk and mcp must be installed: pip install google-adk mcp"
        )

    if stub:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "gemini_multi_agent_orchestra.mcp_stub"],
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
    else:
        # Real Bright Data MCP server.
        params = StdioServerParameters(
            command="npx",
            args=["-y", "@brightdata/mcp"],
            env={
                **os.environ,
                "BRIGHTDATA_API_TOKEN": os.environ.get("BRIGHTDATA_API_TOKEN", ""),
            },
        )
    return McpToolset(connection_params=StdioConnectionParams(server_params=params))


# ---------------------------------------------------------------------------
# Sub-agent builders
# ---------------------------------------------------------------------------


def _build_researcher(model: str, stub: bool) -> Any:
    return LlmAgent(
        model=model,
        name="researcher",
        description="Gathers verbatim quotes from the top 3 SERP results via Bright Data.",
        instruction=RESEARCHER_PROMPT,
        tools=[_bright_data_toolset(stub=stub)],
        # The researcher's full output becomes session state under this key,
        # so the analyst and writer can read it back in one shot.
        output_key="research_notes",
    )


def _build_analyst(model: str, stub: bool) -> Any:
    return LlmAgent(
        model=model,
        name="analyst",
        description="Scores each researched source by adoption signal.",
        instruction=ANALYST_PROMPT,
        tools=[_bright_data_toolset(stub=stub)],
        output_key="scoring_log",
    )


def _build_writer(model: str) -> Any:
    # Writer has no tools — all data flows in via session state.
    return LlmAgent(
        model=model,
        name="writer",
        description="Composes the final 4-section ranked report.",
        instruction=WRITER_PROMPT,
        tools=[],
        output_key="final_report",
    )


def build_agent(model: str = "gemini-2.5-flash", stub: bool = True) -> Any:
    """Build the 3-agent supervisor.

    Returns a `SequentialAgent` that runs researcher → analyst → writer
    in order, with handoffs via ADK session state (`output_key`).
    """
    if not _ADK_AVAILABLE:
        return None
    researcher = _build_researcher(model=model, stub=stub)
    analyst    = _build_analyst(model=model, stub=stub)
    writer     = _build_writer(model=model)
    return SequentialAgent(
        name="orchestra_supervisor",
        description=("3-agent supervisor: researcher gathers verbatim "
                     "quotes, analyst scores them, writer composes the "
                     "ranked report. Handoffs via session state."),
        sub_agents=[researcher, analyst, writer],
    )
