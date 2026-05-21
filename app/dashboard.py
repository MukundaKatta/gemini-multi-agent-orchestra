"""gemini-multi-agent-orchestra dashboard."""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gemini_multi_agent_orchestra.runner import ask  # noqa: E402


st.set_page_config(
    page_title="gemini-multi-agent-orchestra",
    layout="wide",
    page_icon=":musical_keyboard:",
)
st.title("gemini-multi-agent-orchestra")
st.caption(
    "3-agent supervisor pattern on Vertex AI Agent Builder · "
    "DoraHacks Agents Without Masters"
)

with st.sidebar:
    st.header("Ask the orchestra")
    question = st.text_area(
        "Your research question",
        value=(
            "Rank the top 3 AI coding agents launched in May 2026 by "
            "adoption and cite their announcement URLs verbatim."
        ),
        height=140,
    )
    model = st.selectbox(
        "Gemini model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.5-flash-lite"],
        index=0,
    )
    stub = st.toggle(
        "Use stub Bright Data MCP",
        value=True,
        help=("On = local stub with canned SERPs + scraped pages. "
              "Off = real Bright Data account (set BRIGHTDATA_API_TOKEN)."),
    )
    run = st.button("Run orchestra", type="primary", use_container_width=True)
    st.divider()
    st.caption(
        f"Project: `{os.getenv('GOOGLE_CLOUD_PROJECT', 'not-set')}`  "
        f"Vertex AI: `{os.getenv('GOOGLE_GENAI_USE_VERTEXAI', 'true')}`"
    )

st.markdown(
    """
The supervisor (`SequentialAgent`) delegates to 3 sub-agents that hand
off through ADK session state:

- **researcher** — pulls the SERP via `search_engine`, scrapes the top 3
  via `scrape_page`, writes verbatim quotes to `research_notes`.
- **analyst** — reads `research_notes`, scores each source via
  `score_source`, writes the ranking to `scoring_log`.
- **writer** — reads both, composes the final ANSWER / EVIDENCE /
  SCORING / HANDOFF TRACE report. No tool calls in the writer.
"""
)

if run:
    with st.status("Running the orchestra...", expanded=True) as status:
        t0 = time.perf_counter()
        try:
            resp = ask(question, stub=stub, model=model)
        except Exception as e:  # pragma: no cover
            status.update(label=f"Error: {e}", state="error")
            st.exception(e)
            st.stop()
        elapsed = (time.perf_counter() - t0) * 1000
        status.update(label=f"Done in {elapsed:.0f} ms", state="complete")

    st.subheader("Final report (writer)")
    st.markdown(resp.final_text or "_(no final response)_")

    if resp.by_author:
        cols = st.columns(len(resp.by_author))
        for col, (author, text) in zip(cols, resp.by_author.items()):
            with col:
                st.markdown(f"**{author}**")
                st.code((text or "")[:1500], language=None)

    with st.expander(f"Agent event trace ({len(resp.events)} events)"):
        for i, ev in enumerate(resp.events):
            st.markdown(
                f"**{i}.** author=`{ev.get('author')}` "
                f"final=`{ev.get('is_final')}`"
            )
            text = ev.get("text") or ""
            if text:
                st.code(text[:1500], language=None)
else:
    st.info(
        "Use the sidebar to fire a research question through the "
        "researcher → analyst → writer orchestra."
    )
