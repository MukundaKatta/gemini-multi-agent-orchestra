from gemini_multi_agent_orchestra.agent import build_agent, _ADK_AVAILABLE


def test_adk_importable():
    assert _ADK_AVAILABLE


def test_supervisor_constructs():
    agent = build_agent(stub=True)
    assert agent is not None
    assert agent.name == "orchestra_supervisor"


def test_supervisor_has_three_sub_agents():
    agent = build_agent(stub=True)
    subs = list(getattr(agent, "sub_agents", []) or [])
    assert len(subs) == 3
    names = [s.name for s in subs]
    assert names == ["researcher", "analyst", "writer"]


def test_researcher_and_analyst_have_bright_data_tools():
    agent = build_agent(stub=True)
    subs = {s.name: s for s in agent.sub_agents}
    assert len(list(subs["researcher"].tools or [])) >= 1
    assert len(list(subs["analyst"].tools or [])) >= 1
    # Writer must NOT have tools — it only reads session state.
    assert len(list(subs["writer"].tools or [])) == 0


def test_sub_agents_use_output_key_for_handoff():
    agent = build_agent(stub=True)
    subs = {s.name: s for s in agent.sub_agents}
    assert subs["researcher"].output_key == "research_notes"
    assert subs["analyst"].output_key == "scoring_log"
    assert subs["writer"].output_key == "final_report"
