"""LLM-as-judge: a second model grades each answer against rubric.md."""

import json
import re
from pathlib import Path

from agent.llm import client_for

RUBRIC = (Path(__file__).parent / "rubric.md").read_text()

# Rubric: 4 = correct with minor omissions, 3 = missing something the customer needs.
PASS_SCORE = 4


def _complete(client, model: str, messages: list[dict]) -> str:
    """Ask for JSON mode; retry without it if the provider rejects the option."""
    kwargs = {"model": model, "messages": messages, "temperature": 0}
    try:
        response = client.chat.completions.create(**kwargs, response_format={"type": "json_object"})
    except Exception:
        response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content or ""


def _parse(raw: str) -> dict:
    """Parse the judge's JSON, tolerating prose or code fences around it."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise ValueError(f"no JSON in judge reply: {raw[:200]!r}")
        return json.loads(match.group(0))


def judge(case: dict, result: dict) -> dict | None:
    """Return {"score": 1-5, "passed": bool, "reason": "..."}, or None to skip."""
    if not case.get("expected"):
        return None
    if not (result.get("answer") or "").strip():
        return {"score": 1, "passed": False, "reason": "No answer produced."}

    client, model = client_for("JUDGE")
    messages = [
        {"role": "system", "content": RUBRIC},
        {
            "role": "user",
            "content": (
                f"Customer question:\n{case['input']}\n\n"
                f"Expected behaviour:\n{case['expected']}\n\n"
                f"Assistant answer:\n{result['answer']}"
            ),
        },
    ]

    try:
        data = _parse(_complete(client, model, messages))
        score = max(1, min(5, int(data["score"])))
        return {"score": score, "passed": score >= PASS_SCORE, "reason": str(data.get("reason", ""))}
    except Exception as e:
        # passed=None means "not scored", so a broken judge never fails a case silently;
        # the error is still saved to results/ for inspection.
        return {"score": None, "passed": None, "reason": f"judge error: {e}"}
