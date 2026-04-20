# Instant Refund Decision Engine

A prototype decision engine for e-commerce returns that determines refund outcomes at the moment of drop-off, rather than after warehouse inspection.

Built for HBS Digital Operations — Spring 2026.
Team: Mikel Acha, Taylor Joyce, Rahul Kilambi, Kolade Lawal, Kelly Petrino.

---

## How to Run

```bash
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

Then open http://localhost:8501 in your browser.

To verify the scoring logic in isolation (no UI required):

```bash
python3 test_engine.py
```

---

## How It Works

The engine evaluates every return request against three inputs:

1. **Customer trust score** — account tenure, return rate, fraud flags
2. **Item risk score** — price tier, category, resale viability, days since purchase
3. **Return reason modifier** — defective/wrong item reduce risk; changed mind increases it

These combine into a weighted composite risk score (0–100). Returns below 45 are auto-approved for an instant refund; at or above 45 they're flagged for inspection.

Before scoring, four hard override rules apply:
- 2+ fraud flags → always flag
- Item over $500 → always flag
- Item under $10 → always approve
- Wrong item shipped → always approve (retailer error)

---

## Screens

**Submit a Return** — Select a customer and item, choose a return reason, and submit. The engine displays the decision instantly with a full score breakdown showing how each component contributed.

**Dashboard** — Aggregate view of all returns: KPI metrics (total, auto-approved %, flagged %, avg risk score), decisions by return reason, returns by category, risk score distribution with the threshold marked, and a filterable returns table.

**Score Explainer** — Interactive weight sliders let you adjust how much customer history, item risk, and return reason each contribute. The example scenario re-routes live. A threshold sensitivity chart shows how many returns would flip decision at each cutoff value.

**Scenario Comparison** — Three contrasting returns side by side: a trusted customer with a defective item (auto-approved, score ~13), a new account with electronics and a changed-mind reason (flagged, score ~48), and a fraud-flagged customer where the hard rule fires before scoring even starts.

---

## Project Structure

```
dig_ops/
├── app.py                    # Streamlit entry point + sidebar navigation
├── requirements.txt
├── test_engine.py            # Standalone scoring smoke tests
│
├── engine/
│   ├── models.py             # Customer, Item, ReturnRequest dataclasses
│   ├── scoring.py            # Trust score, item risk, composite score, routing
│   └── rules.py              # Hard override rules
│
├── data/
│   ├── customers.csv         # 20 mock customers spanning full trust spectrum
│   ├── items.csv             # 20 mock items across categories and price tiers
│   └── returns_history.csv   # 50 pre-seeded historical returns for dashboard
│
├── ui/
│   ├── submit_return.py      # Screen 1: submit a return and see decision
│   ├── dashboard.py          # Screen 2: aggregate returns dashboard
│   ├── explainer.py          # Screen 3: interactive weight and threshold explorer
│   └── scenarios.py          # Screen 4: side-by-side scenario comparison
│
├── utils/
│   ├── data_loader.py        # Cached CSV loading
│   └── formatters.py         # Color badges and score labels
│
└── scripts/
    └── generate_history.py   # Regenerates returns_history.csv via the engine
```

---

## Demo Script

Three scenarios to walk through live:

**Scenario A — Easy approve**
Customer: Sarah Chen · Item: Cotton T-Shirt · Reason: Defective
→ Expected: score ~13, instant refund approved

**Scenario B — Flagged by score**
Customer: James Park · Item: Wireless Headphones · Reason: Changed mind
→ Expected: score ~48, flagged for inspection

**Scenario C — Hard rule**
Customer: Alex M. · Item: anything · Reason: anything
→ Expected: hard rule fires (2 fraud flags), flagged immediately — no score shown
