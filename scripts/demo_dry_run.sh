#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
START_TS="$(date +%s)"

cat <<'EOF'
LifeLedger 2-minute dry run

Exact click flow:
1. Launch app: streamlit run src/ui/app.py
2. Sidebar -> Persona: select "Jordan Lee — Burnout + Home Savings" (p01)
3. Scroll through:
   - KPI cards (correlation/months/themes)
   - Stress vs Discretionary Spend chart
   - First spike expander with threshold math + evidence
   - Data Story + Consent card
4. In chat input ask exactly:
   "What week had the highest discretionary spend, what was the prior-week stress, and what should I do next?"
5. Sidebar -> Persona: select "Theo Nakamura — Freelancer Business Brain" (p05)
6. Confirm Freelancer Rate Signal section and at least one evidence bullet.
7. Ask exactly:
   "Do I have any undercharging signal and what is the estimated dollar impact?"

Pass criteria:
- Both persona paths render without errors.
- p01 shows non-trivial stress/spend coefficient and spike evidence.
- p05 shows rate signal card (flagged or explicit not-found language).
EOF

ELAPSED=$(( $(date +%s) - START_TS ))
REMAINING=$(( 120 - ELAPSED ))
if [ "$REMAINING" -gt 0 ]; then
  echo "\nTime budget remaining after checklist print: ${REMAINING}s"
else
  echo "\nTime budget exceeded while reading checklist."
fi
