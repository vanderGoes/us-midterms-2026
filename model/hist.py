import pandas as pd, numpy as np, json
d = pd.read_csv('data_raw/raw_polls.csv')
d = d[d.type_simple.isin(['Sen-G','Gov-G','Pres-G','House-G','House-G-US'])].copy()
# orient to D-R
def dr(row, which):
    p1, p2 = row.cand1_party, row.cand2_party
    a = row['cand1_'+which]; b = row['cand2_'+which]
    if p1 == 'DEM' and p2 == 'REP': return a - b
    if p1 == 'REP' and p2 == 'DEM': return b - a
    return np.nan
d['poll_m'] = d.apply(lambda r: dr(r,'pct'), axis=1)
d['act_m'] = d.apply(lambda r: dr(r,'actual'), axis=1)
d['err'] = d.poll_m - d.act_m          # + = poll overstated Dems
d['abserr'] = (d.margin_poll - d.margin_actual).abs()   # works for any pair
d = d[d.time_to_election <= 21]
print('rows', len(d))
# 1) pollster race-adjusted excess error 2014-2022 (general elections, all types)
g = d[d.cycle.between(2014, 2023)].copy()
g['race_mean'] = g.groupby('race_id').abserr.transform('mean')
g['race_n'] = g.groupby('race_id').abserr.transform('count')
g = g[g.race_n >= 2]
g['excess'] = g.abserr - g.race_mean
# 2) signed bias relative to race mean signed error (house effect, historical)
g['race_err_mean'] = g.groupby('race_id').err.transform('mean')
g['rel_bias'] = g.err - g.race_err_mean
K = 15
ps = g.groupby('pollster').agg(n=('excess','size'), excess_raw=('excess','mean'),
        excess_sum=('excess','sum'), relbias_sum=('rel_bias', lambda x: np.nansum(x)),
        last_cycle=('cycle','max'))
ps['excess_shrunk'] = ps.excess_sum/(ps.n+K)
ps['hist_bias_shrunk'] = ps.relbias_sum/(ps.n+K)
ps = ps.sort_values('n', ascending=False)
ps.to_csv('pollster_hist.csv')
print(ps.head(40)[['n','excess_raw','excess_shrunk','hist_bias_shrunk','last_cycle']].round(2).to_string())
# 3) partisan sponsored polls
g['part'] = g.partisan.fillna('N')
for p in ['D','R']:
    sub = g[g.part==p]
    # signed error toward sponsor party relative to race mean
    tow = sub.rel_bias if p=='D' else -sub.rel_bias
    print('partisan', p, 'n', len(sub), 'mean rel bias toward sponsor', round(np.nanmean(tow),2), 'excess err', round(sub.excess.mean(),2))
# 4) national bias by cycle (state-level Sen/Gov/Pres polls) and generic ballot
st = d[d.type_simple.isin(['Sen-G','Gov-G','Pres-G']) & (d.location.str.len()==2) & (d.location!='US')]
cyc = st[st.cycle.isin([2014,2016,2018,2020,2022])].groupby('cycle').err.agg(['mean','count'])
print('state-poll mean signed error by cycle (+ = D overstated)\n', cyc.round(2))
gb = d[d.type_simple=='House-G-US'].groupby('cycle').err.agg(['mean','count'])
print('generic ballot signed error by cycle\n', gb.round(2))
# 5) state relative bias by cycle
st2 = st[st.cycle.isin([2016,2018,2020,2022])].copy()
# race-level average error first (avoid heavily polled races dominating)
race = st2.groupby(['cycle','location','race_id']).err.mean().reset_index()
nat = race.groupby('cycle').err.mean()
race['rel'] = race.err - race.cycle.map(nat)
sb = race.groupby(['location','cycle']).rel.mean().unstack()
sb['mean_rel'] = sb.mean(axis=1)
sb['n_cycles'] = sb[[2016,2018,2020,2022]].notna().sum(axis=1)
sb.round(2).to_csv('state_bias.csv')
print(sb.round(1).sort_values('mean_rel').to_string())
print('national race-level bias', nat.round(2).to_dict())
