"""Stub Bright Data MCP server with a scoring tool layered on top.

Mirrors the Bright Data MCP shape (`search_engine`, `scrape_page`,
`web_data_lookup`) plus a scoring tool the analyst sub-agent uses
(`score_source`) to rank scraped pages by adoption signal.

The canned story chain is "Top 3 AI coding agents launched in May 2026":
  1. `search_engine("Top 3 AI coding agents launched in May 2026")`
     returns 5 SERP results.
  2. `scrape_page(url)` on the top 3 returns full text with verbatim
     adoption-quotes for each.
  3. `score_source(url, score, reason)` records analyst-side rankings.
  4. `web_data_lookup` is the canonical structured-record fallback.

Returns canned, deterministic responses so judges can reproduce the demo
without provisioning a Bright Data account. Real Bright Data MCP swap is
one env-var change (BRIGHTDATA_API_TOKEN) — the agent code is unchanged.

Run with: python -m gemini_multi_agent_orchestra.mcp_stub

Submission: DoraHacks · Agents Without Masters ($25K, Jun 16)
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


NOW = datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Canned SERP + scrape + dataset data
# ---------------------------------------------------------------------------


# Story chain query: "Top 3 AI coding agents launched in May 2026"
_SERPS: dict[str, list[dict[str, Any]]] = {
    "Top 3 AI coding agents launched in May 2026": [
        {
            "rank":    1,
            "title":   "Introducing Claude Code 2.0 — Anthropic",
            "url":     "https://www.anthropic.com/news/claude-code-2-may-2026",
            "snippet": "Claude Code 2.0 shipped on 2026-05-06 with the new "
                       "multi-agent orchestrator, 1M-token context, and a "
                       "VS Code extension. 480,000 weekly active developers "
                       "in the first 7 days.",
            "domain":  "anthropic.com",
            "fetched_at": NOW.isoformat(),
        },
        {
            "rank":    2,
            "title":   "Codex 3 launches with self-repair loops — OpenAI",
            "url":     "https://openai.com/index/codex-3-launch-may-2026",
            "snippet": "OpenAI's Codex 3 launched 2026-05-12. Adds parallel "
                       "tool execution and a 'critic' sub-agent that audits "
                       "every diff before commit. 310,000 weekly active "
                       "developers across the JetBrains and VS Code plugins.",
            "domain":  "openai.com",
            "fetched_at": NOW.isoformat(),
        },
        {
            "rank":    3,
            "title":   "Gemini Code Assist Agent goes GA — Google Developers",
            "url":     "https://developers.google.com/blog/gemini-code-assist-agent-ga-may-2026",
            "snippet": "Google's Gemini Code Assist Agent reached GA on "
                       "2026-05-19 with full IDE-resident multi-step task "
                       "execution. 215,000 weekly active developers in the "
                       "Workspace + Cloud Code preview.",
            "domain":  "developers.google.com",
            "fetched_at": NOW.isoformat(),
        },
        {
            "rank":    4,
            "title":   "May 2026 AI coding agent roundup — Latent Space",
            "url":     "https://www.latent.space/p/may-2026-coding-agent-roundup",
            "snippet": "Independent recap of the May 2026 coding-agent wave: "
                       "Claude Code 2.0, OpenAI Codex 3, Gemini Code Assist "
                       "Agent, Cursor Composer 4, and Cline 5. Adoption "
                       "numbers and benchmark deltas inside.",
            "domain":  "latent.space",
            "fetched_at": NOW.isoformat(),
        },
        {
            "rank":    5,
            "title":   "Best AI coding agents shipped this month — Hacker News digest",
            "url":     "https://news.ycombinator.com/digest/may-2026-coding-agents",
            "snippet": "Community-curated digest ranking the 10 most-discussed "
                       "AI coding agents launched in May 2026. Anthropic, "
                       "OpenAI, and Google take the top three slots by points.",
            "domain":  "news.ycombinator.com",
            "fetched_at": NOW.isoformat(),
        },
    ],
}


# Full-text scrapes for the top 3 SERP results — analyst pulls verbatim
# adoption numbers + ship dates from these.
_SCRAPED_PAGES: dict[str, dict[str, Any]] = {
    "https://www.anthropic.com/news/claude-code-2-may-2026": {
        "url":     "https://www.anthropic.com/news/claude-code-2-may-2026",
        "title":   "Introducing Claude Code 2.0",
        "status":  200,
        "rendered_chars": 6120,
        "text_excerpt": (
            "We're shipping Claude Code 2.0 today, 2026-05-06. The release "
            "ships with a built-in multi-agent orchestrator that lets a "
            "supervisor agent delegate to a fleet of researcher, planner, "
            "and executor sub-agents. Context expands to 1M tokens across "
            "the orchestra. A new official VS Code extension ships at GA. "
            "In the first 7 days post-launch we measured 480,000 weekly "
            "active developers, the highest weekly cohort we've ever shipped "
            "with on a launch week."
        ),
        "fetched_at": NOW.isoformat(),
        "unlocked_by_brightdata": True,
    },
    "https://openai.com/index/codex-3-launch-may-2026": {
        "url":     "https://openai.com/index/codex-3-launch-may-2026",
        "title":   "Codex 3: self-repair loops for production code",
        "status":  200,
        "rendered_chars": 5482,
        "text_excerpt": (
            "OpenAI Codex 3 launched on 2026-05-12 across the JetBrains and "
            "VS Code plugins. The headline feature is a 'critic' sub-agent "
            "that audits every diff before it lands. Codex 3 also runs tool "
            "calls in parallel, cutting median task latency by 38% vs Codex "
            "2.5. Adoption: 310,000 weekly active developers in the first "
            "week after launch."
        ),
        "fetched_at": NOW.isoformat(),
        "unlocked_by_brightdata": True,
    },
    "https://developers.google.com/blog/gemini-code-assist-agent-ga-may-2026": {
        "url":     "https://developers.google.com/blog/gemini-code-assist-agent-ga-may-2026",
        "title":   "Gemini Code Assist Agent — generally available",
        "status":  200,
        "rendered_chars": 4910,
        "text_excerpt": (
            "Today, 2026-05-19, Gemini Code Assist Agent reaches general "
            "availability. The agent runs inside the IDE and executes "
            "multi-step coding tasks end-to-end — read the repo, draft a "
            "plan, edit files, run tests, and report. Across the Workspace "
            "+ Cloud Code preview we count 215,000 weekly active developers "
            "this week."
        ),
        "fetched_at": NOW.isoformat(),
        "unlocked_by_brightdata": True,
    },
}


# Structured-dataset fallback (mirrors Bright Data's web_data_lookup shape).
_DATASETS: dict[str, list[dict[str, Any]]] = {
    "coding_agent:claude-code-2": [
        {
            "name":            "Claude Code 2.0",
            "vendor":          "Anthropic",
            "launched_on":     "2026-05-06",
            "weekly_active":   480_000,
            "supports_ides":   ["VS Code", "JetBrains", "Neovim", "Terminal"],
            "url":             "https://www.anthropic.com/news/claude-code-2-may-2026",
            "fetched_at":      NOW.isoformat(),
        },
    ],
    "coding_agent:codex-3": [
        {
            "name":            "Codex 3",
            "vendor":          "OpenAI",
            "launched_on":     "2026-05-12",
            "weekly_active":   310_000,
            "supports_ides":   ["VS Code", "JetBrains"],
            "url":             "https://openai.com/index/codex-3-launch-may-2026",
            "fetched_at":      NOW.isoformat(),
        },
    ],
    "coding_agent:gemini-code-assist": [
        {
            "name":            "Gemini Code Assist Agent",
            "vendor":          "Google",
            "launched_on":     "2026-05-19",
            "weekly_active":   215_000,
            "supports_ides":   ["VS Code", "JetBrains", "Cloud Code"],
            "url":             "https://developers.google.com/blog/gemini-code-assist-agent-ga-may-2026",
            "fetched_at":      NOW.isoformat(),
        },
    ],
}


# In-memory scoring log. The analyst sub-agent calls `score_source` once
# per scraped page; the writer reads back the full log so its final
# SCORING section is grounded in real tool calls (not hallucinated).
_SCORES: list[dict[str, Any]] = []


# ---------------------------------------------------------------------------
# Response builders
# ---------------------------------------------------------------------------


def search_engine_response(query: str, engine: str = "google") -> dict[str, Any]:
    results = _SERPS.get(query, [])
    if not results:
        # Loose match: any query mentioning "AI coding agents" + "May 2026"
        # routes to the canned top-3 SERP. Saves the agent from having to
        # guess the exact canonical phrasing.
        lower = query.lower()
        if (("coding" in lower or "code" in lower)
                and "agent" in lower
                and "may" in lower
                and "2026" in lower):
            results = _SERPS["Top 3 AI coding agents launched in May 2026"]
    if not results:
        # Soft fallback so the agent can still reason about unknown queries.
        results = [{
            "rank":    1,
            "title":   f"(stub) no canned SERP for {query!r}",
            "url":     "",
            "snippet": "Bright Data stub: this query has no canned results. "
                       "In production the real Bright Data SERP API would "
                       "return live results from the chosen engine.",
            "domain":  "stub",
            "fetched_at": NOW.isoformat(),
        }]
    return {
        "query":        query,
        "engine":       engine,
        "result_count": len(results),
        "results":      results,
    }


def scrape_page_response(url: str) -> dict[str, Any]:
    rec = _SCRAPED_PAGES.get(url)
    if rec is None:
        return {
            "url":    url,
            "status": 200,
            "rendered_chars": 0,
            "text_excerpt": (
                f"(stub) no canned scrape for {url}. In production the real "
                "Bright Data Web Unlocker would return the rendered page "
                "text after bypassing any anti-bot defences."
            ),
            "unlocked_by_brightdata": True,
            "fetched_at": NOW.isoformat(),
        }
    return rec


def score_source_response(url: str, score: float, reason: str) -> dict[str, Any]:
    """Record an analyst-side score for a scraped source.

    Returns the full ranked log so downstream agents can read it back in
    one call (no hidden state). Scores are clamped to [0, 10].
    """
    clamped = max(0.0, min(10.0, float(score)))
    entry = {
        "url":      url,
        "score":    clamped,
        "reason":   reason,
        "ranked_at": NOW.isoformat(),
    }
    _SCORES.append(entry)
    # Stable rank: highest score first, ties broken by call order.
    ranked = sorted(_SCORES, key=lambda e: -e["score"])
    return {
        "recorded":   entry,
        "rank_log":   ranked,
        "log_size":   len(_SCORES),
    }


def web_data_lookup_response(dataset: str, key: str) -> dict[str, Any]:
    lookup_key = f"{dataset}:{key}"
    rec = _DATASETS.get(lookup_key)
    if rec is None:
        return {"error": f"unknown dataset entry {lookup_key!r}",
                "known": list(_DATASETS.keys())}
    return {"dataset": dataset, "key": key, "records": rec, "count": len(rec)}


def _reset_scores_for_tests() -> None:
    """Test helper — clear the in-memory scoring log between tests."""
    _SCORES.clear()


# ---------------------------------------------------------------------------
# MCP server wiring
# ---------------------------------------------------------------------------


def _make_server() -> Server:
    server = Server("bright-data-stub")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(name="search_engine",
                 description=("Run a SERP query through Bright Data's SERP API. "
                              "Returns the top results with rank, title, url, "
                              "snippet, and domain. Engine defaults to google."),
                 inputSchema={"type": "object",
                              "properties": {
                                  "query":  {"type": "string"},
                                  "engine": {"type": "string",
                                              "enum": ["google", "bing", "duckduckgo"],
                                              "default": "google"},
                              },
                              "required": ["query"]}),
            Tool(name="scrape_page",
                 description=("Fetch a URL through Bright Data's Web Unlocker. "
                              "Returns the rendered HTML + a text excerpt + "
                              "the anti-bot status. Use this for verbatim "
                              "quotes — text_excerpt is byte-accurate."),
                 inputSchema={"type": "object",
                              "properties": {"url": {"type": "string"}},
                              "required": ["url"]}),
            Tool(name="score_source",
                 description=("Record an analyst score (0-10) for a scraped "
                              "source, with a one-sentence reason. Returns "
                              "the full ranked log so downstream agents can "
                              "read back the ranking in one call."),
                 inputSchema={"type": "object",
                              "properties": {
                                  "url":    {"type": "string"},
                                  "score":  {"type": "number"},
                                  "reason": {"type": "string"},
                              },
                              "required": ["url", "score", "reason"]}),
            Tool(name="web_data_lookup",
                 description=("Look up a structured record from Bright Data's "
                              "web datasets (coding_agent, linkedin_company, "
                              "etc.). Returns canonical fields with verbatim "
                              "values."),
                 inputSchema={"type": "object",
                              "properties": {
                                  "dataset": {"type": "string"},
                                  "key":     {"type": "string"},
                              },
                              "required": ["dataset", "key"]}),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        a = arguments
        if name == "search_engine":
            payload = search_engine_response(a.get("query", ""),
                                              a.get("engine", "google"))
        elif name == "scrape_page":
            payload = scrape_page_response(a.get("url", ""))
        elif name == "score_source":
            payload = score_source_response(a.get("url", ""),
                                            a.get("score", 0),
                                            a.get("reason", ""))
        elif name == "web_data_lookup":
            payload = web_data_lookup_response(a.get("dataset", ""),
                                                a.get("key", ""))
        else:
            payload = {"error": f"unknown tool {name!r}"}
        return [TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]

    return server


async def _main() -> None:
    server = _make_server()
    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
