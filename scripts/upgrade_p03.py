"""
upgrade_p03.py — Boost p03 persona data quality for maximum demo impact.

Changes:
1. Calendar: add 4 high-stress-keyword events each to weeks 2024-18, 2024-28, 2024-36
   (the prior weeks to the 3 biggest spending spikes) so spike detection fires 3x.
2. Transactions: add recovery-spending transactions to weeks 2024-31, 2024-39, 2024-41
   (weeks AFTER the biggest stress periods) so recovery_spending shows 150%+ jump.
3. Conversations: add 4 dense sessions with money/burnout/debt/anxiety/overwhelm keywords
   to boost top_anxiety_themes from 3-4 counts to 10+ and worry_timeline from 7 to 11+.
"""
import json
import os
import sys

os.chdir('/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')
sys.path.insert(0, '/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')

BASE = 'data/raw/persona_p03'

# ─────────────────────────────────────────────────────────────────
# 1. CALENDAR: prior-week stress boosts
# ─────────────────────────────────────────────────────────────────
# Week 2024-18 = ISO Apr 29 – May 5, 2024 (prior to spend spike in 2024-19, $209)
# Week 2024-28 = ISO Jul 8  – Jul 14, 2024 (prior to spend spike in 2024-29, $287)
# Week 2024-36 = ISO Sep 2  – Sep 8,  2024 (prior to spend spike in 2024-37, $284)
new_cal = [
    # ── Week 2024-18: Apr 29 – May 5 ──
    {"id": "cal_0095", "ts": "2024-04-29T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Q1 research synthesis deadline — final presentation to product team",
     "tags": ["work", "deadline", "presentation", "sprint"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0096", "ts": "2024-04-30T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "1:1 with Marcus — contract performance review and status check",
     "tags": ["work", "1:1", "review", "performance", "contract_renewal"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0097", "ts": "2024-05-01T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Launch review — research delivery demo to executive stakeholders",
     "tags": ["work", "launch", "demo", "deadline"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0098", "ts": "2024-05-02T13:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "OKR mid-cycle review — Q2 research roadmap presentation (deadline)",
     "tags": ["work", "okr", "presentation", "review", "deadline"],
     "refs": [], "pii_level": "synthetic"},

    # ── Week 2024-28: Jul 8 – Jul 14 ──
    {"id": "cal_0099", "ts": "2024-07-08T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Pre-sprint review — clinician dashboard deadline prep (1:1 with PM)",
     "tags": ["work", "1:1", "review", "deadline", "sprint"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0100", "ts": "2024-07-09T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Sprint deadline kickoff — synthesis presentation draft due today",
     "tags": ["work", "deadline", "presentation", "sprint"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0101", "ts": "2024-07-10T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Feature launch OKR check — performance review for research pipeline",
     "tags": ["work", "launch", "okr", "performance", "review"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0102", "ts": "2024-07-11T13:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Demo prep — final delivery presentation rehearsal (deadline Friday)",
     "tags": ["work", "demo", "presentation", "deadline"],
     "refs": [], "pii_level": "synthetic"},

    # ── Week 2024-36: Sep 2 – Sep 8 ──
    {"id": "cal_0103", "ts": "2024-09-02T09:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Q3 research launch review — sprint deadline week begins",
     "tags": ["work", "launch", "review", "deadline", "sprint"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0104", "ts": "2024-09-03T14:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "Dual-track sprint deadline — synthesis presentation delivery due",
     "tags": ["work", "deadline", "presentation", "sprint", "overload"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0105", "ts": "2024-09-04T10:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "1:1 with research lead — performance review and overcommitment check",
     "tags": ["work", "1:1", "review", "performance"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "cal_0106", "ts": "2024-09-05T13:00:00-05:00", "source": "calendar",
     "type": "calendar_event",
     "text": "OKR go/no-go demo — September launch decision presentation",
     "tags": ["work", "okr", "demo", "presentation", "deadline"],
     "refs": [], "pii_level": "synthetic"},
]

cal = [json.loads(l) for l in open(f'{BASE}/calendar.jsonl')]
cal.extend(new_cal)
with open(f'{BASE}/calendar.jsonl', 'w') as f:
    for e in cal:
        f.write(json.dumps(e) + '\n')
print(f'Calendar: {len(cal)} total ({len(new_cal)} added for prior-week stress boost)')


# ─────────────────────────────────────────────────────────────────
# 2. TRANSACTIONS: recovery-spending weeks after high-stress periods
# ─────────────────────────────────────────────────────────────────
# Week 2024-31 = ISO Jul 29 – Aug 4, 2024  (after Jul 22-26 delivery crunch)
# Week 2024-39 = ISO Sep 23 – Sep 29, 2024 (after Sep 9-15 dual-track sprint)
# Week 2024-41 = ISO Oct 7  – Oct 13, 2024 (after Sep 30 - Oct 6 crunch window)
new_txns = [
    # ── Recovery week 2024-31 (Jul 29 – Aug 4): post-delivery decompression ──
    {"id": "t_0122", "ts": "2024-07-30T19:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — post-sprint dinner delivery (finally hit DELIVER, decompressing)",
     "amount": -78.44,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery", "decompression"],
     "refs": ["ll_0092"], "pii_level": "synthetic"},
    {"id": "t_0123", "ts": "2024-07-31T20:30:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — second delivery night (recovery mode, treating myself)",
     "amount": -64.22,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0124", "ts": "2024-08-01T14:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "ASOS — summer dress (post-sprint reward buy, felt justified after crunch)",
     "amount": -98.00,
     "tags": ["shopping", "clothing", "asos", "discretionary", "impulse", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0125", "ts": "2024-08-02T12:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "Novo Coffee — long catch-up with friend (first social outing post-sprint)",
     "amount": -22.50,
     "tags": ["coffee", "social", "cafe", "discretionary"],
     "refs": [], "pii_level": "synthetic"},

    # ── Recovery week 2024-39 (Sep 23–29): post-dual-track sprint decompression ──
    {"id": "t_0126", "ts": "2024-09-23T19:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — post-burnout dinner binge (September finally over)",
     "amount": -91.33,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery", "stress_spend"],
     "refs": ["c_0012"], "pii_level": "synthetic"},
    {"id": "t_0127", "ts": "2024-09-24T21:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — third consecutive delivery night (decompression continues)",
     "amount": -67.88,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0128", "ts": "2024-09-25T15:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "Target — home items (impulse, post-sprint decompression shopping run)",
     "amount": -76.44,
     "tags": ["shopping", "target", "discretionary", "impulse", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0129", "ts": "2024-09-27T12:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "Novo Coffee — brunch with Priya (first social post-September crunch)",
     "amount": -34.99,
     "tags": ["coffee", "social", "cafe", "discretionary"],
     "refs": [], "pii_level": "synthetic"},

    # ── Recovery week 2024-41 (Oct 7–13): moderate rebound after Oct crunch ──
    {"id": "t_0130", "ts": "2024-10-07T19:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — delivery (recovery from a heavy contract-check week)",
     "amount": -54.22,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0131", "ts": "2024-10-09T15:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "ASOS — fall sweater (impulse comfort buy, reward for surviving October)",
     "amount": -72.00,
     "tags": ["shopping", "clothing", "asos", "discretionary", "impulse", "recovery"],
     "refs": [], "pii_level": "synthetic"},
    {"id": "t_0132", "ts": "2024-10-10T20:00:00-05:00", "source": "transactions",
     "type": "transaction",
     "text": "DoorDash — late delivery (quiet Thursday, treating myself)",
     "amount": -44.55,
     "tags": ["food_delivery", "doordash", "discretionary", "recovery"],
     "refs": [], "pii_level": "synthetic"},
]

txns = [json.loads(l) for l in open(f'{BASE}/transactions.jsonl')]
txns.extend(new_txns)
with open(f'{BASE}/transactions.jsonl', 'w') as f:
    for t in txns:
        f.write(json.dumps(t) + '\n')
print(f'Transactions: {len(txns)} total ({len(new_txns)} added for recovery spending weeks)')


# ─────────────────────────────────────────────────────────────────
# 3. CONVERSATIONS: dense anxiety / burnout / money sessions
# ─────────────────────────────────────────────────────────────────
new_convos = [
    # ── c_0011: Jul 29 (recovery week 2024-31, post sprint) ──
    {"id": "c_0011", "ts": "2024-07-29T21:00:00-05:00", "source": "conversations",
     "type": "ai_conversation",
     "text": (
         "USER: I just finished the biggest sprint of my contract cycle and I'm exhausted. "
         "Like genuinely burned out. And somehow I ended up spending $300+ this week — DoorDash "
         "every night, some impulse ASOS thing. I feel like stress turns me into a totally "
         "different person with money. "
         "ASSISTANT: That's a real pattern — when we experience sustained pressure and finally "
         "cross the finish line, the nervous system looks for relief. Food delivery and low-effort "
         "purchases become stress valves. The money piece is important: how does it land after? "
         "USER: Like guilt. I have $22k in loans and a $12k savings goal and I'm spending $90 "
         "on DoorDash when I could be paying extra toward my debt. The budget math doesn't feel "
         "like math anymore — it feels personal. "
         "ASSISTANT: That's the key distinction. The budget guilt compounds the burnout. What would "
         "it look like to give yourself one recovery day without thinking about money at all, while "
         "also setting a spending boundary you feel okay with? "
         "USER: I need to sit with how burnout and money anxiety feed each other. When I'm "
         "stressed about work I spend more, and then I'm stressed about money, and the cycle "
         "continues. The debt is a weight I carry and I barely feel it until I'm also burned out."
     ),
     "tags": ["burnout", "money", "debt", "stress", "spending_habits", "self_awareness"],
     "refs": ["t_0122", "t_0123", "t_0124", "cal_0084"],
     "pii_level": "synthetic"},

    # ── c_0012: Sep 26 (recovery week 2024-39, post dual-track sprint) ──
    {"id": "c_0012", "ts": "2024-09-26T20:00:00-05:00", "source": "conversations",
     "type": "ai_conversation",
     "text": (
         "USER: September overwhelmed me completely. I overbooked, got burned out, and I can "
         "feel I'm stress-spending again — DoorDash every night, a Target run I barely remember, "
         "lots of online browsing. I'm anxious about money AND I'm anxious about how I deal with "
         "anxiety. It's a loop I can't seem to break. "
         "ASSISTANT: The loop you're describing — anxiety leads to impulse spending leads to guilt "
         "leads to more anxiety — is very common. What triggered the overcommitment this time? "
         "USER: The dual-track sprint plus contract renewal prep layered on top of each other. I "
         "was too overwhelmed to say no to anything. The stress made everything feel urgent and I "
         "couldn't protect my time or my budget. "
         "ASSISTANT: That's the overwhelm trap. When everything feels urgent, the nervous system "
         "can't prioritize properly. The stressed-spending is the nervous system finding comfort. "
         "How do you feel now that September is actually wrapping up? "
         "USER: Tired. Worried about money — I know I blew my savings target this month. "
         "Burned out but trying not to be too harsh on myself. I have goals: emergency fund, "
         "student debt payoff. But burnout makes those goals feel impossibly far away."
     ),
     "tags": ["burnout", "anxiety", "overwhelm", "money", "stress", "spending_habits"],
     "refs": ["t_0126", "t_0127", "t_0128", "cal_0088"],
     "pii_level": "synthetic"},

    # ── c_0013: Oct 15 (week 2024-42, debt + career reality check) ──
    {"id": "c_0013", "ts": "2024-10-15T19:00:00-05:00", "source": "conversations",
     "type": "ai_conversation",
     "text": (
         "USER: I want to map out my money situation with fresh eyes. Student debt is at $22k "
         "remaining. My HYSA emergency fund is at about $5,400 now which feels meaningful, but "
         "I still have this background money anxiety that never fully turns off. Career-wise I'm "
         "thinking about whether to stay a contractor or push toward going independent. "
         "ASSISTANT: That's a lot of financial and career weight to carry simultaneously. The HYSA "
         "progress is real — you've grown it from $1,200. What does the background money anxiety "
         "actually look like for you on a normal day? "
         "USER: A low hum. I know roughly what my income is, but there's always fear that the "
         "contract won't renew, that I'll have a gap, that I'll stress-spend too much in a bad "
         "week and blow my savings target. The debt is always there — $412 a month toward loans "
         "is a lot when you're also trying to save. "
         "ASSISTANT: That's anticipatory money anxiety. It's not about what's happening now, "
         "it's about what could happen. The contract-cycle structure amplifies it — uncertainty "
         "is literally built into your income. Going independent might feel like more career "
         "control, but potentially worse money anxiety until you have a stable client base. "
         "USER: Exactly. The career ambition and the money anxiety are sort of the same thing. "
         "I need to separate what I'm scared of from what I actually want."
     ),
     "tags": ["debt", "career", "money", "planning", "anxiety", "self_awareness"],
     "refs": ["t_0130", "t_0131"],
     "pii_level": "synthetic"},

    # ── c_0014: Nov 20 (week 2024-47, post-negotiation + year-end money/burnout) ──
    {"id": "c_0014", "ts": "2024-11-20T20:00:00-05:00", "source": "conversations",
     "type": "ai_conversation",
     "text": (
         "USER: I got the rate increase — contract renewed at $7,600/month. I'm proud and "
         "also aware of how much the anxiety of negotiating completely drained me. It was "
         "burnout-inducing just to advocate for myself. "
         "ASSISTANT: That tension is real. Negotiating your own worth while running on low energy "
         "is one of the hardest asks in a contractor's career. How does it feel now that it's done? "
         "USER: Relieved and a bit numb. Also I noticed I spent way more on DoorDash and impulse "
         "buys during the negotiation week than any other week this month — money anxiety means "
         "spend more, not less. The stress makes me worse at managing money precisely when I need "
         "to be better at it. "
         "ASSISTANT: There's real irony there: the weeks you're most worried about money and feeling "
         "financially precarious are also the weeks you spend the most. It's the nervous system "
         "finding definite small comforts when the big financial picture feels scary. "
         "USER: I want to build better habits around this. My career goal is independent "
         "consultancy. My money goal is the emergency fund and paying down debt. But I know "
         "now that burnout and money anxiety are the things that will slow me down most — "
         "the stressed-spend-guilt cycle is the real obstacle."
     ),
     "tags": ["money", "career", "burnout", "self_advocacy", "anxiety", "finances"],
     "refs": ["e_0074", "cal_0092"],
     "pii_level": "synthetic"},
]

convos = [json.loads(l) for l in open(f'{BASE}/conversations.jsonl')]
convos.extend(new_convos)
with open(f'{BASE}/conversations.jsonl', 'w') as f:
    for c in convos:
        f.write(json.dumps(c) + '\n')
print(f'Conversations: {len(convos)} total ({len(new_convos)} added for theme/worry boost)')

print('\nAll upgrades applied.')
