# Expected Synthetic Insight Outcomes

These fixtures are synthetic and deterministic. They are designed to make the ingestion and inference pipeline inspectable without private financial data.

## Persona Summary

| Persona | Strongest Demo Signal | Expected Data Sources |
|---|---|---|
| `p01` Jordan Lee | Burnout spending, subscription creep, payday surge | Bank, calendar, AI chat, email |
| `p03` Sasha Moreno | Cleanest stress-spend correlation story | Bank, calendar, AI chat, email |
| `p05` Theo Nakamura | Freelance invoice-rate risk plus stress spending | Bank, calendar, AI chat, email |

## Golden Outcomes

### `p01` Jordan Lee

- `stress_spend_correlation` should be high confidence with a positive stress/spend signal.
- `subscription_creep` should detect exactly three subscription-like recurring charges:
  - Figma Professional monthly subscription
  - Spotify monthly subscription
  - Netflix monthly subscription
- Rent, groceries, payroll, and other recurring non-subscription transactions should not appear as subscriptions.
- `post_payday_surge` should be detected because spend is intentionally concentrated after payroll deposits.
- `worry_timeline` should contain structured worry facts from synthetic AI-chat exports.

### `p03` Sasha Moreno

- `stress_spend_correlation` should be the clearest system-design demo path.
- `post_payday_surge` should be detected.
- `worry_timeline` should show multiple worry mentions, but with fewer signals than `p01` and `p05`.
- `subscription_creep` should detect exactly three professional/lifestyle subscriptions.

### `p05` Theo Nakamura

- `invoice_rate_risk` should be present and high confidence.
- The invoice extractor should produce four `invoice_payment` facts from email rows.
- Each invoice fact should include:
  - source type `email`
  - a stable `source_id`
  - amount `$750`
  - `15` hours
  - extraction confidence at or above `0.90`
- The deterministic rate rule should flag the invoices because `$750 / 15 hours = $50/hr`, below the `$65/hr` baseline.
- The expected estimated leakage is `$900` across the four synthetic invoices.

## Confidence And Provenance Contract

Every newly computed insight should include:

- `confidence.level` and `confidence.score`
- a human-readable `confidence.rationale`
- `provenance.source_types`
- `provenance.method`
- `provenance.source_record_counts`
- `provenance.evidence_refs` when source-level references are available

The trust framing is: LifeLedger does not ask the model to invent financial conclusions. It extracts typed facts, computes deterministic metrics, and uses grounded AI only for explanation.
