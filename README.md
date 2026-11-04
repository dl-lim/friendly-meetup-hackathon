# Hackathon Guidelines

Welcome to The Friendly Data Meetup's Hackathon. This session is made possible by CFC Underwriting.

The challenges before you today are open ended. You may bring your own perspective, your own tech stack, make your own assumptions about the data and collaborate with others on a project together

The key goal here is to learn, work with great people, and have fun.

This repository is for the Agentic AI project.

Please refer to https://github.com/dl-lim/friendly-hackathon-analytics if you are after the Analytics Project.

When you have completed your work, open a PR to the repository. See [GitHub's guide on contributing to projects](https://docs.github.com/en/get-started/exploring-projects-on-github/contributing-to-a-project) for how to fork, make changes, and submit a PR

**Disclaimer**  
The content and processes in this Hackathon are completely made up. Any similarities to real world processes are purely coincidental.

# Proactive Risk Notification Agent

Design an **AI agent system** that helps a cyber insurance company notify customers about risks on their internet-facing assets.

## The Problem

**Proactive** department detects risks (CVEs, exposed services, KEVs) on customer assets (IPs, domains). They need to:
1. Triage: Is this a real risk? How severe?
2. Decide: Should we notify the customer?
3. Communicate: Draft a clear, actionable notification

## Goal

Build an agent (or agents) that:
- Ingests risk findings
- Reasons about severity, confidence, and customer context
- Decides whether to open a case
- Drafts customer-friendly notifications

Human-in-the-loop is encouraged.

## Quick Start

```bash
# Set up environment with uv
uv venv
uv pip install -e .

# Run the example
uv run python -m src.examples
```

## Data

See `data/sample_data.json` for:
- Customers (company, industry, risk profile)
- Assets (IP addresses, domains)
- Risk findings (type, severity, confidence, details)

## Key Questions

- What does "agentic" mean here? Single agent? Multiple agents?
- How do we prevent false positives?
- Rules, LLM, or hybrid approach?
- Where should humans review?

## Files

**These files are samples, and you may overwrite or make your own**
- `src/agent.py` - Agent stubs (triage, drafting)
- `src/data_loader.py` - Load sample data
- `src/examples.py` - Examples and experiments
- `ARCHITECTURE.md` - Architecture ideas

---

## A Note on "Agentic" AI

The current starter code in `src/agent.py` uses class names like `RiskTriageAgent` and `NotificationDraftingAgent`, but **the implementation is rule-based if/else logic**, not truly agentic behavior.

### What Makes Something "Agentic"?

True agentic AI typically includes:

1. **LLM-Powered Reasoning** - The agent uses a language model to think through problems, not hard-coded rules
2. **Tool Use** - The agent can call external tools/functions to gather information and take actions
3. **Observable Thinking** - You can see the agent's reasoning process, not just the final output
4. **Autonomous Decision-Making** - The agent decides what to do next based on context, not a fixed script

### The Gap in the Starter Code

```python
# Current approach (rule-based):
def should_open_case(self, finding, customer, asset):
    if severity in ['high', 'critical'] and confidence == 'high':
        return True
    return False

# Agentic approach (LLM-powered):
# The agent would:
# 1. Look up customer context using a tool
# 2. Research the CVE using a tool
# 3. Check industry threat intel using a tool
# 4. Reason about all the context
# 5. Make a decision with confidence level and explanation
```

### Making It Truly Agentic

Consider using a framework like **[Pydantic AI](https://ai.pydantic.dev/)** to build real agents:

```bash
uv pip install pydantic-ai
```

```python
from pydantic_ai import Agent

# Define structured output
class TriageDecision(BaseModel):
    should_notify: bool
    confidence: float
    reasoning: str

# Create an agent with tools
agent = Agent(
    'openai:gpt-4o-mini',
    result_type=TriageDecision,
    system_prompt="You are a security triage analyst..."
)

@agent.tool
def lookup_customer(customer_id: str) -> dict:
    """Look up customer profile and risk level."""
    return get_customer_by_id(customers, customer_id)

@agent.tool
def lookup_cve(cve_id: str) -> dict:
    """Get CVE details from vulnerability database."""
    # Query NVD or internal CVE database
    ...

# Run the agent - it will use tools and reason
result = agent.run_sync(f"Evaluate this finding: {finding}")
print(result.data.reasoning)  # See the agent's thinking!
```

### Hackathon Challenge

Your challenge: Transform this rule-based system into a truly agentic one! Consider:

- Which decisions benefit from LLM reasoning vs. simple rules?
- What tools should agents have access to?
- How do you make the agent's thinking visible?
- Where do humans need to stay in the loop?

Good luck!
