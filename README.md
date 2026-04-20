# Instant Refund Decision Engine

A prototype decision engine for e-commerce returns that determines refund outcomes at the moment of drop-off, rather than after warehouse inspection.

Built for HBS Digital Operations — Spring 2026.
Team: Mikel Acha, Taylor Joyce, Rahul Kilambi, Kolade Lawal, Kelly Petrino.

**Live demo: https://dig-ops-return-engine.streamlit.app/**

---

## What the App Does

The app demonstrates an alternative to the traditional e-commerce returns workflow, where customers drop off a return and wait days for a warehouse team to inspect it before a refund is issued. Instead, the engine makes a routing decision at the moment of drop-off — instantly approving low-risk returns and flagging high-risk ones for inspection.

It has four screens:

**Submit a Return** — The core demo. Select a customer from the mock database, select an item, and choose a return reason. The engine evaluates the request and returns a decision in real time, along with a score breakdown showing exactly how much each factor contributed. New submissions carry over to the dashboard within the same session.

**Dashboard** — An aggregate view of return activity. Shows KPI metrics (total returns, auto-approval rate, flagged rate, average risk score), a stacked bar chart of decisions broken down by return reason, a donut chart of returns by product category, a risk score distribution histogram with the approval threshold marked, and a filterable table of all return records.

**Score Explainer** — An interactive tool for understanding and stress-testing the engine's logic. Weight sliders let you adjust how much customer history, item risk, and return reason each contribute to the final score; an example scenario re-routes live as you drag. A threshold sensitivity chart shows how many of the 50 seeded returns would flip decision at each possible cutoff value. Includes a reference table of all return reason modifiers.

**Scenario Comparison** — Three contrasting returns shown side by side to illustrate what the engine discriminates on: a trusted customer with a defective low-value item (score ~13, auto-approved), a new account returning mid-value electronics with a discretionary reason (score ~48, flagged), and a fraud-flagged customer where a hard policy rule fires before scoring even begins.

---

## How the Engine Works

Every return is evaluated across three dimensions:

1. **Customer trust score (40%)** — Starts at 100. Penalized for high return rates, fraud flags, and new accounts. Rewarded for long tenure and high order volume. Inverted to a risk score before combining.
2. **Item risk score (35%)** — Starts at 0. Points added for higher price tier, riskier category (electronics > beauty > apparel > home goods > books), low resale viability, and older purchase dates.
3. **Return reason modifier (25%)** — Centers at 50. Defective and wrong-item returns are discounted (company fault). Changed-mind returns are penalized.

These combine into a composite risk score from 0–100. Below 45 → instant refund. At or above 45 → flagged for inspection.

Before scoring, four hard override rules apply regardless of score:
- 2+ fraud flags on account → always flag
- Item over $500 → always flag
- Item under $10 → always approve (inspection cost exceeds item value)
- Wrong item shipped → always approve (retailer error)

---

## From Prototype to Production

The engine logic is sound and would carry over to a real implementation. What's missing is everything around it.

**Data infrastructure**
The prototype runs on static CSVs with mock customers and items. A production system would connect to a live database — customer records, order history, item catalog — and compute trust scores from actual transaction history rather than hardcoded fields. Return rate would be calculated dynamically and updated as new returns come in.

**Calibrated scoring**
The weights (40/35/25) and threshold (45) are set by judgment. A real system would train on historical return outcomes to find the weights that minimize fraud loss while maximizing the auto-approval rate. The threshold would also be tunable by category or season rather than fixed globally.

**Closed-loop feedback**
Right now a decision is made and nothing happens next. A production system would track outcomes — did the auto-approved return turn out to be fraudulent? That signal feeds back into future scoring and keeps the model accurate over time.

**Operational integrations**
The engine would sit inside the retailer's existing returns portal, not as a standalone tool. Auto-approved decisions would trigger a refund API call directly. Flagged returns would create work orders in the warehouse management system. Customers would receive real-time notifications with their outcome.

**Inspection workflow**
Flagged returns need somewhere to go. A real system would include a queue interface for warehouse staff to process inspections, record outcomes, and escalate fraud cases — which in turn update the customer's fraud flag count.

**Monitoring**
A production deployment would track approval rates, fraud rates, inspection backlog, and cost savings over time. Alerting would fire if the auto-approval rate shifts unexpectedly, which could indicate model drift or a new fraud pattern.

---

## Running Locally

```bash
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

To verify the scoring logic without the UI:

```bash
python3 test_engine.py
```

---

## Demo Script

**Scenario A — Easy approve**
Customer: Sarah Chen · Item: Cotton T-Shirt · Reason: Defective
→ Score ~13, instant refund approved

**Scenario B — Flagged by score**
Customer: James Park · Item: Wireless Headphones · Reason: Changed mind
→ Score ~48, flagged for inspection

**Scenario C — Hard rule**
Customer: Alex M. · Item: anything · Reason: anything
→ Hard rule fires (2 fraud flags), flagged immediately — no score computed
