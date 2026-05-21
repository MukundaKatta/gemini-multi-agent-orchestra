"""Pin the canned 3-agent story chain for the orchestra demo.

The chain is `search_engine("Top 3 AI coding agents launched in May
2026") → scrape top 3 SERP results → score each → writer composes a
ranked report`. Tests assert each link in the chain is reproducible.
"""

from gemini_multi_agent_orchestra.mcp_stub import (
    _DATASETS,
    _SCRAPED_PAGES,
    _SERPS,
    _reset_scores_for_tests,
    score_source_response,
    scrape_page_response,
    search_engine_response,
    web_data_lookup_response,
)


QUERY = "Top 3 AI coding agents launched in May 2026"
TOP3_URLS = [
    "https://www.anthropic.com/news/claude-code-2-may-2026",
    "https://openai.com/index/codex-3-launch-may-2026",
    "https://developers.google.com/blog/gemini-code-assist-agent-ga-may-2026",
]


def test_serps_seeded():
    assert QUERY in _SERPS
    assert len(_SERPS[QUERY]) == 5


def test_search_engine_known_query_returns_5_serps():
    payload = search_engine_response(QUERY)
    assert payload["engine"] == "google"
    assert payload["result_count"] == 5
    titles = [r["title"] for r in payload["results"]]
    # Top 3 must be the vendor announcement pages (researcher's picks).
    assert any("Claude Code 2.0" in t for t in titles[:3])
    assert any("Codex 3" in t for t in titles[:3])
    assert any("Gemini Code Assist" in t for t in titles[:3])


def test_search_engine_unknown_query_fallback():
    payload = search_engine_response("some unrelated query")
    assert payload["result_count"] == 1
    assert "stub" in payload["results"][0]["title"].lower()


def test_search_engine_loose_match_routes_to_canonical_serp():
    """The researcher might rephrase the query slightly. Any query that
    mentions AI coding agents in May 2026 should still hit the canned
    top-3 SERP."""
    rephrasings = [
        "AI coding agents launched in May 2026",
        "best AI code agent releases May 2026",
        "Top AI coding agents May 2026 adoption",
    ]
    for q in rephrasings:
        payload = search_engine_response(q)
        assert payload["result_count"] == 5, f"missed match for {q!r}"


def test_scrape_page_top3_have_verbatim_adoption_numbers():
    """Each top-3 scrape must contain the verbatim adoption number the
    analyst will cite. These numbers are what the writer ranks by."""
    expected = {
        TOP3_URLS[0]: ("480,000", "2026-05-06"),
        TOP3_URLS[1]: ("310,000", "2026-05-12"),
        TOP3_URLS[2]: ("215,000", "2026-05-19"),
    }
    for url, (active, date) in expected.items():
        page = scrape_page_response(url)
        assert page["status"] == 200
        assert page["unlocked_by_brightdata"] is True
        assert active in page["text_excerpt"]
        assert date in page["text_excerpt"]


def test_scrape_page_unknown_url_returns_stub():
    payload = scrape_page_response("https://example.com/unknown")
    assert payload["status"] == 200
    assert payload["rendered_chars"] == 0
    assert payload["unlocked_by_brightdata"] is True


def test_score_source_clamps_and_ranks():
    _reset_scores_for_tests()
    # Out-of-range scores get clamped to [0, 10].
    r1 = score_source_response(TOP3_URLS[0], 9.5, "480k WAD")
    r2 = score_source_response(TOP3_URLS[1], 11.0, "310k WAD")  # clamps to 10
    r3 = score_source_response(TOP3_URLS[2], -1.0, "215k WAD")  # clamps to 0
    assert r1["recorded"]["score"] == 9.5
    assert r2["recorded"]["score"] == 10.0
    assert r3["recorded"]["score"] == 0.0
    # Final rank log: codex-3 (10) > claude (9.5) > gemini (0).
    ranked_urls = [e["url"] for e in r3["rank_log"]]
    assert ranked_urls == [TOP3_URLS[1], TOP3_URLS[0], TOP3_URLS[2]]
    assert r3["log_size"] == 3


def test_score_source_log_returned_with_every_call():
    _reset_scores_for_tests()
    r = score_source_response(TOP3_URLS[0], 8.0, "first")
    assert r["log_size"] == 1
    assert len(r["rank_log"]) == 1
    r = score_source_response(TOP3_URLS[1], 7.0, "second")
    assert r["log_size"] == 2
    assert len(r["rank_log"]) == 2


def test_web_data_lookup_returns_canonical_coding_agent_record():
    payload = web_data_lookup_response("coding_agent", "claude-code-2")
    assert payload["count"] == 1
    rec = payload["records"][0]
    assert rec["name"] == "Claude Code 2.0"
    assert rec["vendor"] == "Anthropic"
    assert rec["weekly_active"] == 480_000
    assert "VS Code" in rec["supports_ides"]


def test_web_data_lookup_unknown_returns_error_with_known_list():
    payload = web_data_lookup_response("coding_agent", "not-a-real-slug")
    assert "error" in payload
    assert any("claude-code-2" in k for k in payload["known"])


def test_supervisor_chain_is_consistent():
    """Top-level chain test: SERP → scrape top 3 → score each → ranking
    matches the verbatim adoption numbers in the scraped pages."""
    _reset_scores_for_tests()

    serp = search_engine_response(QUERY)
    assert serp["result_count"] == 5

    # Researcher would pick the top 3 first-party URLs.
    picks = [r["url"] for r in serp["results"][:3]]
    assert picks == TOP3_URLS

    # Researcher scrapes — verbatim adoption numbers are present.
    scrapes = [scrape_page_response(u) for u in picks]
    assert all(s["unlocked_by_brightdata"] for s in scrapes)
    assert "480,000" in scrapes[0]["text_excerpt"]
    assert "310,000" in scrapes[1]["text_excerpt"]
    assert "215,000" in scrapes[2]["text_excerpt"]

    # Analyst scores by adoption (weekly active devs).
    score_source_response(picks[0], 10.0, "480,000 weekly active developers")
    score_source_response(picks[1], 7.5,  "310,000 weekly active developers")
    final = score_source_response(picks[2], 5.5, "215,000 weekly active developers")

    # Writer would rank by score (highest first); chain is consistent.
    ranked_urls = [e["url"] for e in final["rank_log"]]
    assert ranked_urls == [picks[0], picks[1], picks[2]]
    assert final["log_size"] == 3
