import pandas as pd, numpy as np
d = pd.read_csv('data_raw/raw_polls.csv')
print(d.partisan.value_counts(dropna=False).head())
d = d[d.type_simple.isin(['Sen-G','Gov-G','Pres-G'])].copy()
d = d[(d.time_to_election<=21)]
def orient(r):
    if r.cand1_party=='DEM' and r.cand2_party=='REP': s=1
    elif r.cand1_party=='REP' and r.cand2_party=='DEM': s=-1
    else: return pd.Series([np.nan]*2)
    pd_ = r.cand1_pct if s==1 else r.cand2_pct; pr = r.cand2_pct if s==1 else r.cand1_pct
    ad = r.cand1_actual if s==1 else r.cand2_actual; ar = r.cand2_actual if s==1 else r.cand1_actual
    return pd.Series([100*(pd_-pr)/(pd_+pr), 100*(ad-ar)/(ad+ar)])
d[['pm2','am2']] = d.apply(orient, axis=1)
d = d.dropna(subset=['pm2','am2'])
d = d[(d.location.str.len()==2)&(d.location!='US')]
# partisan bias toward sponsor
d['race_pm_mean'] = d.groupby('race_id').pm2.transform('mean')
for p in ['D','R']:
    s = d[d.partisan==p]; dev = (s.pm2 - s.race_pm_mean) * (1 if p=='D' else -1)
    print('sponsor',p,'n',len(s),'mean deviation toward sponsor vs race mean', round(dev.mean(),2), 'median', round(dev.median(),2))
# race-level avg
for cycles in [[2016,2018,2020,2022],[2018,2022]]:
    r = d[d.cycle.isin(cycles)].groupby(['cycle','location','race_id']).agg(pm=('pm2','mean'),am=('am2','mean'),n=('pm2','size')).reset_index()
    # regress actual on poll avg with cycle fixed effects
    X = np.column_stack([r.pm]+[ (r.cycle==c).astype(float) for c in cycles])
    beta,*_ = np.linalg.lstsq(X, r.am, rcond=None)
    print(cycles,'beta on poll margin', round(beta[0],3), 'cycle intercepts (actual - beta*poll) ', np.round(beta[1:],2))
    comp = r[r.pm.abs()<15]
    X = np.column_stack([comp.pm]+[ (comp.cycle==c).astype(float) for c in cycles])
    b2,*_ = np.linalg.lstsq(X, comp.am, rcond=None)
    print('   competitive (|poll|<15) beta', round(b2[0],3), np.round(b2[1:],2), 'n', len(comp))
cycles=[2016,2018,2020,2022]
r = d[d.cycle.isin(cycles)].groupby(['cycle','location','race_id']).agg(pm=('pm2','mean'),am=('am2','mean')).reset_index()
X = np.column_stack([r.pm]+[ (r.cycle==c).astype(float) for c in cycles])
beta,*_ = np.linalg.lstsq(X, r.am, rcond=None)
r['resid'] = r.am - X@beta     # + = Dems did better than (scaled) polls -> polls underestimated D
se = r.groupby('location').resid.agg(['mean','count','std'])
se['shrunk'] = se['mean']*se['count']/(se['count']+4)
se.to_csv('state_resid.csv')
print(se.round(2).sort_values('mean').to_string())
print('resid sd', r.resid.std().round(2), 'corr check')
# persistence: correlate state resid in 2016+2020 vs 2018+2022
a = r[r.cycle.isin([2016,2018])].groupby('location').resid.mean(); b = r[r.cycle.isin([2020,2022])].groupby('location').resid.mean()
j = pd.concat([a,b],axis=1).dropna(); print('persistence corr (16/18 vs 20/22):', round(j.corr().iloc[0,1],2), 'n', len(j))
a = r[r.cycle.isin([2016,2020])].groupby('location').resid.mean(); b = r[r.cycle.isin([2018,2022])].groupby('location').resid.mean()
j = pd.concat([a,b],axis=1).dropna(); print('persistence corr (pres vs mid):', round(j.corr().iloc[0,1],2), 'n', len(j))
# national cycle bias on 2-party margins (race-level mean of poll - actual)
r['err'] = r.pm - r.am
print('cycle mean err (poll-actual, + = D overstated):', r.groupby('cycle').err.mean().round(2).to_dict(), ' SD across cycles:', round(r.groupby('cycle').err.mean().std(),2))
print('within-cycle race-level error SD (after removing cycle mean):', round((r.err - r.groupby('cycle').err.transform('mean')).std(),2))
comp = r[r.pm.abs()<12]
print('competitive within-cycle SD:', round((comp.err - comp.groupby('cycle').err.transform('mean')).std(),2), 'n', len(comp))

for p in ['DEM','REP']:
    s = d[d.partisan==p]; dev = (s.pm2 - s.race_pm_mean) * (1 if p=='DEM' else -1)
    # compare to nonpartisan polls in same races only
    print('sponsor',p,'n',len(s),'mean deviation toward sponsor vs race mean', round(dev.mean(),2), 'median', round(dev.median(),2))
np_ = d[d.partisan.isna()]
rm = np_.groupby('race_id').pm2.mean()
for p in ['DEM','REP']:
    s = d[(d.partisan==p) & d.race_id.isin(rm.index)].copy()
    s['dev'] = (s.pm2 - s.race_id.map(rm)) * (1 if p=='DEM' else -1)
    print(' vs nonpartisan mean:', p, len(s), round(s.dev.mean(),2))
