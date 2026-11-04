"""Intensive run: repeats, a held-out split and honest counts (ideas from Axolotl's verifier).

  uv run python -m evals.gen_orders                      # builds heldout/orders.jsonl
  uv run python -m evals.merge_cases                     # builds evals/cases.all.jsonl
  uv run python -m evals.intensive run --label base      # BEFORE touching agent/
  uv run python -m evals.intensive run --label fix-1     # after one change
  uv run python -m evals.intensive compare base fix-1

Rules it enforces:
  * Each case runs --repeats times. pass = every attempt passed, fail = none did,
    flaky = both. A fix only counts as stable fail -> stable pass; flaky moves are noise.
  * An attempt where the agent crashed/timed out or the judge broke is INCONCLUSIVE.
    Inconclusive is never a pass.
  * Each case is counted once, after its repeats are combined (never summed per attempt).
  * Held-out cases are shown as ids and totals only. Their inputs stay out of the
    console and the report, so the person fixing the bot can run them without seeing them.

Judge calls are cached on (case, answer, tools called): a repeat that gives the
same answer reuses the verdict, so every attempt is judged but only distinct
answers cost a judge call. A broken judge is never cached.

Each repeat is also saved in run.py's format (results/<label>-r1.jsonl ...), so
evals.compare and evals.calibrate read them unchanged.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import evals.run as run_mod
from evals.run import evaluate

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
CAVEATS = [
    "Agreement on these cases is not proof the bot is ready: untested behaviour can still be wrong.",
    "Inconclusive is not a pass: those cases are counted separately and never in the pass rate.",
    "Held-out independence is by honour: the person fixing the bot can open heldout/. "
    "If they did before the fix was final, the held-out numbers are no longer independent.",
    "Held-out answers are computed from orders.json and policies.md by evals/gen_orders.py; "
    "cases the policy doesn't decide were not generated.",
]


_judge, _cache, _hits = run_mod.judge, {}, Counter()


def cached_judge(case: dict, result: dict) -> dict | None:
    key = (case["id"], result.get("answer"), tuple(t.get("name") for t in result.get("tool_calls") or []))
    if key in _cache:
        _hits["hit"] += 1
        return _cache[key]
    _hits["call"] += 1
    verdict = _judge(case, result)
    if verdict and not str(verdict.get("reason", "")).startswith("judge failed"):
        _cache[key] = verdict
    return verdict


run_mod.judge = cached_judge  # evaluate() looks judge up in evals.run at call time


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip() and not line.lstrip().startswith("#")]


def attempt_outcome(row: dict) -> str:
    """pass / fail / inconclusive / unscored for one attempt."""
    if "error" in row["result"]:
        return "inconclusive"
    if row["judge"] and str(row["judge"].get("reason", "")).startswith("judge failed"):
        return "inconclusive"
    return {True: "pass", False: "fail", None: "unscored"}[row["passed"]]


def case_state(outcomes: list[str]) -> str:
    seen = set(outcomes)
    if "pass" in seen and "fail" in seen:
        return "flaky"
    if "fail" in seen:
        return "fail"
    if "inconclusive" in seen:
        return "inconclusive"  # passed when it ran, but not every attempt ran
    if seen == {"pass"}:
        return "pass"
    return "unscored"


STATES = ["pass", "fail", "flaky", "inconclusive", "unscored"]


def summarise(states: dict[str, dict]) -> dict[str, Counter]:
    out = {"visible": Counter(), "heldout": Counter()}
    for s in states.values():
        out[s["split"]][s["state"]] += 1
    return out


def run(args: argparse.Namespace) -> None:
    visible_path = args.visible or (ROOT / "evals" / ("cases.all.jsonl" if (ROOT / "evals" / "cases.all.jsonl").exists() else "cases.jsonl"))
    visible = load(Path(visible_path))
    heldout = load(args.heldout) if args.heldout.exists() else []
    clash = {c["id"] for c in visible} & {c["id"] for c in heldout}
    if clash or any(c["id"].startswith("hord-") for c in visible):
        sys.exit("held-out cases found in the visible suite: they would stop being an independent check")
    if args.limit:
        visible, heldout = visible[: args.limit], heldout[: args.limit]

    split = {c["id"]: "visible" for c in visible} | {c["id"]: "heldout" for c in heldout}
    jobs = [(r, c) for r in range(1, args.repeats + 1) for c in visible + heldout]
    print(f"{len(visible)} visible + {len(heldout)} held-out cases x {args.repeats} repeats = {len(jobs)} attempts, "
          f"{args.workers} workers (agent {os.environ.get('AGENT_MODEL')}, judge {os.environ.get('JUDGE_MODEL')})")

    rows: dict[int, list[dict]] = {r: [] for r in range(1, args.repeats + 1)}
    start, done = time.perf_counter(), 0
    with ThreadPoolExecutor(args.workers) as pool:
        futures = {pool.submit(evaluate, c, not args.no_judge): (r, c) for r, c in jobs}
        for f in as_completed(futures):
            r, c = futures[f]
            rows[r].append(f.result())
            done += 1
            if done == 10 or done % 25 == 0 or done == len(jobs):
                rate = done / (time.perf_counter() - start)
                print(f"  {done}/{len(jobs)} attempts, ETA {(len(jobs) - done) / rate / 60:.1f} min", flush=True)

    RESULTS.mkdir(exist_ok=True)
    for r, rs in rows.items():
        rs.sort(key=lambda row: row["case"]["id"])
        (RESULTS / f"{args.label}-r{r}.jsonl").write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in rs))

    per_case: dict[str, list[str]] = {}
    for rs in rows.values():
        for row in rs:
            per_case.setdefault(row["case"]["id"], []).append(attempt_outcome(row))
    states = {cid: {"split": split[cid], "state": case_state(o), "attempts": o} for cid, o in sorted(per_case.items())}
    meta = {"label": args.label, "at": f"{datetime.now():%Y-%m-%d %H:%M}", "repeats": args.repeats,
            "agent_model": os.environ.get("AGENT_MODEL"), "judge_model": None if args.no_judge else os.environ.get("JUDGE_MODEL"),
            "visible_file": str(visible_path), "minutes": round((time.perf_counter() - start) / 60, 1)}
    (RESULTS / f"intensive-{args.label}.json").write_text(json.dumps({"meta": meta, "states": states}, indent=1))

    report = render_run(meta, states).replace("## Caveats", "\n".join(judge_only_lines(args.label, states)) + "\n\n## Caveats", 1)
    (RESULTS / f"intensive-{args.label}.md").write_text(report)
    print(report)
    print(f"Judge calls: {_hits['call']}, reused for identical answers: {_hits['hit']}")
    print(f"Saved results/intensive-{args.label}.md and results/{args.label}-r1..r{args.repeats}.jsonl")


def render_run(meta: dict, states: dict[str, dict]) -> str:
    counts = summarise(states)
    lines = [f"# Intensive run: {meta['label']}", "",
             f"{meta['at']} · agent `{meta['agent_model']}` · judge `{meta['judge_model']}` · "
             f"{meta['repeats']} repeats · {meta['minutes']} min", "",
             "| Split | Cases | Stable pass | Fail | Flaky | Inconclusive | Unscored |", "|---|---|---|---|---|---|---|"]
    for sp in ["visible", "heldout"]:
        c = counts[sp]
        if sum(c.values()):
            lines.append(f"| {sp} | {sum(c.values())} | {c['pass']} | {c['fail']} | {c['flaky']} | {c['inconclusive']} | {c['unscored']} |")
    lines += ["", "A case is a stable pass only if it passed every attempt. Inconclusive and unscored cases are never counted as passes.", ""]
    vis_bad = [f"{cid} ({s['state']})" for cid, s in states.items() if s["split"] == "visible" and s["state"] != "pass"]
    if vis_bad:
        lines += ["**Visible cases not stably passing:** " + ", ".join(vis_bad), ""]
    held_bad = [cid for cid, s in states.items() if s["split"] == "heldout" and s["state"] != "pass"]
    if held_bad:
        lines += [f"**Held-out not stably passing:** {len(held_bad)} cases (ids only, inputs sealed): " + ", ".join(held_bad), ""]
    lines += ["## Caveats", *[f"- {c}" for c in CAVEATS], ""]
    return "\n".join(lines)


def judge_only(label: str) -> set[str] | None:
    """Cases whose every failed attempt passed all deterministic checks: the judge alone failed them.

    Read from the saved repeat files, so it works on runs made before this existed.
    """
    files = sorted(RESULTS.glob(f"{label}-r*.jsonl"))
    if not files:
        return None
    failed: dict[str, list[bool]] = {}
    for f in files:
        for row in load(f):
            if attempt_outcome(row) == "fail":
                checks_ok = all(c.get("passed") is not False for c in row["checks"])
                failed.setdefault(row["case"]["id"], []).append(checks_ok)
    return {cid for cid, oks in failed.items() if all(oks)}


def judge_only_lines(label: str, states: dict[str, dict]) -> list[str]:
    ids = judge_only(label)
    if ids is None:
        return [f"_Judge-only split for {label}: copy results/{label}-r*.jsonl here to see it._"]
    vis = sorted(c for c in ids if states.get(c, {}).get("split") == "visible")
    held = sum(states.get(c, {}).get("split") == "heldout" for c in ids)
    return [f"**{label}, failed on the judge alone (every check passed):** {len(vis)} visible, {held} held-out"
            + (f" ({', '.join(vis)})" if vis else "")]


def compare(args: argparse.Namespace) -> None:
    before = json.loads((RESULTS / f"intensive-{args.before}.json").read_text())["states"]
    after = json.loads((RESULTS / f"intensive-{args.after}.json").read_text())["states"]
    lines = [f"# {args.before} → {args.after}", "",
             "| Split | Fixed (fail→pass) | Broke (pass→fail) | Noise (flaky either side) | Inconclusive either side | Stable pass before → after |",
             "|---|---|---|---|---|---|"]
    tally = {}
    for sp in ["visible", "heldout"]:
        ids = sorted(cid for cid in before.keys() & after.keys() if before[cid]["split"] == sp)
        if not ids:
            continue
        moves = Counter()
        for cid in ids:
            b, a = before[cid]["state"], after[cid]["state"]
            if "inconclusive" in (b, a):
                moves["inconclusive"] += 1
            elif "flaky" in (b, a) and b != a:
                moves["noise"] += 1
            elif b == "fail" and a == "pass":
                moves["fixed"] += 1
            elif b == "pass" and a == "fail":
                moves["broke"] += 1
        pb = sum(before[c]["state"] == "pass" for c in ids)
        pa = sum(after[c]["state"] == "pass" for c in ids)
        tally[sp] = moves
        lines.append(f"| {sp} | {moves['fixed']} | {moves['broke']} | {moves['noise']} | {moves['inconclusive']} | {pb}/{len(ids)} → {pa}/{len(ids)} |")
        if sp == "visible":
            for cid in ids:
                b, a = before[cid]["state"], after[cid]["state"]
                if b != a:
                    lines.append(f"|  | `{cid}` {b} → {a} | | | | |")

    v, h = tally.get("visible", Counter()), tally.get("heldout", Counter())
    if v["broke"] or h["broke"]:
        verdict = f"Something broke: {v['broke']} visible and {h['broke']} held-out cases went from stable pass to fail."
    elif v["fixed"] and not h["fixed"] and "heldout" in tally:
        verdict = "Visible improved but held-out didn't: the fix may be overfit to the visible wording."
    elif v["fixed"] and h["fixed"]:
        verdict = f"The fix generalises: {v['fixed']} visible and {h['fixed']} unseen held-out cases fixed, nothing broke."
    elif h["fixed"]:
        verdict = f"Held-out improved ({h['fixed']} fixed) with no visible change."
    else:
        verdict = "No stable change."
    lines += ["", *judge_only_lines(args.before, before), "", *judge_only_lines(args.after, after)]
    lines += ["", f"**Verdict:** {verdict}", "", "## Caveats", *[f"- {c}" for c in CAVEATS], ""]
    report = "\n".join(lines)
    (RESULTS / f"intensive-compare-{args.before}-{args.after}.md").write_text(report)
    print(report)


def flaky(args: argparse.Namespace) -> None:
    """Split flaky cases: did the bot change what it did, or did only the judge change its mind?

    The judge verdict is cached on identical answers, so a flip always comes with a
    different answer. If the deterministic checks flip too, the bot behaved differently
    (bot noise). If the checks agree on every attempt and only the judge flipped, the
    answers differed in wording only (judge noise).
    """
    states = json.loads((RESULTS / f"intensive-{args.label}.json").read_text())["states"]
    attempts: dict[str, list[dict]] = {}
    for f in sorted(RESULTS.glob(f"{args.label}-r*.jsonl")):
        for row in load(f):
            attempts.setdefault(row["case"]["id"], []).append(row)
    split = {"visible": Counter(), "heldout": Counter()}
    ids = {"bot": [], "judge": [], "nochecks": []}
    judge_only_rows = []
    for cid, s in states.items():
        if s["state"] != "flaky":
            continue
        rows = [r for r in attempts.get(cid, []) if attempt_outcome(r) in ("pass", "fail")]
        checks = {tuple(c.get("passed") for c in r["checks"]) for r in rows}
        kind = "nochecks" if rows and not rows[0]["checks"] else "bot" if len(checks) > 1 else "judge"
        split[s["split"]][kind] += 1
        if kind != "bot" and rows:
            judge_only_rows.append(rows[0])
        if s["split"] == "visible":
            ids[kind].append(cid)
    lines = [f"# Flaky cases in {args.label}: bot noise vs judge noise", "",
             "| Split | Flaky | Bot changed (checks flipped) | Judge only (checks identical, verdict flipped) | No checks (can't tell) |",
             "|---|---|---|---|---|"]
    for sp, c in split.items():
        if sum(c.values()):
            lines.append(f"| {sp} | {sum(c.values())} | {c['bot']} | {c['judge']} | {c['nochecks']} |")
    lines += ["", f"Visible, bot noise: {', '.join(ids['bot']) or '-'}", "", f"Visible, judge only: {', '.join(ids['judge']) or '-'}", "",
              f"Visible, no checks: {', '.join(ids['nochecks']) or '-'}", "",
              "'Checks identical' means the facts the checks test didn't change; the wording did "
              "(identical answers reuse the cached verdict). Held-out ids stay sealed.", ""]
    if args.rejudge and judge_only_rows:
        def regrade(row):
            return [(_judge(row["case"], row["result"]) or {}).get("passed") for _ in range(args.rejudge)]
        with ThreadPoolExecutor(4) as pool:
            verdicts = list(pool.map(regrade, judge_only_rows))
        flips = sum(len(set(v)) > 1 for v in verdicts)
        lines += [f"**Same answer, re-judged {args.rejudge}x (no cache):** {flips} of {len(verdicts)} judge-only/no-check "
                  "flaky cases got different verdicts on the identical answer. This is the judge disagreeing with itself.", ""]
    report = "\n".join(lines)
    (RESULTS / f"intensive-flaky-{args.label}.md").write_text(report)
    print(report)


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--label", required=True)
    r.add_argument("--visible", type=Path, help="default: evals/cases.all.jsonl if merged, else evals/cases.jsonl")
    r.add_argument("--heldout", type=Path, default=ROOT / "heldout" / "orders.jsonl")
    r.add_argument("--repeats", type=int, default=3)
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--limit", type=int, help="first N cases of each split (smoke test)")
    r.add_argument("--no-judge", action="store_true")
    c = sub.add_parser("compare")
    c.add_argument("before")
    c.add_argument("after")
    fl = sub.add_parser("flaky")
    fl.add_argument("label")
    fl.add_argument("--rejudge", type=int, default=0, help="re-grade one identical answer N times, uncached")
    args = parser.parse_args()
    {"run": run, "compare": compare, "flaky": flaky}[args.cmd](args)


if __name__ == "__main__":
    main()
