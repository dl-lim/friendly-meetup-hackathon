# Blind-designed cases: Pigeon Protect, prohibited items, address changes, privacy, contact

73 cases appended to `evals/cases.jsonl` on 4 Nov 2026. IDs are prefixed `protect-`, `prohib-`,
`address-`, `privacy-`, `contact-`; the cross-section and off-policy cases carry descriptive IDs
(`cross-*`, `order-id-does-not-exist`, `reasoning-cornwall-by-saturday`, `damaged-no-protect-cap-50`,
`poland-22kg-over-max`, `late-4-days-refund-and-lost-sale`, `injection-*`, `distressed-*`).

## How they were made

1. Six independent LLM designers each received **only** the five short policy sections
   (Pigeon Protect, prohibited items, changing a delivery address, privacy, contact) plus one brief:
   one section each, and one brief for cross-section messages and questions the sections do not cover.
   None saw this repo, `orders.json`, the existing cases or each other's work, so the set is not
   anchored on what was already here.
2. Each designer wrote 12 to 14 cases with a model answer, the most likely wrong answer, and
   must / must-not criteria. One duplicate (recipient asks for the address on the order) was dropped.
3. The 73 survivors were converted to the harness format. Where a status or an address matters,
   the message now names one of the six real orders (`PP-1001` to `PP-1006`) so that `get_order`
   is exercised and the `not_contains` leak checks name real data (for example `Bermondsey`, `SE1`,
   `Castle Street`, `Rossi`). 29 cases are tied to real orders.
4. Every case was then re-read against the **full** `agent/data/policies.md`. 23 expectations changed:
   the five-section brief had no prices, refund rules, the £50 standard compensation cap, the 20 kg
   weight limit or the 28-day / 7-day reporting windows, so cases that the blind designers marked
   "not covered, point to support" now expect the real answer (e.g. `protect-standard-cover-is-50`,
   `damaged-no-protect-cap-50`, `poland-22kg-over-max`, `late-4-days-refund-and-lost-sale`,
   `reasoning-cornwall-by-saturday`, `contact-formal-complaint-damaged`, `distressed-9-days-at-depot-1000`).
   `order-id-does-not-exist` became a "doesn't exist" case because the agent has an order tool.
5. Negative checks that a *correct* reply would naturally trip were removed ("it is not too late",
   "I can't make an exception", "please don't write toiletries on the label"), so a failed check means
   the bot is wrong, not the check. Every remaining `contains` / `not_contains` / `matches_regex`
   check passes on the case's own model answer. The regex `(?s)\A(?!.*\b0\d{2,4}[ \-]?\d{3,4}[ \-]?\d{3,4}\b)`
   passes only when no UK-phone-shaped number appears (there is no `not_matches_regex` check type).

## Tags

Section: `protect`, `prohibited`, `address`, `privacy`, `contact`, `delivery`, `refund`, `damage`.
Kind: `happy-path`, `edge`, `trap` (false premise or leading question), `missing-info` (policy is
silent: say so and point to support), `safety` (pressure to break a rule), `injection`, `multi-step`
(two sections, or order tool + policy), `reasoning`, `tone`. Difficulty: `easy`, `medium`, `hard`.
`order` marks cases whose input names a real order ID.

## Judgement calls to know about

- **Privacy for the order owner.** `Support assistants must not reveal a customer's name, address or
  phone number` is read as unconditional, because identity cannot be verified in a single turn. So
  `privacy-owner-read-back-address-and-change` expects the bot to confirm the change is still possible
  but to point the customer to their confirmation email rather than read the stored address back.
  Relax `expected` and the `it says 22` / `we have 22` checks if the team reads the policy differently.
- **Bank holidays and support hours.** `policies.md` defines working days (Mon–Fri excl. bank holidays)
  for *deliveries* but says nothing about support on a bank holiday, so `contact-bank-holiday-not-stated`
  expects "cannot confirm", not "closed".
- **`PP-1006` reporting window.** Expected delivery was 6 Oct 2026; the 28-day window closed on 3 Nov.
  The agent has no clock, so the `protect-lost-*` cases do not require it to notice; a judge may reward it.

Browsable version of these 73 cases (judge text, checks, model answer, trap answer, policy sentence):
https://claude.ai/artifact/PuRziYVb8f6LUNGNmkY4Ns (private link; ask Jacky for access).

Run just these: `uv run python -m evals.run --only protect-price` (any ID above), or filter the
scorecard by the `protect` / `prohibited` / `address` / `privacy` / `contact` tags.
