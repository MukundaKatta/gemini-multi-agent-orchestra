# gemini-multi-agent-orchestra

A 3-agent supervisor pattern built on **Google Cloud Agent Builder
(ADK)**, **Gemini 2.5**, and the **Bright Data MCP server**. Submission
for the **DoraHacks Agents Without Masters** hackathon ($25K, Jun 16
2026) — explicitly themed around autonomous multi-agent systems.

## The pattern

A `SequentialAgent` ("orchestra_supervisor") delegates to three
`LlmAgent` sub-agents that hand off through ADK session state via
`output_key`:

```
orchestra_supervisor (SequentialAgent)
├── researcher  → search_engine + scrape_page  → writes `research_notes`
├── analyst     → score_source                 → writes `scoring_log`
└── writer      → (no tools)                   → composes final report
```

Each sub-agent has its own system prompt and its own job. Handoffs are
verbatim — quotes the researcher scrapes survive byte-for-byte through
the analyst and into the writer's final EVIDENCE section.

## The story chain

Ask `"Rank the top 3 AI coding agents launched in May 2026 by adoption
and cite their announcement URLs verbatim"` and the orchestra:

1. **researcher** runs `search_engine(...)` → 5 SERP results, picks the
   top 3 first-party announcement pages, runs `scrape_page(url)` on
   each, dumps verbatim text to `research_notes`.
2. **analyst** reads `research_notes`, calls `score_source(url, score,
   reason)` 3 times — `reason` quotes the verbatim adoption number from
   the scraped page (480k / 310k / 215k weekly active developers).
3. **writer** reads `research_notes` + `scoring_log`, composes the
   final report:

```
ANSWER:        ranked list of the 3 coding agents (highest adoption first)
EVIDENCE:      verbatim quotes from each scraped page, tagged with URL
SCORING:       analyst's score + reason per source
HANDOFF TRACE: which agent did what
```

## Tool surface (Bright Data MCP-shaped)

- `search_engine(query, engine)` — SERP API
- `scrape_page(url)` — Web Unlocker, returns verbatim `text_excerpt`
- `score_source(url, score, reason)` — analyst's ranking tool (returns
  the full ranked log so the writer can read it back in one call)
- `web_data_lookup(dataset, key)` — structured-dataset lookup

The stub is one env-var away from a real Bright Data account
(`BRIGHTDATA_API_TOKEN` + `npx @brightdata/mcp`) with no agent-code
change.

## Architecture

```
┌──────────────────────┐    ┌──────────────────────────────────────────┐   ┌────────────────────────────┐
│ Streamlit dashboard  │──▶ │  orchestra_supervisor (SequentialAgent)   │──▶│  Bright Data MCP server     │
│ on Cloud Run         │    │                                            │   │  (stub for demos,           │
│                      │    │  researcher  →  analyst  →  writer         │   │   real account via          │
│ "rank the top 3 ..." │    │  Gemini 2.5 Flash on Vertex AI             │   │   BRIGHTDATA_API_TOKEN)     │
└──────────────────────┘    └──────────────────────────────────────────┘   └────────────────────────────┘
```

## Try it locally

```sh
uv venv
uv pip install -e ".[dev]"
pytest -q
GOOGLE_CLOUD_PROJECT=careersavvy-mukunda \
  GOOGLE_GENAI_USE_VERTEXAI=true \
  GOOGLE_CLOUD_LOCATION=us-central1 \
  .venv/bin/python scripts/smoke.py
```

Streamlit dashboard:

```sh
streamlit run app/dashboard.py
```

## Try it against a real Bright Data account

```sh
export BRIGHTDATA_API_TOKEN="brd_..."
streamlit run app/dashboard.py
```

Untick "Use stub Bright Data MCP" in the sidebar. The agents now spawn
the official `@brightdata/mcp` server via `npx`.

## Tests

```sh
uv pip install -e ".[dev]"
pytest -q
```

The suite pins the orchestra's contract: the SERP returns 5 results
with the top 3 vendor announcements, each scrape contains the verbatim
adoption number the analyst cites, `score_source` clamps and ranks
correctly, and the top-level `test_supervisor_chain_is_consistent`
walks the full SERP → scrape → score chain in one shot.

## License

Apache 2.0. Standalone repo created for the DoraHacks Agents Without
Masters hackathon (target deadline Jun 16 2026).
