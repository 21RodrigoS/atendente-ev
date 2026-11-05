"""Compara duas rodadas salvas. Uso: uv run python -m eval.compare [ANTIGA.json NOVA.json]

Sem argumentos, compara as duas rodadas mais recentes de eval/runs/.
"""

import sys
from pathlib import Path

from eval.history import compare_runs, list_runs, load_run


def format_diff(old: dict, new: dict) -> str:
    diff = compare_runs(old, new)
    lines = [
        f"Antes:  {old['passed']}/{old['total']} = {diff['score_old']:.0%}  ({old['meta'].get('label', '')})",
        f"Depois: {new['passed']}/{new['total']} = {diff['score_new']:.0%}  ({new['meta'].get('label', '')})",
        f"Regressões (passavam e agora falham): {len(diff['regressions'])}",
        *[f"  - {q}" for q in diff["regressions"]],
        f"Melhorias (falhavam e agora passam): {len(diff['improvements'])}",
        *[f"  + {q}" for q in diff["improvements"]],
    ]
    if diff["added"]:
        lines.append(f"Perguntas novas: {len(diff['added'])}")
    if diff["removed"]:
        lines.append(f"Perguntas removidas: {len(diff['removed'])}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if len(argv) == 2:
        old_path, new_path = Path(argv[0]), Path(argv[1])
    else:
        runs = list_runs()
        if len(runs) < 2:
            print("É preciso ter pelo menos duas rodadas salvas em eval/runs/.")
            return 1
        old_path, new_path = runs[-2], runs[-1]
    print(format_diff(load_run(old_path), load_run(new_path)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
