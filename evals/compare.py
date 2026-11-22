"""Compare two runs side by side.

  uv run python -m evals.compare results/<before>.jsonl results/<after>.jsonl
"""

import json
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from evals.run import is_errored, row_icon


def load(path: str) -> dict:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    return {r["case"]["id"]: r for r in rows}


def main() -> None:
    before, after = load(sys.argv[1]), load(sys.argv[2])
    table = Table(title="Before → After")
    for column in ["Case", "Before", "After", "Change"]:
        table.add_column(column)

    for case_id in sorted(before.keys() | after.keys()):
        b_row, a_row = before.get(case_id, {}), after.get(case_id, {})
        b, a = b_row.get("passed"), a_row.get("passed")
        if is_errored(b_row) or is_errored(a_row):
            change = "⚠️ errored"  # can't call it fixed or broken if one side never ran
        else:
            change = "🟢 fixed" if (b is False and a) else "🔴 broke" if (b and a is False) else ""
        table.add_row(case_id, row_icon(b_row), row_icon(a_row), change)

    Console().print(table)
    for name, run in [("Before", before), ("After", after)]:
        errored = sum(is_errored(r) for r in run.values())
        scored = [r["passed"] for r in run.values() if r["passed"] is not None and not is_errored(r)]
        print(f"{name}: {sum(scored)}/{len(scored)} passed" + (f"  (⚠️ {errored} errored)" if errored else ""))


if __name__ == "__main__":
    main()
