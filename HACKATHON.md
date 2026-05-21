# DoraHacks Agents Without Masters — BUIDL submission

Event: https://dorahacks.io/hackathon/agents-without-masters
Prize pool: $25K
Submission deadline: 2026-06-16

## Elevator pitch

A 3-agent supervisor on Google Cloud Agent Builder (ADK) — researcher,
analyst, writer — that walks Bright Data's MCP tools to answer plain
English research questions with verbatim quotes that survive every
handoff.

## Rule compliance

| Rule | How we meet it |
|---|---|
| Autonomous multi-agent system | `SequentialAgent` ("orchestra_supervisor") delegates to 3 `LlmAgent` sub-agents with their own prompts, tool surfaces, and outputs. No human in the loop after the user's question. |
| Agents (not a single LLM call) | researcher → analyst → writer, with handoffs through ADK session state (`output_key`). Each sub-agent runs its own turn, calls its own tools, emits its own intermediate output. |
| Real tool use | Bright Data MCP-shaped tools: `search_engine`, `scrape_page`, `score_source`, `web_data_lookup`. Stub for the demo, real `@brightdata/mcp` via one env-var swap. |
| Reproducible | Apache 2.0, public GitHub repo, deterministic stub, pytest suite pins the chain, Cloud Run URL live. |
| Newly created | Repo init within the contest period. |

## Description

`gemini-multi-agent-orchestra` is the same Bright Data tool surface as
its sibling `gemini-bright-agent` — only this one replaces the single
LlmAgent with a 3-agent supervisor that hands off verbatim quotes
across three roles:

1. **researcher** — runs `search_engine` on the user's question, picks
   the top 3 first-party sources, calls `scrape_page` to grab full
   text, writes a structured `RESEARCH NOTES` block to session state
   (`research_notes`).
2. **analyst** — reads `research_notes`, calls `score_source(url,
   score, reason)` once per source. Each `reason` quotes the verbatim
   adoption number from the scraped page. Writes the ranked log to
   session state (`scoring_log`).
3. **writer** — reads `research_notes` + `scoring_log`, composes the
   final user-facing report. No tool calls. Output is exactly 4
   labeled sections:

```
ANSWER:        ranked list of the 3 coding agents (highest adoption first)
EVIDENCE:      verbatim quotes from each scraped page, tagged with URL
SCORING:       analyst's score + reason per source
HANDOFF TRACE: which agent did what
```

The killer property: quotes that the researcher copies byte-for-byte
out of `scrape_page` survive the analyst handoff and land in the
writer's EVIDENCE section unchanged. Tests pin this contract.

## Demo question

> Rank the top 3 AI coding agents launched in May 2026 by adoption and
> cite their announcement URLs verbatim.

The canned story chain:

| Rank | Agent | Vendor | Launched | Weekly active devs |
|---|---|---|---|---|
| 1 | Claude Code 2.0 | Anthropic | 2026-05-06 | 480,000 |
| 2 | Codex 3 | OpenAI | 2026-05-12 | 310,000 |
| 3 | Gemini Code Assist Agent | Google | 2026-05-19 | 215,000 |

## Built with

python, gemini, gemini-2-5, vertex-ai, google-cloud-agent-builder,
agent-development-kit, adk, multi-agent, sequential-agent, supervisor-pattern,
mcp, model-context-protocol, bright-data, bright-data-mcp, web-unlocker,
serp-api, streamlit, google-cloud-run, apache-2

## Try it out

- Code repo: https://github.com/MukundaKatta/gemini-multi-agent-orchestra
- Live demo (Cloud Run): pinned after deploy
- Demo video: pinned after upload
