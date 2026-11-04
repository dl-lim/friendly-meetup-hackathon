# Hackathon Guidelines

Welcome to The Friendly Data Meetup's Hackathon. This session is made possible by CFC Underwriting.

The challenges before you today are open ended. You may bring your own perspective, your own tech stack, make your own assumptions about the data and collaborate with others on a project together

The key goal here is to learn, work with great people, and have fun.

This repository is for the Analytics project.

Please refer to https://github.com/dl-lim/friendly-hackathon-agentic-ai if you are after the Agentic AI Project.

When you have completed your work, open a PR to the repository.

**Disclaimer**  
The content and processes in this Hackathon are completely made up. Any similarities to real world processes are purely coincidental.

# Proactive Cyber Risk Analytics

Data visualization and insights exploration for a cyber insurance company's Proactive department which notifies customers about risks on their internet-facing assets.


## The Problem

The **Proactive** department identifies and notifies customers about cyber risks (e.g., Open RDP, CVEs, exposed databases) based on their internet assets (IP addresses, domains).

**Key questions teams struggle with:**
- Which customers are most exposed right now?
- Which asset types generate the most risk?
- What's the value of sending notifications for a given threat?
- Are we notifying customers too late, too often, or not clearly enough?

## Goal

Explore how **visualization and data storytelling** can make cyber risk more understandable and actionable. Focus on **insight and clarity**, not polished dashboards.

## Key Entities

- **Customers** — Organizations with cyber insurance (ID, sector)
- **Assets** — Internet-facing resources (IPs, domains, asset types)
- **Risks** — Security issues (type, severity, detection time)
- **Cases** — Work items tracking risks (status, creation/resolution time)
- **Notifications** — Customer communications (timestamp, time to notify)

## Dataset

`proactive_risk_data.csv` contains synthetic data:
- 200 risks across 50 customers
- 500 assets, 150 cases, 120 notifications
- 90 days of data

**Note:** Missing values are expected — not all risks become cases, not all cases get notifications. This is part of the real-world data story.

### Data Columns

Each row represents a risk detection. The columns are:

**Risk identification:**
- `risk_id` — Unique identifier for each risk
- `risk_type` — Type of security issue (e.g., "Open RDP", "Exposed Database", "Weak SSL/TLS", "CVE")
- `severity` — Risk severity level (Critical, High, Medium, Low)
- `detection_time` — When the risk was first detected (datetime)

**Asset information:**
- `asset_id` — Unique identifier for the internet-facing asset
- `asset_identifier` — The actual IP address or domain name
- `asset_type` — Type of asset (e.g., "Application Server", "Load Balancer", "Database Server")

**Customer information:**
- `customer_id` — Unique identifier for the customer organization
- `customer_name` — Customer name
- `sector` — Industry sector (e.g., "Healthcare", "Technology", "Retail", "Government")

**Case information (may be null):**
- `case_id` — Unique identifier if a case was created (null if no case)
- `status` — Case status (e.g., "Open", "Resolved") — only present if case exists
- `case_created` — When the case was created (datetime, null if no case)
- `resolution_time` — When the case was resolved (datetime, null if unresolved or no case)

**Notification information (may be null):**
- `notification_time` — When the customer was notified (datetime, null if not notified)
- `time_to_notify_hours` — Hours between detection and notification (null if not notified)

### Data Relationships

- Each risk is associated with one asset and one customer
- A risk may or may not have a case (case_id is null if no case was created)
- A case may or may not have a notification (notification_time is null if not notified)
- Cases can be Open or Resolved
- The workflow: Risk → (optional) Case → (optional) Notification

### Time Fields

All datetime columns are in ISO format. You can extract:
- Date components for daily/weekly/monthly analysis
- Time of day for hourly patterns
- Duration calculations (e.g., time between detection and case creation, case open duration)

## Exploration Ideas

### Questions to Explore

1. **Customer exposure**
   - Which customers have the most risks? Consider severity weighting.
   - Are there customers with multiple unresolved cases?
   - Which sectors are most exposed?

2. **Asset risk patterns**
   - Which asset types generate the most risk?
   - Are certain asset types associated with higher severity?
   - Do risks cluster by asset type or customer?

3. **Notification efficiency**
   - How long does it take to notify customers? What's the distribution?
   - Are critical risks notified faster than low-severity ones?
   - Which customers get notified fastest?

4. **Case lifecycle**
   - How long do cases stay open?
   - What's the resolution rate by severity or sector?
   - Are there patterns in case status over time?

5. **Temporal patterns**
   - Do risks cluster by time of day or day of week?
   - Are there trends in risk detection over the 90-day period?
   - Do certain risk types spike at specific times?

6. **Risk-to-case conversion**
   - What percentage of risks become cases?
   - Are certain risk types or severities more likely to become cases?
   - Which customers have risks that don't become cases?

## Tips

- **Start simple** — one question, one visualization
- **Focus on insights** — not perfection or polish
- **Explain your choices** — why did you visualize it that way?
- **Missing data is data** — use it to tell the story (not all risks become cases)
- **Collaborate** — discuss your visual choices and insights

---

*Synthetic dataset designed for exploration and discussion, not a finished product.*
