# Instant Refund Decision Engine

A prototype decision engine for e-commerce returns that determines refund outcomes at the moment of drop-off, rather than after warehouse inspection.

Built for HBS Digital Operations — Spring 2026. Team: Mikel Acha, Taylor Joyce, Rahul Kilambi, Kolade Lawal, Kelly Petrino.

---

## How to Run

```bash
pip install -r requirements.txt
streamlit run app.py
```

To verify the scoring logic in isolation:

```bash
python test_engine.py
```

---

## What's Been Built

### Decision Engine (`engine/`)

The core logic is complete and tested. All UI-independent.

- **`engine/models.py`** — `Customer`, `Item`, and `ReturnRequest` dataclasses. Computed properties handle `return_rate`, `price_tier`, and `trust_score` automatically.
- **`engine/scoring.py`** — Three scoring functions that combine into a final risk score (0–100):
  - Customer trust score (tenure, return rate, fraud flags)
  - Item risk score (price tier, category, resale viability, age)
  - Return reason modifier
  - Weighted composite: trust 40% / item 35% / reason 25%
  - Returns a full score breakdown dict for UI display
- **`engine/rules.py`** — Hard override rules applied before scoring: multiple fraud flags → always flag; item >$500 → always flag; item <$10 → always approve; wrong item shipped → always approve.

### Tests

- **`test_engine.py`** — Five hand-crafted scenarios covering the full risk spectrum (trusted customer, new account, fraud-flagged, high-value item, high return rate). All route correctly.

---

## Still To Build

**Day 2 — Mock data + Submit Return screen**
- `data/customers.csv` — 20 mock customers spanning full trust spectrum
- `data/items.csv` — 20 mock items across categories and price tiers
- `utils/data_loader.py` — CSV loading with Streamlit caching
- `ui/submit_return.py` — customer/item selector, return reason, decision result with score breakdown
- `app.py` — entry point with sidebar navigation (Screen 1 live)

**Day 3 — Dashboard**
- `scripts/generate_history.py` — generates 50 historical returns via the engine
- `data/returns_history.csv` — pre-seeded history for dashboard
- `ui/dashboard.py` — KPI metrics, charts by reason and category, filterable returns table

**Day 4 — Explainer + Polish**
- `ui/explainer.py` — interactive weight sliders, threshold sensitivity chart
- `ui/scenarios.py` — side-by-side scenario comparison (optional)
- Visual polish: color palette, page config, color-coded decision badges

**Day 5 — Screenshots + Prep**
- Capture screenshots of all screens for slide deck
- Demo walk-through of key scenarios (Scenario A/B/C)

---

## Key Dates

| Date | Milestone |
|------|-----------|
| Apr 15 | Progress report due — engine core complete |
| Apr 22 | Showcase — 10-min presentation |
| Apr 25 | Final submission (deck PDF + peer feedback poll) |
