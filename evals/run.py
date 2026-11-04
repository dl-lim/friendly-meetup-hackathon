"""Run every test case through the agent, score it, and save a scorecard.

  uv run python -m evals.run --label baseline
  uv run python -m evals.run --only late-refund    # one case
  uv run python -m evals.run --no-judge            # checks only (faster)
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.table import Table

from agent.agent import run_agent
from agent.llm import client_for
from evals.checks import CHECKS
from evals.judge import judge

ROOT = Path(__file__).parent.parent
console = Console()


def icon(passed: bool | None) -> str:
    return {True: "✅", False: "❌", None: "➖"}[passed]


def is_errored(row: dict) -> bool:
    """True if the harness couldn't finish grading this case (agent, check or judge failed)."""
    return row.get("status") == "error" or "error" in row.get("result", {})  # older files lack status


def row_icon(row: dict) -> str:
    """Pass column: errors get their own icon so a crash never looks like a verdict."""
    return "⚠️" if is_errored(row) else icon(row.get("passed"))


def preflight(roles: list[str]) -> None:
    """Make one tiny call per model so a missing model or bad key stops the run before it starts."""
    for role in roles:
        try:
            client, model = client_for(role)
            client.chat.completions.create(model=model, messages=[{"role": "user", "content": "Reply OK."}])
        except Exception as e:
            console.print(f"[red bold]Preflight failed for {role} model: {e}[/red bold]")
            console.print(
                f"Check {role}_BASE_URL / {role}_MODEL / {role}_API_KEY in .env. "
                "Local Ollama models: run scripts/pull-models.sh"
                + (".  Or skip the judge with --no-judge." if role == "JUDGE" else ".")
            )
            sys.exit(2)
        console.print(f"[green]✓ {role} model reachable: {model}[/green]")


def evaluate(case: dict, use_judge: bool) -> dict:
    try:
        result = run_agent(case["input"])
    except Exception as e:
        result = {"answer": "", "tool_calls": [], "latency_s": 0, "tokens": 0, "error": str(e)}
        console.print(f"[red]Agent error on {case['id']}: {e}[/red]")
        # The agent never answered, so there's nothing to grade: skip checks and judge.
        checks = [{**check, "passed": None} for check in case.get("checks", [])]
        return {"case": case, "result": result, "checks": checks, "judge": None,
                "passed": None, "status": "error", "error": {"stage": "agent", "message": str(e)}}

    # If a check or the judge raises, keep going (record what did run) but mark the case errored:
    # a partly graded case could look like a pass when the missing part would have failed it.
    error = None
    checks = []
    for check in case.get("checks", []):
        fn = CHECKS.get(check["type"])
        if fn is None:
            console.print(f"[yellow]Unknown check type '{check['type']}' in {case['id']}[/yellow]")
            checks.append({**check, "passed": None})
            continue
        try:
            checks.append({**check, "passed": fn(result, check.get("value"))})
        except Exception as e:
            console.print(f"[red]Check error on {case['id']} ({check['type']}): {e}[/red]")
            checks.append({**check, "passed": None, "error": str(e)})
            error = error or {"stage": "check", "message": f"{check['type']}: {e}"}

    verdict, judge_error = None, None
    if use_judge:
        try:
            verdict = judge(case, result)
        except Exception as e:
            console.print(f"[red]Judge error on {case['id']}: {e}[/red]")
            judge_error = str(e)
            error = error or {"stage": "judge", "message": judge_error}

    if error:
        row = {"case": case, "result": result, "checks": checks, "judge": verdict,
               "passed": None, "status": "error", "error": error}
        if judge_error:
            row["judge_error"] = judge_error  # kept even when a check failed first
        return row

    # A case passes if every check (and the judge) that ran passed. Nothing ran = not scored.
    outcomes = [c["passed"] for c in checks] + [verdict["passed"] if verdict else None]
    scored = [o for o in outcomes if o is not None]
    passed = all(scored) if scored else None
    status = {True: "pass", False: "fail", None: "unscored"}[passed]

    return {"case": case, "result": result, "checks": checks, "judge": verdict,
            "passed": passed, "status": status}


def error_stage(row: dict) -> str:
    """' (judge)' / ' (check)' suffix for the errored list; agent errors are the default, so no suffix."""
    stage = row.get("error", {}).get("stage", "agent")
    return "" if stage == "agent" else f" ({stage})"


def print_scorecard(rows: list[dict]) -> None:
    table = Table(title="Scorecard")
    for column in ["Case", "Pass", "Checks", "Judge", "Tools used", "Secs"]:
        table.add_column(column)
    for row in rows:
        verdict = row["judge"]
        table.add_row(
            row["case"]["id"],
            row_icon(row),
            " ".join(icon(c["passed"]) for c in row["checks"]) or "-",
            "⚠️" if row.get("judge_error") else f"{verdict['score']}/5" if verdict else "-",
            ", ".join(t["name"] for t in row["result"]["tool_calls"]) or "-",
            str(row["result"]["latency_s"]),
        )
    console.print(table)

    errored = [r for r in rows if is_errored(r)]
    scored = [r for r in rows if r["passed"] is not None and not is_errored(r)]
    passes = sum(r["passed"] for r in scored)
    by_tag = defaultdict(list)
    for r in scored:
        for tag in r["case"].get("tags", []):
            by_tag[tag].append(r["passed"])

    unscored = len(rows) - len(scored) - len(errored)
    console.print(f"[bold]Pass rate: {passes}/{len(scored)}[/bold]  (not scored: {unscored}, errored: {len(errored)})")
    if errored:
        console.print(
            f"[red bold]⚠️  {len(errored)} case(s) errored and are excluded from the pass rate: "
            + ", ".join(f"{r['case']['id']}{error_stage(r)}" for r in errored) + "[/red bold]"
        )
    console.print("By tag: " + (", ".join(f"{t} {sum(v)}/{len(v)}" for t, v in sorted(by_tag.items())) or "-"))
    console.print(
        f"Avg latency: {sum(r['result']['latency_s'] for r in rows) / len(rows):.1f}s  "
        f"Total tokens: {sum(r['result']['tokens'] for r in rows)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="name for this run, e.g. baseline")
    parser.add_argument("--cases", default=ROOT / "evals" / "cases.jsonl", type=Path)
    parser.add_argument("--only", help="run a single case by id")
    parser.add_argument("--no-judge", action="store_true")
    args = parser.parse_args()

    cases = [json.loads(line) for line in args.cases.read_text().splitlines() if line.strip()]
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]

    preflight(["AGENT"] + ([] if args.no_judge else ["JUDGE"]))

    rows = []
    for case in cases:
        with console.status(f"Running {case['id']}..."):
            rows.append(evaluate(case, use_judge=not args.no_judge))

    print_scorecard(rows)

    # A run with errors isn't comparable to a clean one, so its filename says so.
    errored = any(is_errored(r) for r in rows)
    suffix = "-ERRORS" if errored else ""
    out = ROOT / "results" / f"{datetime.now():%Y%m%d-%H%M%S}-{args.label}{suffix}.jsonl"
    out.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    console.print(f"Saved: {out.relative_to(ROOT)}")
    if errored:
        sys.exit(1)


if __name__ == "__main__":
    main()
