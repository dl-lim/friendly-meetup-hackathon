# Architecture Ideas

## Option 1: Single Agent
```
┌─────────────────────────────────────────┐
│     ProactiveAgent (Orchestrator)      │
│                                         │
│  ┌──────────────┐    ┌──────────────┐  │
│  │ Triage Agent │    │ Draft Agent  │  │
│  │              │    │              │  │
│  │ - Rules      │    │ - LLM        │  │
│  │ - LLM        │    │ - Templates  │  │
│  └──────────────┘    └──────────────┘  │
└─────────────────────────────────────────┘
           │                    │
           ▼                    ▼
    ┌──────────┐         ┌──────────┐
    │  Cases   │         │ Messages │
    └──────────┘         └──────────┘
           │
           ▼
    ┌──────────┐
    │  Review  │ (Human-in-the-loop)
    └──────────┘
```

## Option 2: Multi-Agent
```
┌─────────────────────────────────────────────┐
│         Coordinator Agent                    │
│  (Routes findings to appropriate agents)     │
└─────────────────────────────────────────────┘
           │
    ┌──────┼──────┬──────────┐
    ▼      ▼      ▼          ▼
┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ CVE  │ │Exposed│ │Misconf│ │Review│
│Agent │ │Service│ │ Agent │ │Agent │
└──────┘ └──────┘ └──────┘ └──────┘
    │      │      │          │
    └──────┴──────┴──────────┘
              │
              ▼
         ┌─────────┐
         │  Cases  │
         └─────────┘
```

## Option 3: Pipeline
```
Risk Findings
     │
     ▼
┌─────────────┐
│   Triage    │ → Filter: Should we notify?
└─────────────┘
     │
     ▼
┌─────────────┐
│   Group     │ → Group related findings?
└─────────────┘
     │
     ▼
┌─────────────┐
│   Draft     │ → Generate notification
└─────────────┘
     │
     ▼
┌─────────────┐
│   Review    │ → Human approval (optional)
└─────────────┘
     │
     ▼
┌─────────────┐
│   Send      │ → Deliver to customer
└─────────────┘
```

## Approaches

**Triage:**
- Rules: Fast, deterministic
- LLM: Flexible, contextual
- Hybrid: Rules for clear cases, LLM for edge cases

**Drafting:**
- Templates: Fast, consistent
- LLM: Natural, adaptive
- Hybrid: Template + LLM details

## Questions

- How much autonomy vs. human review?
- How to handle uncertainty?
- How to explain decisions?
