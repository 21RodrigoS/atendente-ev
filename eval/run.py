"""Avaliação do atendente: roda as perguntas de eval/questions.yaml e calcula o score.

Uso: uv run python -m eval.run [--min 0.85]   (usa o provedor configurado no .env)
"""

import argparse
import subprocess
import sys
from pathlib import Path

import yaml

from app.agent import FALLBACK_TEXT, Agent, AgentResult
from app.tools import normalize

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


def score(results: list[bool]) -> float:
    return sum(results) / len(results) if results else 0.0


def run_eval(agent: Agent, db, questions: list[dict]) -> dict:
    results = []
    for i, q in enumerate(questions):
        result = agent.answer(db, f"eval-{i}", q["question"])
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

    parser = argparse.ArgumentParser()
    parser.add_argument("--min", type=float, default=0.0, help="score mínimo (0 a 1)")
    parser.add_argument("--repeat", type=int, default=1, help="quantas vezes rodar (mede a variação)")
    parser.add_argument("--label", default="", help="o que mudou desde a rodada anterior")
    parser.add_argument("--no-save", action="store_true", help="não grava em eval/runs/")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    engine = make_engine("sqlite://")
    init_db(engine)
    questions = yaml.safe_load(QUESTIONS.read_text(encoding="utf-8"))
    agent = Agent(build_provider(get_settings()), load_index(root / "knowledge", FastEmbedder()))
    with Session(engine) as db:
        seed_products(db, root / "data" / "products.json")
        out = run_eval(agent, db, questions)

    value = out["passed"] / out["total"]
    print(f"Score: {out['passed']}/{out['total']} = {value:.0%}")
    for f in out["failures"]:
        print(f"- [{f['expect']}] {f['question']}\n    -> {f['got']}")
    return 0 if value >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
