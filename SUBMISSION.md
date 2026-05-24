# Submission package — gemini-multi-agent-orchestra

**Primary target:** DoraHacks Agents Without Masters (deadline Jun 16 2026, $25K)
**Cross-submission candidate:** lablab.ai Web Data UNLOCKED (May 29 2026) if multi-entry rules allow

The body of this file is written for either platform — both ask for
the same project description, tags, repo URL, and demo. The "submission
timeline" section at the bottom lists both deadlines.

Event URLs:
  - DoraHacks: https://dorahacks.io/hackathon/agents-without-masters
  - lablab.ai: https://lablab.ai/ai-hackathons/brightdata-ai-agents-web-data-hackathon

## 📋 Basic Information

**Project Title**

    gemini-multi-agent-orchestra

**Short Description** (one sentence)

    A 3-agent supervisor pattern (researcher + analyst + writer) over the
    Bright Data MCP server, built on Google Cloud Agent Builder ADK and
    Gemini 2.5. Primary target: DoraHacks Agents Without Masters; eligible
    as a Bright Data cross-submission if multi-entry is allowed.

**Long Description**

    A SequentialAgent supervisor ("orchestra_supervisor") delegates to
    three LlmAgent sub-agents that hand off state through ADK's
    output_key:

        orchestra_supervisor (SequentialAgent)
        ├── researcher   → search_engine + scrape_page → writes research_notes
        ├── analyst      → score_source                → writes scoring_log
        └── writer       → (no tools)                  → composes final report

    Each sub-agent has its own system prompt and its own job. Hand-offs
    are verbatim: quotes the researcher scrapes survive byte-for-byte
    through the analyst and into the writer's final EVIDENCE section.

    Ask "Rank the top 3 AI coding agents launched in May 2026 by adoption
    and cite their announcement URLs verbatim" and the orchestra:

    1. researcher runs search_engine() → 5 SERP results, picks the top 3
       first-party announcement pages, runs scrape_page(url) on each,
       writes verbatim text to research_notes.
    2. analyst reads research_notes, calls score_source(url, score,
       reason) 3 times — reason quotes the verbatim adoption number from
       the scraped page (480k / 310k / 215k weekly active developers).
    3. writer reads research_notes plus scoring_log, composes the final
       report:

         ANSWER:        ranked list of the 3 coding agents.
         EVIDENCE:      verbatim quotes from each scraped page, tagged
                        with URL.
         SCORING:       analyst's score plus reason per source.
         HANDOFF TRACE: which sub-agent did what.

    Why this fits Agents Without Masters: no central planner picks the
    next step. The SequentialAgent shape encodes the workflow; each
    sub-agent is autonomous within its lane and the hand-off is by state,
    not by orchestrator interrupt. The orchestra is a working pattern
    other teams can lift directly.

    Tool surface is Bright Data MCP-shaped (same as the official
    @brightdata/mcp npm package), so the same orchestra runs against the
    real Bright Data account with one env-var swap (BRIGHTDATA_API_TOKEN).
    The repo ships a local stub for demos with no account required.

    Built on Google Cloud Agent Builder (ADK), Gemini 2.5 Flash on Vertex
    AI, and the Bright Data MCP server. Apache 2.0.

**Technology & Category Tags**

    python, gemini, gemini-2-5, vertex-ai, google-cloud-agent-builder,
    agent-development-kit, sequential-agent, multi-agent, supervisor,
    mcp, model-context-protocol, bright-data, bright-data-mcp,
    web-unlocker, serp-api, autonomous-agents, agents-without-masters,
    streamlit, google-cloud-run, apache-2

## 📸 Cover Image and Presentation

**Cover Image**

    /Users/ubl/gemini-multi-agent-orchestra/.video-build/cover.png
    (1200x675, 42.5 KB, PNG)

**Video Presentation**

    https://youtu.be/OjcFb89eloY
    (1m51s — intro slide + ~32s real Cloud Run footage + outro slide,
     unlisted, hosted on YouTube)

**Slide Presentation**

    Skipped — the demo video carries the same content.

## 💻 App Hosting & Code Repository

**Public GitHub Repository**

    https://github.com/MukundaKatta/gemini-multi-agent-orchestra

**Demo Application Platform**

    Google Cloud Run (us-central1)

**Application URL**

    https://gemini-multi-agent-orchestra-1029931682737.us-central1.run.app

## ✅ Bright Data Requirement Check

> Bright Data Requirement: Your submission must demonstrably use at least
> one Bright Data product.

The agent's MCP tool surface is a 1:1 match for the official
`@brightdata/mcp` npm package and uses four Bright Data products:

  - SERP API           — `search_engine(query, engine)`
  - Web Unlocker       — `scrape_page(url)` (returns `unlocked_by_brightdata: true`)
  - extract / scrape   — `extract_text(url, css_selector)` for clean text
  - Structured Datasets — `web_data_lookup(dataset, key)` (LinkedIn companies, etc.)

The demo video shows all four firing through the deployed Streamlit
dashboard, with `unlocked_by_brightdata: true` printed in the event trace
on the verbatim Claude 4.7 release-notes scrape.

## ⏱️ Submission timeline

  - **2026-05-18** — repo + Cloud Run + YouTube + cover all built (today)
  - **2026-05-XX** — lablab moderator approves application (currently
                     "Waiting for approval")
  - **2026-05-25 10:00 AM PDT** — submission portal opens
  - **2026-05-29 05:00 PM PDT** — submission deadline
  - **2026-05-30** — onsite Build Day (SF, The Web Data Loft)
  - **2026-05-31** — Demos & Awards (online + onsite)
