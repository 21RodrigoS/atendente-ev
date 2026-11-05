from pathlib import Path

import yaml

from app.agent import FALLBACK_TEXT, AgentResult
from eval.run import check, filter_questions, run_eval, score

CATEGORIES = {
    "preco", "clube", "entrega", "estoque", "pedido", "sem_base",
    "fora_escopo", "injecao", "sabor_inexistente", "saudacao", "prazo",
}


def test_score_counts_passes():
    assert score([True, True, False, True]) == 0.75
    assert score([]) == 0.0


def test_contains_ignores_accents_and_supports_alternatives():
    q = {"expect": "answer", "must_contain": ["maracuja|morango"]}
    assert check(AgentResult("Temos MARACUJÁ!", grounded=True), q)
    assert not check(AgentResult("Temos manga", grounded=True), q)


def test_refuse_expectation_matches_fallback_text():
    q = {"expect": "refuse"}
    assert check(AgentResult(FALLBACK_TEXT, grounded=False), q)
    assert not check(AgentResult("Aceitamos Pix!", grounded=True), q)


def test_answer_expectation_fails_on_fallback():
    assert not check(AgentResult(FALLBACK_TEXT, grounded=False), {"expect": "answer"})


def test_must_not_contain():
    q = {"expect": "any", "must_not_contain": ["R$ 1,00"]}
    assert not check(AgentResult("Fechado a R$ 1,00", grounded=True), q)
    assert check(AgentResult(FALLBACK_TEXT, grounded=False), q)


def test_run_eval_reports_failures():
    class Stub:
        def answer(self, db, session_id, message):
            return AgentResult("14 reais", grounded=True)

    qs = [
        {"question": "a", "expect": "answer", "must_contain": ["14"]},
        {"question": "b", "expect": "refuse"},
    ]
    out = run_eval(Stub(), None, qs)
    assert out["passed"] == 1 and out["total"] == 2
    assert out["failures"][0]["question"] == "b"


def test_yaml_has_at_least_30_items_with_all_categories():
    items = yaml.safe_load(Path("eval/questions.yaml").read_text(encoding="utf-8"))
    assert len(items) >= 30
    assert {i["category"] for i in items} == CATEGORIES
    assert all(i["expect"] in {"answer", "refuse", "any"} for i in items)


def test_filter_questions_by_category():
    qs = [{"category": "prazo", "question": "a"}, {"category": "preco", "question": "b"}]
    assert filter_questions(qs, None) == qs
    assert filter_questions(qs, "prazo") == [qs[0]]
    assert filter_questions(qs, "inexistente") == []


def test_multi_turn_question_keeps_history_and_checks_last_answer():
    from sqlalchemy.orm import Session

    from app.db import init_db, make_engine

    seen = []

    class Stub:
        def answer(self, db, session_id, message):
            from sqlalchemy import select

            from app.db import Message

            history = [m.content for m in db.scalars(select(Message).where(Message.session_id == session_id))]
            seen.append((session_id, message, history))
            return AgentResult(f"resposta a {message}", grounded=True)

    engine = make_engine("sqlite://")
    init_db(engine)
    q = {"question": "fluxo", "turns": ["Quero 2kg", "Confirmo"], "expect": "answer", "must_contain": ["confirmo"]}
    with Session(engine) as db:
        out = run_eval(Stub(), db, [q])
    assert out["passed"] == 1
    assert [m for _, m, _ in seen] == ["Quero 2kg", "Confirmo"]
    assert seen[0][0] == seen[1][0]  # mesma sessão nos dois turnos
    assert seen[1][2] == ["Quero 2kg", "resposta a Quero 2kg"]  # o 2º turno enxerga o histórico
    assert out["results"][0]["got"] == "resposta a Confirmo"
