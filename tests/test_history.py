from app.agent import AgentResult
from eval.history import compare_runs, list_runs, load_run, save_run
from eval.run import run_eval


def _run(results, **meta):
    passed = sum(1 for r in results if r["passed"])
    return {"meta": {"model": "m", "commit": "abc", **meta}, "passed": passed, "total": len(results), "results": results}


def _r(q, ok):
    return {"question": q, "expect": "answer", "passed": ok, "got": "x"}


def test_run_eval_returns_per_question_results():
    class Stub:
        def answer(self, db, session_id, message):
            return AgentResult("14 reais", grounded=True)

    out = run_eval(Stub(), None, [{"question": "a", "expect": "answer", "must_contain": ["14"]}])
    assert out["results"] == [{"question": "a", "expect": "answer", "passed": True, "got": "14 reais"}]


def test_compare_finds_regressions_and_improvements():
    old = _run([_r("a", True), _r("b", False), _r("c", True)])
    new = _run([_r("a", False), _r("b", True), _r("c", True)])
    diff = compare_runs(old, new)
    assert diff["regressions"] == ["a"]
    assert diff["improvements"] == ["b"]
    assert diff["score_old"] == old["passed"] / 3
    assert diff["score_new"] == new["passed"] / 3


def test_compare_ignores_questions_missing_in_one_run():
    old = _run([_r("a", True)])
    new = _run([_r("a", True), _r("novo", False)])
    diff = compare_runs(old, new)
    assert diff["regressions"] == [] and diff["added"] == ["novo"]


def test_save_and_load_roundtrip_in_order(tmp_path):
    first = save_run(_run([_r("a", True)], label="r1"), tmp_path, stamp="2026-11-05T10-00-00")
    second = save_run(_run([_r("a", False)], label="r2"), tmp_path, stamp="2026-11-05T11-00-00")
    assert load_run(first)["meta"]["label"] == "r1"
    assert list_runs(tmp_path) == [first, second]
