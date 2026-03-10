"""
Boost p03 demo quality:
1. Add 5 richer AI chat sessions with more worry/anxiety keywords
2. Add 3 SaaS subscriptions (Notion, YNAB, Dovetail) for cleaner subscription_creep story
"""
import json
import os
os.chdir('/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')

BASE = 'data/raw/persona_p03'

# ── 1. New conversations ─────────────────────────────────────────────────────
new_convs = [
    {
        "id": "c_0011",
        "ts": "2024-02-08T21:00:00-05:00",
        "source": "ai_chat",
        "type": "chat_turn",
        "text": (
            "USER: I just looked at my January bank statement and honestly felt sick. "
            "I spent way more on food delivery than I budgeted. My debt payoff plan is slipping. "
            "I know rent is fixed and the loan autopay is fixed — but the spend between paycheck "
            "and the next one just bleeds out. How do I get less anxious about money when the "
            "numbers are actually bad sometimes? "
            "ASSISTANT: The anxiety you're feeling is data, not failure. When the numbers come in "
            "worse than expected, the instinct is to look away — which is exactly when looking "
            "closely matters most. Try separating the emotion from the ledger: open the statement "
            "with a curious mindset, not a self-critical one. For the food delivery overage, the "
            "question isn't 'why did I do this again' but 'what week was it and what was happening.' "
            "Stress and isolation are expensive. Name the pattern so you can see it early next time. "
            "The debt is real but so is your income — you're not broke, you're just stressed. "
            "What's the actual gap between what you spent and what you planned?"
        ),
        "tags": ["money", "debt", "budget", "anxiety", "finances", "self_awareness"],
        "refs": ["t_0005", "t_0010"],
        "pii_level": "synthetic"
    },
    {
        "id": "c_0012",
        "ts": "2024-04-22T22:30:00-05:00",
        "source": "ai_chat",
        "type": "chat_turn",
        "text": (
            "USER: Got my tax refund and I'm torn — use it to pay a chunk of the student loan "
            "principal or add it to the emergency fund? I can't afford to do both meaningfully. "
            "On one hand the debt interest is eating me. On the other I have basically no financial "
            "cushion and that makes me really anxious every time a bill comes up. "
            "ASSISTANT: This is a real tradeoff and the 'right' answer depends on your actual anxiety "
            "threshold. If you're losing sleep over not having a cushion — if a $500 unexpected "
            "expense would send you into panic mode — the emergency fund comes first, because financial "
            "stress has real costs too. The loan interest is hurting you mathematically, but money "
            "anxiety has a compounding effect on decisions too. A practical split: put 60% toward "
            "the emergency fund until you hit $2,500 (your 'I won't spiral' number), then redirect "
            "everything to loan principal. What's the refund amount approximately?"
        ),
        "tags": ["money", "finances", "debt", "budget", "student_loans", "anxiety", "planning"],
        "refs": ["t_0010"],
        "pii_level": "synthetic"
    },
    {
        "id": "c_0013",
        "ts": "2024-08-14T21:30:00-05:00",
        "source": "ai_chat",
        "type": "chat_turn",
        "text": (
            "USER: The July sprint nearly broke me and I spent way too much on delivery and "
            "impulse buys that month. I want to actually reset financially in August — I keep "
            "saying that and not doing it. I'm worried I have a stress-spending problem that's "
            "deeper than just bad habits. Can you help me build a plan I'll actually follow? "
            "ASSISTANT: The fact that you're worried about it rather than dismissing it is the "
            "useful part. Stress-spending isn't a willpower failure — it's a coping loop: pressure "
            "builds, control feels absent, the purchase creates a momentary sense of agency. "
            "Knowing that doesn't make it stop, but it does point to the intervention. For August: "
            "instead of restricting, try redirecting. When the urge to order delivery hits, you can "
            "still spend — just move the budget line. Set a $200 'decompression fund' you're "
            "explicitly allowed to use on whatever feels good, guilt-free. Track it visibly. "
            "For the deeper pattern: what are the specific moments — time of day, what just happened — "
            "when you're most vulnerable to the impulse buy? Knowing the trigger window helps."
        ),
        "tags": ["stress_spending", "burnout", "money", "budget", "finances", "behavioral_patterns", "anxiety"],
        "refs": ["t_0067", "t_0069"],
        "pii_level": "synthetic"
    },
    {
        "id": "c_0014",
        "ts": "2024-11-15T22:00:00-05:00",
        "source": "ai_chat",
        "type": "chat_turn",
        "text": (
            "USER: I got the rate increase — 9%, not the 12% I asked for — and I'm trying to "
            "decide if I should push back or accept. Part of me is relieved just to have a number. "
            "Part of me knows I left money on the table again. My loans aren't going to pay "
            "themselves and my savings goal is still 14 months out. "
            "ASSISTANT: Nine percent on an 18-month-flat rate is real money. Don't underestimate it. "
            "That said, you're right that 9 vs 12 over a 6-month contract is meaningful — over a year "
            "that's roughly $2,000 in income difference. Whether to push depends on one thing: do you "
            "have a credible alternative? If yes, push gently for 11 and accept 10 if they hold. "
            "If no, take 9, bank the increase immediately into the emergency fund, and use the next "
            "cycle to come in anchored higher from day one. The pattern of undercharging is cumulative "
            "— each acceptance makes the next ask harder. What does your gut say about what the role "
            "is actually worth in the current market?"
        ),
        "tags": ["money", "career", "negotiation", "finances", "debt", "savings", "self_advocacy"],
        "refs": ["cal_0092", "e_0074"],
        "pii_level": "synthetic"
    },
    {
        "id": "c_0015",
        "ts": "2024-06-10T20:00:00-05:00",
        "source": "ai_chat",
        "type": "chat_turn",
        "text": (
            "USER: I keep comparing myself to a colleague who got converted to full-time. Same work, "
            "different status. She has benefits. I don't. Her financial stress is different from mine — "
            "predictable paycheck, no contract anxiety, probably no budget panic when a gap appears. "
            "I'm not sure if I'm actually undervaluing myself or if this is just imposter syndrome talking. "
            "ASSISTANT: Both can be true. Imposter syndrome tends to attack the most competent people "
            "because they're the ones aware enough to see their own gaps. But 'I don't deserve more' "
            "and 'I might be undercharging' are different questions. The comparison to your colleague "
            "is useful data: if her work and yours are equivalent and her full-time rate is $X, "
            "you're almost certainly undercharging on your contract because contractors should earn "
            "a premium to compensate for the instability and lack of benefits. The anxiety about "
            "money isn't irrational — variable income is genuinely stressful and your nervous system "
            "is correct that the risk is asymmetric. The question is whether the contract arrangement "
            "is still worth the tradeoff for you."
        ),
        "tags": ["imposter_syndrome", "self_doubt", "career", "money", "contract", "anxiety", "finances"],
        "refs": [],
        "pii_level": "synthetic"
    },
]

convs = [json.loads(l) for l in open(f'{BASE}/conversations.jsonl')]
convs.extend(new_convs)
with open(f'{BASE}/conversations.jsonl', 'w') as f:
    for c in convs:
        f.write(json.dumps(c) + '\n')
print(f'Conversations: {len(convs)} total ({len(new_convs)} added)')

# ── 2. New SaaS subscriptions ─────────────────────────────────────────────────
# 3 tools × 4 monthly occurrences each = 12 new transactions → max ID 133
new_txns = []
saas = [
    ("t_0122", "t_0123", "t_0124", "Notion — workspace subscription", -16.00,
     ["subscription", "productivity", "saas", "recurring"],
     ["2024-01-05T00:01:00-05:00", "2024-04-05T00:01:00-05:00",
      "2024-07-05T00:01:00-05:00", "2024-10-05T00:01:00-05:00"]),
    ("t_0126", "t_0127", "t_0128", "YNAB — budget tracking subscription", -14.99,
     ["subscription", "budgeting", "finances", "saas", "recurring"],
     ["2024-01-06T00:01:00-05:00", "2024-04-06T00:01:00-05:00",
      "2024-07-06T00:01:00-05:00", "2024-10-06T00:01:00-05:00"]),
    ("t_0130", "t_0131", "t_0132", "Dovetail — UX research repository subscription", -25.00,
     ["subscription", "work_tools", "research", "saas", "recurring"],
     ["2024-01-07T00:01:00-05:00", "2024-04-07T00:01:00-05:00",
      "2024-07-07T00:01:00-05:00", "2024-10-07T00:01:00-05:00"]),
]
# Build IDs sequentially
id_counter = 122
for _, _, _, label, amount, tags, dates in saas:
    for i, ts in enumerate(dates):
        new_txns.append({
            "id": f"t_{id_counter:04d}",
            "ts": ts,
            "source": "transactions",
            "type": "transaction",
            "text": label,
            "amount": amount,
            "tags": tags,
            "refs": [],
            "pii_level": "synthetic"
        })
        id_counter += 1

txns = [json.loads(l) for l in open(f'{BASE}/transactions.jsonl')]
txns.extend(new_txns)
with open(f'{BASE}/transactions.jsonl', 'w') as f:
    for t in txns:
        f.write(json.dumps(t) + '\n')
print(f'Transactions: {len(txns)} total ({len(new_txns)} added)')
print('Done.')
