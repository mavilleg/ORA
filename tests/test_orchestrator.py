from app.orchestrator import ArenaOrchestrator


def test_parse_judge_scores_plain_json() -> None:
    orchestrator = ArenaOrchestrator()
    scores = orchestrator._parse_judge_scores('{"scores":{"a":0.8,"b":0.2}}')
    assert scores == {'a': 0.8, 'b': 0.2}


def test_parse_judge_scores_fenced_json() -> None:
    orchestrator = ArenaOrchestrator()
    raw = '```json\n{"scores":{"a":0.7}}\n```'
    scores = orchestrator._parse_judge_scores(raw)
    assert scores == {'a': 0.7}


def test_parse_judge_scores_invalid_json() -> None:
    orchestrator = ArenaOrchestrator()
    scores = orchestrator._parse_judge_scores('not-json')
    assert scores == {}
