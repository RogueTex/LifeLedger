import json, os, sys
os.chdir('/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')
sys.path.insert(0, '/Users/shruthisubramanian/Downloads/GENAI_1/lifeledger')

ins = json.load(open('outputs/insights_p03.json'))
corr_block = next(b for b in ins['insights'] if b['id'] == 'stress_spend_correlation')
ws = corr_block['weekly_series']

import statistics
spends = [w['weekly_discretionary_total'] for w in ws]
mean_s = statistics.mean(spends)
std_s = statistics.pstdev(spends)
print(f'Spend mean={mean_s:.2f} std={std_s:.2f}')
print(f'Spike threshold (1.5std): {mean_s + 1.5*std_s:.2f}')
print(f'Relaxed threshold (1.0std): {mean_s + 1.0*std_s:.2f}')
print()

week_map = {w['year_week']: w for w in ws}
print('Top spend weeks and their prior-week stress:')
for w in sorted(ws, key=lambda x: x['weekly_discretionary_total'], reverse=True)[:12]:
    yw = w['year_week']
    y, wn = yw.split('-')
    pw = f'{y}-{int(wn)-1:02d}'
    prev = week_map.get(pw, {})
    print(f'  {yw}: spend={w["weekly_discretionary_total"]:.2f}  stress={w["weekly_stress_avg"]:.3f}  prior={pw} prior_stress={prev.get("weekly_stress_avg", "N/A")}')

print()
print('High-stress weeks (top 25%) -- targets for recovery spending:')
stresses = sorted([w['weekly_stress_avg'] for w in ws], reverse=True)
q75 = stresses[len(stresses)//4]
print(f'  75th pct threshold: {q75:.3f}')
for w in sorted(ws, key=lambda x: x['weekly_stress_avg'], reverse=True)[:8]:
    yw = w['year_week']
    y, wn = yw.split('-')
    nw = f'{y}-{int(wn)+1:02d}'
    nxt = week_map.get(nw, {})
    print(f'  {yw}: stress={w["weekly_stress_avg"]:.3f}  spend={w["weekly_discretionary_total"]:.2f}  next={nw} next_spend={nxt.get("weekly_discretionary_total", "N/A")}')
