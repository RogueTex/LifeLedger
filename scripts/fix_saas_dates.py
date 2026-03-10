"""Fix SaaS subscription dates to monthly spacing for subscription detection."""
import json
import os
os.chdir('/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')

BASE = 'data/raw/persona_p03'
txns = [json.loads(l) for l in open(f'{BASE}/transactions.jsonl')]

# Remove any entries with id >= t_0122 (the quarterly ones we added)
txns = [t for t in txns if int(t['id'].replace('t_', '')) < 122]

notion_label = 'Notion \u2014 workspace subscription'
ynab_label = 'YNAB \u2014 budget tracking subscription'
dovetail_label = 'Dovetail \u2014 UX research repository'

months = ['01','02','03','04','05','06','07','08','09','10','11','12']

saas_subs = [
    (notion_label,   -16.00,  ['subscription','productivity','saas','recurring'],   '05'),
    (ynab_label,     -14.99,  ['subscription','budgeting','finances','saas','recurring'], '06'),
    (dovetail_label, -25.00,  ['subscription','work_tools','research','saas','recurring'], '07'),
]

new_txns = []
id_counter = 122
for label, amount, tags, day in saas_subs:
    for mo in months:
        new_txns.append({
            'id': f't_{id_counter:04d}',
            'ts': f'2024-{mo}-{day}T00:01:00-05:00',
            'source': 'transactions',
            'type': 'transaction',
            'text': label,
            'amount': amount,
            'tags': tags,
            'refs': [],
            'pii_level': 'synthetic',
        })
        id_counter += 1

txns.extend(new_txns)
with open(f'{BASE}/transactions.jsonl', 'w') as f:
    for t in txns:
        f.write(json.dumps(t) + '\n')
print(f'Transactions: {len(txns)} total ({len(new_txns)} SaaS monthly entries added)')
