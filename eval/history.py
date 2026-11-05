"""Registro das rodadas de avaliação: salva cada execução e compara duas rodadas."""

import json
from datetime import datetime
from pathlib import Path

RUNS_DIR = Path(__file__).parent / "runs"


def save_run(run: dict, directory: Path = RUNS_DIR, stamp: str | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = stamp or datetime.now().strftime("%Y-%m-%dT%H-%M-%S")
    path = directory / f"{stamp}.json"
    n = 1
    while path.exists():  # duas rodadas no mesmo segundo
        path = directory / f"{stamp}-{n}.json"
        n += 1
    path.write_text(json.dumps(run, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_run(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def list_runs(directory: Path = RUNS_DIR) -> list[Path]:
    return sorted(Path(directory).glob("*.json"))


def compare_runs(old: dict, new: dict) -> dict:
    """Mostra o que passou a falhar (regressions) e o que passou a acertar (improvements)."""
    before = {r["question"]: r["passed"] for r in old["results"]}
    after = {r["question"]: r["passed"] for r in new["results"]}
    common = before.keys() & after.keys()
    return {
        "regressions": [q for q in after if q in common and before[q] and not after[q]],
        "improvements": [q for q in after if q in common and not before[q] and after[q]],
        "added": [q for q in after if q not in before],
        "removed": [q for q in before if q not in after],
        "score_old": old["passed"] / old["total"],
        "score_new": new["passed"] / new["total"],
    }
