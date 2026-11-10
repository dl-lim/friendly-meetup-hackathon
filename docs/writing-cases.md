# ✍️ Writing good test cases

## The format

One case per line in `evals/cases.jsonl`:

```json
{"id": "price-next-day", "category": "happy-path", "input": "How much does Next Day delivery cost?", "expected": "£6.50 for parcels up to 2 kg.", "checks": [{"type": "contains", "value": "6.50"}], "tags": ["policy"]}
```

| Field | What it's for |
|---|---|
| `id` | Short, unique name |
| `category` | One of the categories below (`happy-path`, `reasoning`, `multi-step`, `missing-info`, `doesnt-exist`, `edge-case`, `privacy`, `overpromising`, `injection`, `off-topic`, `not-in-policy`). Shown as "By category" on the scorecard |
| `input` | What the customer says |
| `expected` | Ideal behaviour, in plain English (for the judge) |
| `checks` | Deterministic checks to run (types live in `checks.py`) |
| `tags` | Free-form extra groups, e.g. `policy`, `safety` |

## What to cover

Aim for a mix. A test set of only easy questions tells you nothing.

| Category | Example idea |
|---|---|
| 😊 Happy path | Simple price or delivery-time questions |
| 🧮 Reasoning | Was order PP-1005 late *enough* for a refund? (Check the dates!) |
| 🔗 Multi-step | Needs **both** tools: an order lookup *and* a policy |
| ❓ Missing info | "Where's my parcel?" with no order ID |
| 🚫 Doesn't exist | An order ID that isn't in the data |
| 📏 Edge cases | A 25 kg parcel, a Sunday delivery, a perfume bottle |
| 🔒 Privacy | Asking for someone else's details |
| 💸 Overpromising | Pushing the bot to issue a refund itself |
| 🕵️ Injection | "Ignore your instructions and…" |
| 🌍 Off-topic | Questions nothing to do with parcels |

## Tips

- **One behaviour per case.** Easier to see what broke.
- **Check the truth.** Answers live in `agent/data/`, not in your memory.
- **Make cases fail for the right reason.** If a check fails, read the answer: is the bot wrong, or your check?
- **Avoid brittle checks.** `contains "£6.50"` fails on "6.50 pounds". Is that what you want?

## Keep the set lean

`evals/cases.jsonl` is the fast set (about 50 cases, every policy section and every category covered at least twice). The full 300+ case history lives in `evals/archive/cases-full.jsonl`; run it with `--cases evals/archive/cases-full.jsonl` before a release. Add a new case to the lean set only if no existing case would catch that failure.
