"""Deterministic checks: fast, free and repeatable.

Each check gets the agent's `result` and the `value` from the test case, and returns:
  True = pass, False = fail, None = not implemented yet (skipped)

`result` looks like:
  {"answer": "...", "tool_calls": [{"name": "get_order", "args": {"order_id": "PP-1001"}}],
   "latency_s": 3.2, "tokens": 812}
"""

import re


def contains(result: dict, value: str) -> bool:
    # passes when value appears anywhere in the answer (case-insensitive).
    return value.lower() in result["answer"].lower()


def not_contains(result: dict, value: str) -> bool:
    # passes when value does NOT appear in the answer — useful for safety/privacy checks.
    return value.lower() not in result["answer"].lower()


def tool_called(result: dict, value: str) -> bool:
    # result["tool_calls"] is a list of {"name": ..., "args": ...} built by the agent loop.
    # e.g. check: tool_called, value: "get_order" passes only when the agent called get_order.
    return any(call["name"] == value for call in result["tool_calls"])


def tool_called_with(result: dict, value: str) -> bool:
    # value format: "tool_name:key=val"  e.g. "get_order:order_id=PP-1003"
    # passes when the named tool was called with that exact key/value in its args.
    tool_name, _, kv = value.partition(":")
    key, _, expected = kv.partition("=")
    return any(
        call["name"] == tool_name and str(call["args"].get(key)) == expected
        for call in result["tool_calls"]
    )


def max_seconds(result: dict, value: str) -> bool:
    # value: a number string, e.g. "5"  — passes when latency_s is at or below the limit.
    return result["latency_s"] <= float(value)


def max_words(result: dict, value: str) -> bool:
    # value: a number string, e.g. "50"  — passes when the answer is at or below that word count.
    return len(result["answer"].split()) <= int(value)


def no_tools(result: dict, value: str) -> bool:
    # passes when the agent called no tools at all (value is ignored).
    return len(result["tool_calls"]) == 0


def matches_regex(result: dict, value: str) -> bool:
    # value: a regex pattern, e.g. "£[0-9]+\\.[0-9]{2}"
    return bool(re.search(value, result["answer"]))


CHECKS = {
    "contains": contains,
    "not_contains": not_contains,
    "tool_called": tool_called,
    "tool_called_with": tool_called_with,
    "max_seconds": max_seconds,
    "max_words": max_words,
    "no_tools": no_tools,
    "matches_regex": matches_regex,
}
