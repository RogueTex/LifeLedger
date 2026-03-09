import json
import sys
import os
os.chdir('/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')
sys.path.insert(0, '/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')

BASE = 'data/raw/persona_p03'

# FIX 1: transactions.jsonl — strip "(monthly)" from income lines
txns = [json.loads(l) for l in open(f'{BASE}/transactions.jsonl')]
fixed_txns = []
for t in txns:
    if t.get('amount', 0) > 0:
        t['text'] = t['text'].replace(' (monthly)', '')
        t['text'] = t['text'].replace('(monthly)', '')
        t['text'] = t['text'].replace(' (monthly, pre-raise rate)', '')
        t['text'] = t['text'].replace(' (biweekly deposit)', '')
    fixed_txns.append(t)

with open(f'{BASE}/transactions.jsonl', 'w') as f:
    for t in fixed_txns:
        f.write(json.dumps(t) + '\n')
print(f'Transactions fixed: {len(fixed_txns)} records')

# FIX 2: persona_profile.json — add savings fields
with open(f'{BASE}/persona_profile.json') as f:
    profile = json.load(f)

profile['savings_goal'] = 12000
profile['current_savings'] = 1200
profile['avg_net_monthly_savings'] = 633

with open(f'{BASE}/persona_profile.json', 'w') as f:
    json.dump(profile, f, indent=2)
print('Profile updated with savings fields')

# FIX 3: calendar.jsonl — add stress-keyword events for Q2-Q4 spending spike weeks
cal = [json.loads(l) for l in open(f'{BASE}/calendar.jsonl')]

new_events = [
    # Week 19 (May 5-11): contract gap / renewal anxiety -> DoorDash + ASOS spike
    {"id": "cal_0081", "ts": "2024-05-07T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Contract renewal review — pending decision (1:1 with Marcus)",
     "tags": ["work", "contract_renewal", "deadline", "stress"],
     "refs": ["e_0046"], "pii_level": "synthetic"},
    {"id": "cal_0082", "ts": "2024-05-08T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Freelance study facilitation pitch — demo deck review",
     "tags": ["work", "freelance", "presentation", "demo"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0083", "ts": "2024-05-09T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Portfolio presentation prep — independent consultancy pitch deadline",
     "tags": ["work", "career", "presentation", "deadline"],
     "refs": [], "pii_level": "synthetic"},

    # Week 29 (Jul 14-20): clinician dashboard sprint delivery
    {"id": "cal_0084", "ts": "2024-07-15T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Clinician dashboard synthesis — final review pass (deadline)",
     "tags": ["work", "deadline", "sprint", "stress"],
     "refs": ["ll_0087"], "pii_level": "synthetic"},
    {"id": "cal_0085", "ts": "2024-07-16T13:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Stakeholder presentation — research readout demo",
     "tags": ["work", "presentation", "demo", "deadline"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0086", "ts": "2024-07-17T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Launch review — 1:1 with PM on feature go/no-go",
     "tags": ["work", "launch", "review", "1:1"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0087", "ts": "2024-07-18T15:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Post-sprint OKR check — retrospective with lead",
     "tags": ["work", "okr", "sprint", "review"],
     "refs": [], "pii_level": "synthetic"},

    # Week 37 (Sep 8-14): dual-track sprint, overcommitted
    {"id": "cal_0088", "ts": "2024-09-09T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Fall research kickoff — dual-track deadline week begins",
     "tags": ["work", "deadline", "sprint", "stress", "overload"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0089", "ts": "2024-09-10T13:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Interview synthesis presentation — patterns delivery demo",
     "tags": ["work", "presentation", "demo", "deadline"],
     "refs": ["ll_0109"], "pii_level": "synthetic"},
    {"id": "cal_0090", "ts": "2024-09-11T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "1:1 with research lead — performance check mid-cycle",
     "tags": ["work", "1:1", "review", "performance"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0091", "ts": "2024-09-12T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Project launch review — go/no-go for next sprint phase",
     "tags": ["work", "launch", "review", "deadline"],
     "refs": [], "pii_level": "synthetic"},

    # Week 45 (Nov 3-9): contract renewal anxiety
    {"id": "cal_0092", "ts": "2024-11-04T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Contract renewal 1:1 — 6-month performance review (Marcus)",
     "tags": ["work", "contract_renewal", "1:1", "review", "stress"],
     "refs": ["e_0074", "ll_0131"], "pii_level": "synthetic"},
    {"id": "cal_0093", "ts": "2024-11-05T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "Rate negotiation prep — reviewing market benchmarks (deadline)",
     "tags": ["work", "rate_negotiation", "deadline", "career"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0094", "ts": "2024-11-06T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event", "text": "OKR review — Q4 research performance presentation to stakeholders",
     "tags": ["work", "okr", "presentation", "review", "performance"],
     "refs": [], "pii_level": "synthetic"},
]

cal.extend(new_events)
with open(f'{BASE}/calendar.jsonl', 'w') as f:
    for e in cal:
        f.write(json.dumps(e) + '\n')
print(f'Calendar updated: {len(cal)} total events ({len(new_events)} new stress events added)')
print('All fixes applied successfully.')
