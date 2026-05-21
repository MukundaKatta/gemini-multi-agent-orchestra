# lablab.ai submission package — gemini-multi-agent-orchestra

Pre-filled fields for the **Web Data UNLOCKED Hackathon** (Bright Data),
ready to paste into the lablab submission form once the application is
approved and the submission portal opens on **May 25 2026 10:00 AM PDT**
(deadline May 29 2026 5:00 PM PDT).

Event: https://lablab.ai/ai-hackathons/brightdata-ai-agents-web-data-hackathon

## 📋 Basic Information

**Project Title**

    gemini-multi-agent-orchestra

**Short Description** (one sentence)

    A Gemini 2.5 research analyst that walks Bright Data's MCP tools (SERP +
    Web Unlocker + structured datasets) to answer plain-English research
    questions with verbatim quotes and a confidence note.

**Long Description**

    gemini-multi-agent-orchestra treats every research question as a SERP → unlock →
    cite loop. Ask "Anthropic Claude latest release notes 2026" and the agent
    walks the Bright Data MCP tools:

    1. search_engine(query, engine) — pulls the top SERP results.
    2. Pick the most authoritative source (prefer first-party).
    3. scrape_page(url) — fetch the rendered page through the Web Unlocker
       (anti-bot bypass, returns unlocked_by_brightdata: true).
    4. extract_text(url, css_selector) — clean text for citation.
    5. web_data_lookup(dataset, key) — if the question touches a structured
       record (company / profile / product), pull the canonical dataset row.

    The agent answers in 5 labeled sections:

      ANSWER:     one or two sentences, every number/date/version copied
                  verbatim from a tool result.
      SOURCES:    bulleted list of the URLs the agent actually consulted.
      KEY QUOTES: 2–4 verbatim quotes pulled from the scraped pages, each
                  tagged with the source URL.
      CONFIDENCE: high / medium / low, with a one-sentence reason tied to
                  source quality and cross-source agreement.
      NEXT STEP:  one concrete follow-up search.

    Strict rule: every quantitative claim must come from a tool result. The
    agent cites byte-for-byte; it never paraphrases inside KEY QUOTES, and
    flags any page where unlocked_by_brightdata is false as a confidence
    downgrade.

    Built on Google Cloud Agent Builder (ADK) with Gemini 2.5 Flash on
    Vertex AI, wired to Bright Data's MCP server. The repo ships a local
    stub (canned SERPs + scraped pages, no Bright Data account required)
    plus a one-env-var swap to the real @brightdata/mcp server.

**Technology & Category Tags**

    python, gemini, gemini-2-5, vertex-ai, google-cloud-agent-builder,
    agent-development-kit, mcp, model-context-protocol, bright-data,
    bright-data-mcp, web-unlocker, serp-api, structured-datasets,
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
