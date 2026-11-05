"""Avaliação do atendente: roda as perguntas de eval/questions.yaml e calcula o score.

Uso: uv run python -m eval.run [--min 0.85]   (usa o provedor configurado no .env)
"""

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml

from app.agent import FALLBACK_TEXT, Agent, AgentResult
from app.tools import normalize
from eval.compare import format_diff
from eval.history import RUNS_DIR, list_runs, load_run, save_run

QUESTIONS = Path(__file__).parent / "questions.yaml"


def _git_commit(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=root, capture_output=True, text=True, check=False
        )
        return out.stdout.strip() or "desconhecido"
    except OSError:
        return "desconhecido"


def _has(text: str, option: str) -> bool:
    return any(alt.strip() and normalize(alt) in text for alt in option.split("|"))


def check(result: AgentResult, q: dict) -> bool:
    text = normalize(result.text)
    refused = result.text == FALLBACK_TEXT
    expect = q.get("expect", "answer")
    if expect == "refuse" and not refused:
        return False
    if expect == "answer" and (refused or not result.grounded):
        return False
    if any(normalize(bad) in text for bad in q.get("must_not_contain", [])):
        return False
    return refused or all(_has(text, opt) for opt in q.get("must_contain", []))


def filter_questions(questions: list[dict], category: str | None) -> list[dict]:
    if not category:
        return questions
    return [q for q in questions if q.get("category") == category]


def score(results: list[bool]) -> float:
    return sum(results) / len(results) if results else 0.0


def _ask(agent: Agent, db, session_id: str, q: dict) -> AgentResult:
    """Pergunta de um turno ou de vários (`turns`); só a última resposta é avaliada."""
    result = None
    for text in q.get("turns") or [q["question"]]:
        result = agent.answer(db, session_id, text)
        if db is not None:  # guarda o histórico para o próximo turno enxergar
            from app.db import Message

            db.add(Message(session_id=session_id, role="user", content=text, grounded=result.grounded))
            db.add(
                Message(session_id=session_id, role="assistant", content=result.text, grounded=result.grounded)
            )
            db.commit()
    return result


def run_eval(agent: Agent, db, questions: list[dict]) -> dict:
    results = []
    for i, q in enumerate(questions):
        result = _ask(agent, db, f"eval-{i}", q)
        results.append(
            {
                "question": q["question"],
                "expect": q["expect"],
                "passed": check(result, q),
                "got": result.text,
            }
        )
    failures = [r for r in results if not r["passed"]]
    return {
        "passed": len(results) - len(failures),
        "total": len(results),
        "failures": failures,
        "results": results,
    }


def main() -> int:
    from sqlalchemy.orm import Session

    from app.config import get_settings
    from app.db import init_db, make_engine, seed_products
    from app.providers import build_provider
    from app.rag.embedder import FastEmbedder
    from app.rag.index import load_index

    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # console do Windows é cp1252
    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=0.0, help="score mínimo (0 a 1)")
    parser.add_argument("--repeat", type=int, default=1, help="quantas vezes rodar (mede a variação)")
    parser.add_argument("--label", default="", help="o que mudou desde a rodada anterior")
    parser.add_argument("--category", default=None, help="roda só uma categoria de perguntas")
    parser.add_argument("--no-save", action="store_true", help="não grava em eval/runs/")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    engine = make_engine("sqlite://")
    init_db(engine)
    questions = filter_questions(
        yaml.safe_load(QUESTIONS.read_text(encoding="utf-8")), args.category
    )
    agent = Agent(build_provider(get_settings()), load_index(root / "knowledge", FastEmbedder()))
    settings = get_settings()
    values = []
    for n in range(args.repeat):
        previous = list_runs()
        with Session(engine) as db:
            seed_products(db, root / "data" / "products.json")
            out = run_eval(agent, db, questions)
        value = out["passed"] / out["total"]
        values.append(value)
        print(f"Rodada {n + 1}/{args.repeat}: {out['passed']}/{out['total']} = {value:.0%}")
        for f in out["failures"]:
            print(f"- [{f['expect']}] {f['question']}\n    -> {f['got']}")
        if not args.no_save:
            meta = {
                "label": args.label,
                "model": settings.llm_model,
                "commit": _git_commit(root),
                "date": datetime.now().isoformat(timespec="seconds"),
            }
            path = save_run({"meta": meta, **out}, RUNS_DIR)
            print(f"Salvo em {path.name}")
            if previous:
                print(format_diff(load_run(previous[-1]), load_run(path)))
    if len(values) > 1:
        print(f"Variação entre rodadas: min {min(values):.0%}, máx {max(values):.0%}")
    return 0 if min(values) >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
