"""US 2026 midterms: weighted polling averages + correlated-error simulation.
Writes dashboard datasets to out/*.json. Data cutoff: polls published up to 2 Nov 2026 (rerun 3 Nov 2026)."""
import json, math, os
import numpy as np, pandas as pd
from races import *

TODAY = pd.Timestamp("2026-11-03")
rng = np.random.default_rng(20261103)
NSIM = 40000
OUT = "out"; os.makedirs(OUT, exist_ok=True)

hist = pd.read_csv("pollster_hist.csv").set_index("pollster")
r538 = pd.read_csv("data_raw/pollster-ratings_pollster-ratings-combined.csv").set_index("pollster")
sres = pd.read_csv("state_resid.csv").set_index("location")

# ---------------------------------------------------------------- parameters (all exported to the params dataset)
BETA = 1.07
STATE_RHO, STATE_CAP = 0.25, 1.0
SPONSOR_SHIFT = {"D": -3.6, "C": -3.6, "R": +4.6}
SPONSOR_W = 0.5
HALF_LIFE, INFO_HALF_LIFE = 14.0, 30.0
NAT_SD, REG_SD, STATE_SD = 3.0, 1.8, 1.5
IDIO_BASE, IDIO_SPARSE, HOUSE_IDIO, T_DF = 3.0, 5.5, 5.0, 5
UNKNOWN_EXCESS, Q_SLOPE, Q_MIN, Q_MAX = 0.8, 0.4, 0.45, 1.6
HE_SHRINK = 4
SIZE_REF, SIZE_CAP, N_IMPUTE = 600, 2500, 700
POP_W = {"LV": 1.0, "RV": 0.75, "A": 0.5}
ADJ_2025 = {"State Navigate": -0.4, "Beacon/Shaw": +0.3}

CANON = {
 "co/efficient":"co/efficient","Echelon Insights":"Echelon Insights","InsiderAdvantage":"InsiderAdvantage",
 "Trafalgar Group":"Trafalgar Group","GS Strategy/New River":"GS Strategy Group","YouGov":"YouGov",
 "Marist":"Marist College","Emerson":"Emerson College","SSRS":"SSRS","Suffolk":"Suffolk University",
 "NYT/Siena":"The New York Times/Siena College","ReconMR/Siena":"Siena College","Rasmussen":"Rasmussen Reports",
 "Beacon/Shaw":"Beacon Research/Shaw & Co. Research","Cygnal":"Cygnal","Cygnal/Beacon":"Cygnal",
 "Global Strategy Group":"Global Strategy Group","Fabrizio Ward/Impact":"Fabrizio Lee & Associates/Impact Research",
 "WaPo/Schar":"The Washington Post/George Mason University Schar School of Policy and Government",
 "CBS/YouGov":"YouGov","Univision/YouGov":"YouGov","BGSU/YouGov":"YouGov","MSU/YouGov":"YouGov",
 "Catawba/YouGov":"YouGov","Elon/YouGov":"Elon University","High Point/YouGov":"High Point University Survey Research Center",
 "High Point Univ":"High Point University Survey Research Center","Tufts/YouGov":"YouGov","Economist/YouGov":"YouGov",
 "YouGov (254 Labs)":"YouGov","UMass Amherst/YouGov":"University of Massachusetts Department of Political Science/YouGov",
 "UMass Lowell/YouGov":"University of Massachusetts Lowell Center for Public Opinion",
 "Maine People's Resource Center":"Maine People's Resource Center","UNH":"University of New Hampshire Survey Center",
 "Univ of Houston":"University of Houston Hobby School of Public Affairs","Big Data Poll":"Big Data Poll",
 "Mason-Dixon":"Mason-Dixon Polling & Strategy","Concord Public Opinion":"Concord Public Opinion Partners",
 "Mitchell Research":"Mitchell Research & Communications","Glengariff Group":"Glengariff Group",
 "The Tyson Group":"The Tyson Group","GBAO":"GBAO","EPIC-MRA":"EPIC-MRA","Susquehanna":"Susquehanna Polling & Research Inc.",
 "TIPP Insights":"TIPP Insights","Impact Research":"Impact Research","SurveyUSA":"SurveyUSA",
 "Alaska Survey Research":"Alaska Survey Research","Data for Progress":"Data for Progress",
 "Targoz Market Research":"Targoz Market Research","East Carolina Univ":"East Carolina University Center for Survey Research",
 "Victory Insights":"Victory Insights","Morning Consult":"Morning Consult","GQR":"GQR","Saint Anselm":"Saint Anselm College Survey Center",
 "Harper Polling":"Harper Polling","Change Research":"Change Research","Univ of Georgia":"University of Georgia School of Public and International Affairs",
 "Univ of North Florida":"University of North Florida Public Opinion Research Lab","Stetson Univ":"Stetson University Center for Public Opinion Research",
 "St. Pete Polls":"St. Pete Polls","MSU Billings":"Montana State University Billings","American Pulse":"American Pulse Research & Polling",
 "Rutgers-Eagleton":"Rutgers University Eagleton Center for Public Interest Polling","Public Opinion Strategies":"Public Opinion Strategies",
 "RMG Research":"RMG Research","Hendrix College":"Hendrix College","J.L. Partners":"J.L. Partners","Research & Polling":"Research & Polling Inc.",
 "MassINC":"MassINC Polling Group","DHM Research":"DHM Research","Noble Predictive":"Noble Predictive Insights","Wick":"Wick",
 "Lake Research":"Lake Research Partners","Public Policy Polling":"Public Policy Polling","Braun Research":"Braun Research",
 "Fabrizio Lee":"Fabrizio, Lee & Associates","BSP Research":"BSP Research/Shaw & Company Research","McLaughlin & Associates":"McLaughlin & Associates",
 "HighGround":"HighGround Inc.","Arizona State Univ":"Arizona State University Morrison Institute for Public Policy",
 "Harvard/Harris":"Harris Insights & Analytics","Reuters/Ipsos":"Ipsos","Leger":"Leger","Clarity Campaign Labs":"Clarity Campaign Labs",
 "Hart/POS":"Hart Research Associates/Public Opinion Strategies","NBC News":"Hart Research Associates/Public Opinion Strategies",
 "AtlasIntel":"AtlasIntel","Research Co.":"Research Co.","Ipsos":"Ipsos","Political Matrix":"The Political Matrix/The Listener Group",
 "Patinkin Research":"Patinkin Research Strategies","ABC/WaPo/Ipsos":"ABC News/The Washington Post","SurveyMonkey":"SurveyMonkey",
}

def pollster_quality(p):
    key = CANON.get(p)
    src, excess, n_hist, hbias = "No track record (prior)", UNKNOWN_EXCESS, 0, None
    if key is not None and key in hist.index and hist.loc[key, "n"] >= 8:
        excess, n_hist = float(hist.loc[key, "excess_shrunk"]), int(hist.loc[key, "n"])
        hbias, src = float(hist.loc[key, "hist_bias_shrunk"]), "Own calc, 2014-22 polls"
    elif key is not None and key in r538.index and not pd.isna(r538.loc[key, "error_ppm"]):
        excess, src = float(r538.loc[key, "error_ppm"]) + 0.3, "538 rating (2024) + 0.3"
        if key in hist.index: n_hist, hbias = int(hist.loc[key, "n"]), float(hist.loc[key, "hist_bias_shrunk"])
    elif key is not None and key in hist.index:
        n = hist.loc[key, "n"]; excess = float((hist.loc[key, "excess_sum"] + UNKNOWN_EXCESS * 8) / (n + 8 + 15))
        n_hist, hbias, src = int(n), float(hist.loc[key, "hist_bias_shrunk"]), "Own calc, thin record"
    if p in ADJ_2025:
        excess += ADJ_2025[p]; src += "; 2025 review adj."
    w = float(np.clip(math.exp(-Q_SLOPE * excess), Q_MIN, Q_MAX))
    return w, float(excess), n_hist, hbias, src

# ---------------------------------------------------------------- polls and weights
polls = pd.read_csv("polls.csv", dtype={"sponsor": str}).fillna({"sponsor": ""})
polls["end"] = pd.to_datetime(polls["end"])
polls["age"] = (TODAY - polls["end"]).dt.days.clip(lower=0)
polls["m2"] = 100 * (polls.dem - polls.rep) / (polls.dem + polls.rep)
PAIRS = [(11,6),(9,9),(8,10),(9,5),(9,10),(11,12),(3,7),(2,4),(4,1),(9,6),(2,9),(0,2),(4,2),(9,-1),
 (2,4),(0,6),(2,7),(2,2),(3,1),(5,7),(4,9),(3,4),(6,10),(2,7),(1,3),(5,5),(4,7),(5,4),(3,4),(10,10),(11,11),
 (12,11),(8,10),(11,13),(12,11),(-4,5),(2,2),(2,4),(8,7),(7,3),(3,1),(5,0),(4,2),(-2,-1),(-1,0),(-2,-1)]
LV_RV = float(np.mean([a - b for a, b in PAIRS]))
polls["pop_adj"] = polls["pop"].map({"LV": 0.0, "RV": LV_RV, "A": 1.5 * LV_RV}).fillna(0.0)
polls["w_pop"] = polls["pop"].map(POP_W).fillna(0.75)
Q = {p: pollster_quality(p) for p in polls.pollster.unique()}
polls["w_q"] = polls.pollster.map(lambda p: Q[p][0])
polls["n_imp"] = polls.n.replace(0, N_IMPUTE)
polls["w_n"] = np.sqrt(polls.n_imp.clip(upper=SIZE_CAP) / SIZE_REF)
polls["w_sp"] = np.where(polls.sponsor != "", SPONSOR_W, 1.0)
polls["sp_adj"] = polls.sponsor.map(SPONSOR_SHIFT).fillna(0.0)
polls["w_freq"] = 1 / np.sqrt(polls.groupby(["race", "pollster"]).pollster.transform("size"))
common = polls.w_q * polls.w_n * polls.w_pop * polls.w_sp * polls.w_freq
polls["w"] = common * np.exp(-math.log(2) * polls.age / HALF_LIFE)
polls["w_info"] = common * np.exp(-math.log(2) * polls.age / INFO_HALF_LIFE)
polls["base"] = polls.m2 + polls.pop_adj + polls.sp_adj
polls["he"] = 0.0
for _ in range(3):
    polls["adj"] = polls.base - polls.he
    avg = polls.groupby("race").apply(lambda g: np.average(g.adj, weights=g.w), include_groups=False)
    polls["resid"] = polls.base - polls.race.map(avg)
    he = {p: np.average(g.resid, weights=g.w) * len(g) / (len(g) + HE_SHRINK) for p, g in polls.groupby("pollster")}
    polls["he"] = polls.pollster.map(he)
polls["adj"] = polls.base - polls.he

def race_stats(rid):
    g = polls[polls.race == rid]
    if len(g) == 0: return None
    rec = g[g.age <= 45]
    sd = float(np.sqrt(np.average((rec.adj - np.average(rec.adj, weights=rec.w)) ** 2, weights=rec.w))) if len(rec) >= 3 else None
    tops = g.groupby("pollster").w.sum().sort_values(ascending=False)
    share = tops / tops.sum()
    top = ", ".join(f"{p} {s:.0%}" for p, s in share.head(3).items())
    return dict(avg=float(np.average(g.adj, weights=g.w)), raw=float(np.average(g.m2, weights=g.w)),
                W=float(g.w_info.sum()), n=int(len(g)), n_30=int((g.age <= 30).sum()), sd=sd,
                sponsor_share=float(g[g.sponsor != ""].w.sum() / g.w.sum()), top=top, last=str(g.end.max().date()))

gb = race_stats("GB")
GB_MARGIN = gb["avg"]

# ---------------------------------------------------------------- statewide races
RVAL = {"Solid R": -18, "Safe R": -18, "Likely R": -10, "Lean R": -5.5, "Tilt R": -2.5, "Toss-up": 0,
        "Tilt D": 2.5, "Lean D": 5.5, "Likely D": 10, "Solid D": 18, "Safe D": 18}
STATE_NAME = dict(AL="Alabama",AK="Alaska",AZ="Arizona",AR="Arkansas",CA="California",CO="Colorado",CT="Connecticut",DE="Delaware",
 FL="Florida",GA="Georgia",HI="Hawaii",ID="Idaho",IL="Illinois",IN="Indiana",IA="Iowa",KS="Kansas",KY="Kentucky",LA="Louisiana",
 ME="Maine",MD="Maryland",MA="Massachusetts",MI="Michigan",MN="Minnesota",MS="Mississippi",MO="Missouri",MT="Montana",NE="Nebraska",
 NV="Nevada",NH="New Hampshire",NJ="New Jersey",NM="New Mexico",NY="New York",NC="North Carolina",ND="North Dakota",OH="Ohio",
 OK="Oklahoma",OR="Oregon",PA="Pennsylvania",RI="Rhode Island",SC="South Carolina",SD="South Dakota",TN="Tennessee",TX="Texas",
 UT="Utah",VT="Vermont",VA="Virginia",WA="Washington",WV="West Virginia",WI="Wisconsin",WY="Wyoming")
NOTES = {
 "S-AK":"Peltola narrowly ahead in sparse ranked-choice polling; Alaska polls have overstated Democrats before.",
 "S-GA":"Ossoff leads every public poll since August.",
 "S-IA":"Dead heat: Republican-leaning firms show Hinson ahead, higher-rated polls lean Turek.",
 "S-KS":"Hamilton has led most October polls against Marshall; the state's lean keeps it close.",
 "S-ME":"Jackson ahead in every final-week poll but one tie; Collins beat her final polls in 2020.",
 "S-MI":"El-Sayed leads consistently by mid single digits for an open Democratic seat.",
 "S-MN":"Flanagan ahead in every nonpartisan poll.",
 "S-MT":"Three-way race; independent Bodnar is only close in polls from allied sponsors.",
 "S-NE":"Ricketts ahead in most final polls; independent Osborn's best numbers come from allied sponsors.",
 "S-NH":"Pappas leads Sununu in every post-primary poll.",
 "S-NC":"Cooper leads every recent poll, mostly by high single or double digits.",
 "S-OH":"Brown narrowly ahead of appointed Sen. Husted; Republican-leaning firms show a tie.",
 "S-SC":"Appointed Sen. Darline Graham leads most polls; a few show Andrews ahead.",
 "S-TX":"Talarico leads narrowly in the most-polled race; few polls show Paxton ahead.",
 "S-FL":"Moody ahead in every poll except allied Democratic polls.",
 "S-ID":"Risch against independent Achilles; polling is scarce and contradictory.",
 "S-SD":"Rounds against independent Bengs; only an allied poll shows Bengs ahead.",
 "S-AL":"Double-digit Republican leads in the few polls.", "S-AR":"Cotton ahead by high single digits.",
 "S-NM":"Luján ahead by double digits.", "S-MA":"Markey far ahead.",
 "G-AK":"Kreiss-Tomkins leads final-round ranked-choice polls; Alaska's record of overstating Democrats trims the lead.",
 "G-AZ":"Hobbs ahead of Biggs in every recent poll.", "G-FL":"Donalds ahead in nearly every poll.",
 "G-GA":"Polls split between Bottoms and Jackson.", "G-IA":"Sand ahead in every poll since September.",
 "G-KS":"Final polls split, from Masterson +5 to Holscher +6.", "G-ME":"Pingree comfortably ahead despite an independent in the race.",
 "G-MI":"Benson leads by high single digits.", "G-MN":"Klobuchar far ahead.",
 "G-NE":"Pillen ahead in nonpartisan polls; Walz's internal polls show a tie.",
 "G-NV":"Close, with a slight Ford edge; few nonpartisan polls.", "G-NH":"Ayotte ahead in most polls; the final UNH poll shows a tie.",
 "G-NM":"Haaland ahead in sparse polling.", "G-OH":"Acton ahead in every final-week poll.",
 "G-OR":"Polls show a tie but are few and dated; ratings and the state's lean favor Kotek.",
 "G-TX":"Abbott narrowly ahead, far below his past margins.", "G-VT":"Scott led earlier polls, but the final UNH poll shows Janoo ahead.",
 "G-WI":"Crowley ahead in every Marquette poll.",
 "G-OK":"Mazzei narrowly ahead in small Cross Timbers polls; the state's lean and the ratings favor him.",
}
PSEUDO_NOTE = "PollCheck aggregate only (no poll-level data pulled)."
NOPOLL_NOTE = "No public polls in our set; prior from fundamentals and ratings."

def state_adj(st):
    return float(np.clip(STATE_RHO * sres.loc[st, "mean"], -STATE_CAP, STATE_CAP)) if st in sres.index else 0.0

def build(chamber, rows):
    out = []
    for (st, pvi, holder, inc, dn, rn, chal, cook, sab, ie) in rows:
        rid = f"{chamber}-{st}"
        rmean = float(np.mean([RVAL[x] for x in (cook, sab, ie)]))
        if chal == "I":
            fund, prior, kprior = None, rmean, 0.7
        elif chamber == "S":
            fund = GB_MARGIN + 2 * pvi + 2.5 * inc; prior = 0.5 * fund + 0.5 * rmean; kprior = 1.0
        else:
            fund = 0.8 * GB_MARGIN + 1.4 * pvi + 4.0 * inc; prior = 0.2 * fund + 0.8 * rmean; kprior = 0.6
        ra = race_stats(rid); pseudo = False
        if ra is None and rid in PSEUDO:
            d_, r_ = PSEUDO[rid]
            m = 12.7 if rid == "G-RI" else 100 * (d_ - r_) / (d_ + r_)
            ra = dict(avg=m, raw=m, W=1.5, n=0, n_30=0, sd=None, sponsor_share=0.0, top="PollCheck average", last="2026-11-02"); pseudo = True
        sadj = state_adj(st)
        if ra is not None:
            W = ra["W"]; mean = (W * BETA * ra["avg"] + kprior * prior) / (W + kprior) + sadj; share = W / (W + kprior)
        else:
            W = 0.0; mean = prior + sadj; share = 0.0
        sd = math.sqrt(IDIO_BASE ** 2 + (IDIO_SPARSE / math.sqrt(1 + W)) ** 2)
        if chal == "I": sd += 2.0
        if chamber == "S" and st == "MT": sd += 1.5
        if st == "AK": sd += 1.0
        if ra is None: sd = max(sd, 7.0)
        flags = []
        if ra is None: flags.append("No polls")
        elif pseudo: flags.append("Aggregate only")
        else:
            if ra["n_30"] < 3 or W < 2.0: flags.append("Sparse polling")
            if ra["sd"] is not None and ra["sd"] > 5.5: flags.append("Conflicting polls")
            if ra["sponsor_share"] > 0.35: flags.append("Mostly sponsored polls")
        if chal == "I": flags.append("Independent challenger")
        if st == "AK": flags.append("Ranked-choice")
        label = STATE_NAME[st] + (" (special)" if chamber == "S" and st in SENATE_SPECIAL else "")
        note = NOTES.get(rid, PSEUDO_NOTE if pseudo else NOPOLL_NOTE if ra is None else "")
        out.append(dict(id=rid, race=label, state=st, region=REG[st], chamber=chamber, pvi=pvi, holder=holder,
            incumbent="Running" if inc != 0 else "Open seat", chal=chal, dem=f"{dn} ({chal})", rep=f"{rn} (R)",
            cook=cook, sabato=sab, ie=ie, poll_avg=None if ra is None else round(ra["avg"], 1),
            poll_raw=None if ra is None else round(ra["raw"], 1), polls=0 if ra is None else ra["n"],
            polls_30d=0 if ra is None else ra["n_30"], last_poll=None if ra is None or pseudo else ra["last"],
            poll_weight=round(W, 2), poll_share=round(share, 3), top_pollsters="" if ra is None else ra["top"],
            poll_sd=None if ra is None or ra["sd"] is None else round(ra["sd"], 1),
            fundamentals=None if fund is None else round(fund, 1), ratings_margin=round(rmean, 1), prior=round(prior, 1),
            state_adj=round(sadj, 2), margin=round(mean, 1), sd=round(sd, 2), flags="; ".join(flags), rationale=note,
            pos=chal, neg="R", _mean=mean))
    return out

sen = build("S", SENATE); gov = build("G", GOV)

# ---------------------------------------------------------------- House
HVAL = {"Likely D": 10, "Lean D": 5.5, "Tilt D": 2.5, "Toss-up": 0, "Tilt R": -2.5, "Lean R": -5.5, "Likely R": -10}
house = []
for dist, (pvi, holder, inc, note) in HOUSE.items():
    vals = []
    for src in (COOK, SAB, IE):
        if dist in src: vals.append(HVAL[src[dist]])
        else:
            dem_side = CONS.get(dist, "").endswith("D") or (holder == "D" and dist not in CONS) or dist == "CA-06"
            vals.append(15 if dem_side else -15)
    rmean = float(np.mean(vals))
    fund = GB_MARGIN + 2 * pvi + 2.5 * inc
    if dist == "CA-06": fund = rmean
    m = 0.5 * fund + 0.5 * rmean
    pvi_txt = "EVEN" if pvi == 0 else (f"D+{pvi}" if pvi > 0 else f"R+{-pvi}")
    house.append(dict(district=dist, state=dist[:2], region=REG[dist[:2]], holder=holder,
        incumbent="Running" if (inc != 0 or dist == "CA-06") else "Open seat", pvi=pvi_txt, pvi_num=pvi,
        cook=COOK.get(dist, "Safe"), sabato=SAB.get(dist, "Safe"), ie=IE.get(dist, "Safe"), consensus=CONS.get(dist, "Safe"),
        fundamentals=round(fund, 1), ratings_margin=round(rmean, 1), margin=round(m, 1), sd=HOUSE_IDIO, note=note,
        pos="D", neg="I" if dist == "CA-06" else "R", _mean=m))
NU_D = sum(1 for h in house if h["district"] not in CONS and h["ratings_margin"] > 0)
NU_R = sum(1 for h in house if h["district"] not in CONS and h["ratings_margin"] < 0)
SAFE_D, SAFE_R = CONS_SAFE_D - NU_D, CONS_SAFE_R - NU_R
assert len(house) + SAFE_D + SAFE_R == 435

# ---------------------------------------------------------------- simulation
states = sorted(set(REG)); regions = sorted(set(REG.values()))
si = {s: i for i, s in enumerate(states)}; ri = {r: i for i, r in enumerate(regions)}
e_nat = rng.normal(0, NAT_SD, NSIM)
e_reg = rng.normal(0, REG_SD, (NSIM, len(regions)))
e_st = rng.normal(0, STATE_SD, (NSIM, len(states)))
tscale = 1 / math.sqrt(T_DF / (T_DF - 2))
def draws(races): return np.column_stack([rng.standard_t(T_DF, NSIM) * r["sd"] * tscale for r in races])
def margins(races, idio, shift=0.0):
    M = np.empty((NSIM, len(races)))
    for j, r in enumerate(races):
        M[:, j] = r["_mean"] + e_nat + shift + e_reg[:, ri[r["region"]]] + e_st[:, si[r["state"]]] + idio[:, j]
    return M
def tally(M, races, hold):
    c = {"D": np.full(NSIM, hold["D"]), "R": np.full(NSIM, hold["R"]), "I": np.full(NSIM, hold["I"])}
    for j, r in enumerate(races):
        win = M[:, j] > 0
        c[r["pos"]] = c[r["pos"]] + win; c[r["neg"]] = c[r["neg"]] + (~win)
    return c
S_id, G_id, H_id = draws(sen), draws(gov), draws(house)
S, G, H = margins(sen, S_id), margins(gov, G_id), margins(house, H_id)
HOUSE_HOLD = {"D": SAFE_D, "R": SAFE_R, "I": 0}
sc, gc, hc = tally(S, sen, SENATE_HOLDOVER), tally(G, gov, GOV_HOLDOVER), tally(H, house, HOUSE_HOLD)

def rating(p, pos):
    x = max(p, 1 - p); side = pos if p >= 0.5 else "R"
    if x < 0.60: return "Toss-up"
    return ("Tilt" if x < 0.70 else "Lean" if x < 0.85 else "Likely" if x < 0.97 else "Safe") + " " + side
for M, races in ((S, sen), (G, gov), (H, house)):
    for j, r in enumerate(races):
        p = float(np.mean(M[:, j] > 0))
        r["p_win"] = round(p, 3); r["p_win_r"] = round(1 - p, 3) if r["neg"] == "R" else None
        r["margin_lo"] = round(float(np.percentile(M[:, j], 10)), 1); r["margin_hi"] = round(float(np.percentile(M[:, j], 90)), 1)
        r["model_rating"] = rating(p, r["pos"]) if r["neg"] == "R" else ("Toss-up" if max(p, 1-p) < 0.6 else
                             rating(p, "D").replace(" R", " I") if p < 0.5 else rating(p, "D"))
        r["favored"] = r["pos"] if p >= 0.5 else r["neg"]

def central(c, total):
    means = {k: float(v.mean()) for k, v in c.items()}
    fl = {k: math.floor(m) for k, m in means.items()}
    rem = total - sum(fl.values())
    for k in sorted(means, key=lambda k: -(means[k] - fl[k]))[:rem]: fl[k] += 1
    return fl, means

# ---------------------------------------------------------------- datasets
def dump(name, rows):
    json.dump(rows, open(f"{OUT}/{name}.json", "w"), indent=0, ensure_ascii=False, default=float)

NOW = {"senate": {"D": 45, "R": 53, "I": 2}, "house": {"D": 214, "R": 218, "I": 1}, "governors": {"D": 24, "R": 26, "I": 0}}
summary = []
for ch, c, total in (("senate", sc, 100), ("house", hc, 435), ("governors", gc, 50)):
    cen, means = central(c, total)
    for party in ("D", "R", "I"):
        v = c[party]
        summary.append(dict(chamber=ch, party=party, central=cen[party], mean=round(means[party], 1),
                            median=int(np.median(v)), p10=int(np.percentile(v, 10)), p90=int(np.percentile(v, 90)),
                            now=NOW[ch][party], change=cen[party] - NOW[ch][party]))
dump("summary", summary)

control = [
 dict(chamber="senate", outcome="D", label="Democrats control (with Sanders and King)", prob=round(float(np.mean(sc["D"] + 2 >= 51)), 3)),
 dict(chamber="senate", outcome="R", label="Republicans control (50 seats plus VP Vance)", prob=round(float(np.mean(sc["R"] >= 50)), 3)),
 dict(chamber="senate", outcome="other", label="Majority depends on newly elected independents", prob=None),
 dict(chamber="house", outcome="D", label="Democrats win 218+", prob=round(float(np.mean(hc["D"] >= 218)), 3)),
 dict(chamber="house", outcome="R", label="Republicans win 218+", prob=round(float(np.mean(hc["R"] >= 218)), 3)),
 dict(chamber="house", outcome="other", label="No party reaches 218", prob=None),
 dict(chamber="governors", outcome="D", label="Democrats hold 26+ governorships", prob=round(float(np.mean(gc["D"] >= 26)), 3)),
 dict(chamber="governors", outcome="R", label="Republicans hold 26+ governorships", prob=round(float(np.mean(gc["R"] >= 26)), 3)),
 dict(chamber="governors", outcome="other", label="25-25 split", prob=None),
]
for ch in ("senate", "house", "governors"):
    rows = [r for r in control if r["chamber"] == ch]
    rows[2]["prob"] = round(1 - rows[0]["prob"] - rows[1]["prob"], 3)
dump("control", control)

dist = []
for ch, c, lo, hi, thr in (("senate", sc, 40, 60, 49), ("house", hc, 185, 270, 218), ("governors", gc, 15, 35, 26)):
    v = c["D"]; vals, cnt = np.unique(v, return_counts=True)
    for s, n in zip(vals, cnt):
        dist.append(dict(chamber=ch, seats=int(s), prob=round(n / NSIM, 4), threshold=thr))
dump("seat_dist", dist)

KEEP_S = ["race","holder","incumbent","dem","rep","poll_avg","polls","polls_30d","last_poll","poll_weight","poll_share",
          "top_pollsters","prior","state_adj","margin","margin_lo","margin_hi","p_win","favored","model_rating",
          "cook","sabato","ie","flags","rationale","chal","pvi","poll_raw","poll_sd","fundamentals","ratings_margin"]
dump("senate_races", [{k: r[k] for k in KEEP_S} for r in sorted(sen, key=lambda r: abs(r["margin"]))])
dump("governor_races", [{k: r[k] for k in KEEP_S} for r in sorted(gov, key=lambda r: abs(r["margin"]))])
KEEP_H = ["district","holder","incumbent","pvi","cook","sabato","ie","fundamentals","ratings_margin","margin",
          "margin_lo","margin_hi","p_win","favored","model_rating","note","neg"]
dump("house_races", [{k: h[k] for k in KEEP_H} for h in sorted(house, key=lambda h: abs(h["margin"]))])

scen = []
for s in range(-6, 7):
    a = tally(margins(sen, S_id, s), sen, SENATE_HOLDOVER); b = tally(margins(house, H_id, s), house, HOUSE_HOLD)
    g = tally(margins(gov, G_id, s), gov, GOV_HOLDOVER)
    scen.append(dict(shift=s, senate_dem_control=round(float(np.mean(a["D"] + 2 >= 51)), 3),
                     house_dem_control=round(float(np.mean(b["D"] >= 218)), 3),
                     senate_dem_seats=round(float(a["D"].mean()), 1), house_dem_seats=round(float(b["D"].mean()), 1),
                     governors_dem=round(float(g["D"].mean()), 1)))
dump("scenarios", scen)

pq = []
for p in sorted(Q, key=lambda p: -Q[p][0]):
    sub = polls[polls.pollster == p]
    pq.append(dict(pollster=p, weight=round(Q[p][0], 2), excess_error=round(Q[p][1], 2), track_record=Q[p][4],
                   hist_polls=Q[p][2], hist_bias=None if Q[p][3] is None else round(Q[p][3], 2),
                   house_effect=round(float(sub.he.iloc[0]), 2), polls_2026=int(len(sub)), sponsored=int((sub.sponsor != "").sum())))
dump("pollsters", pq)

def contest(r):
    if r == "GB": return "Generic ballot"
    return ("Senate · " if r.startswith("S-") else "Governor · ") + STATE_NAME[r[2:]]
SP = {"": "", "D": "Democratic-aligned", "R": "Republican-aligned", "C": "Ally of independent"}
pl = polls.sort_values(["race", "end"], ascending=[True, False]).reset_index(drop=True)
dump("polls", [dict(poll=i + 1, contest=contest(r.race), pollster=r.pollster, sponsor=SP[r.sponsor], end=r.end.strftime("%Y-%m-%d"),
                    n=int(r.n) if r.n else None, pop=r["pop"], dem=float(r.dem), rep=float(r.rep), margin_2p=round(r.m2, 1),
                    pop_adj=round(r.pop_adj, 2), sponsor_adj=round(r.sp_adj, 1), house_effect=round(r.he, 2),
                    adj_margin=round(r.adj, 1), weight=round(r.w, 3))
               for i, r in pl.iterrows()])

dump("cycle_bias", [
 dict(cycle=2010, kind="Midterm", state_poll_bias=-0.68, generic_bias=-0.33, source="538 raw polls, own calc"),
 dict(cycle=2012, kind="Presidential", state_poll_bias=-2.38, generic_bias=-0.81, source="538 raw polls, own calc"),
 dict(cycle=2014, kind="Midterm", state_poll_bias=3.13, generic_bias=3.16, source="538 raw polls, own calc"),
 dict(cycle=2016, kind="Presidential", state_poll_bias=4.68, generic_bias=3.65, source="538 raw polls, own calc"),
 dict(cycle=2018, kind="Midterm", state_poll_bias=-0.15, generic_bias=-1.20, source="538 raw polls, own calc"),
 dict(cycle=2020, kind="Presidential", state_poll_bias=5.52, generic_bias=4.86, source="538 raw polls, own calc"),
 dict(cycle=2022, kind="Midterm", state_poll_bias=0.98, generic_bias=2.33, source="538 raw polls, own calc"),
 dict(cycle=2024, kind="Presidential", state_poll_bias=2.7, generic_bias=None, source="538/ABC News review, competitive states"),
 dict(cycle=2025, kind="Off-year (NJ, VA governor)", state_poll_bias=-7.4, generic_bias=None, source="RealClearPolling averages vs results"),
])

race_states = sorted(set([r["state"] for r in sen + gov]))
dump("state_bias", [dict(state=STATE_NAME[s], mean_miss=round(float(sres.loc[s, "mean"]), 2) if s in sres.index else None,
                         races=int(sres.loc[s, "count"]) if s in sres.index else 0, applied=round(state_adj(s), 2)) for s in race_states])

dump("params", [
 dict(key="nsim", label="Simulations", value=NSIM, unit="runs"),
 dict(key="cutoff", label="Poll cutoff", value="2026-11-02", unit="date"),
 dict(key="gb", label="Generic ballot average (two-party, after adjustments)", value=round(GB_MARGIN, 1), unit="pts D"),
 dict(key="gb_raw", label="Generic ballot average before adjustments", value=round(gb["raw"], 1), unit="pts D"),
 dict(key="gb_n", label="Generic ballot polls used", value=gb["n"], unit="polls"),
 dict(key="half_life", label="Recency half-life for averages", value=HALF_LIFE, unit="days"),
 dict(key="info_half_life", label="Recency half-life for poll volume vs prior", value=INFO_HALF_LIFE, unit="days"),
 dict(key="size_ref", label="Sample size giving weight 1", value=SIZE_REF, unit="respondents"),
 dict(key="size_cap", label="Sample size cap", value=SIZE_CAP, unit="respondents"),
 dict(key="w_rv", label="Weight of registered-voter polls", value=POP_W["RV"], unit="x"),
 dict(key="w_a", label="Weight of all-adult polls", value=POP_W["A"], unit="x"),
 dict(key="lv_rv", label="Likely minus registered voter margin (paired versions)", value=round(LV_RV, 2), unit="pts"),
 dict(key="lv_pairs", label="Paired LV/RV versions used", value=len(PAIRS), unit="pairs"),
 dict(key="q_slope", label="Quality weight = exp(-k x excess error), k", value=Q_SLOPE, unit=""),
 dict(key="q_min", label="Quality weight floor", value=Q_MIN, unit="x"),
 dict(key="q_max", label="Quality weight ceiling", value=Q_MAX, unit="x"),
 dict(key="unknown_excess", label="Assumed excess error, no track record", value=UNKNOWN_EXCESS, unit="pts"),
 dict(key="sponsor_w", label="Weight of sponsored polls", value=SPONSOR_W, unit="x"),
 dict(key="sponsor_d", label="Shift applied to Democratic-sponsored polls", value=SPONSOR_SHIFT["D"], unit="pts"),
 dict(key="sponsor_r", label="Shift applied to Republican-sponsored polls", value=SPONSOR_SHIFT["R"], unit="pts"),
 dict(key="he_shrink", label="House-effect shrinkage (n / (n + k)), k", value=HE_SHRINK, unit="polls"),
 dict(key="beta", label="Actual vs poll-average margin slope", value=BETA, unit="x"),
 dict(key="state_rho", label="Persistence applied to state polling misses", value=STATE_RHO, unit="x"),
 dict(key="state_corr", label="Measured persistence of state misses (correlation)", value=0.28, unit=""),
 dict(key="state_cap", label="Cap on state adjustment", value=STATE_CAP, unit="pts"),
 dict(key="nat_sd", label="National polling-miss SD (shared by every race)", value=NAT_SD, unit="pts"),
 dict(key="reg_sd", label="Regional error SD", value=REG_SD, unit="pts"),
 dict(key="state_sd", label="State error SD (shared by races in a state)", value=STATE_SD, unit="pts"),
 dict(key="idio", label="Race-specific error SD, well-polled race", value=IDIO_BASE, unit="pts"),
 dict(key="house_idio", label="District-specific error SD", value=HOUSE_IDIO, unit="pts"),
 dict(key="t_df", label="Fat tails: Student t degrees of freedom", value=T_DF, unit=""),
 dict(key="cycle_sd", label="Measured SD of national miss across cycles", value=2.77, unit="pts"),
 dict(key="comp_sd", label="Measured race-level miss SD, competitive races", value=4.1, unit="pts"),
 dict(key="sp_d_meas", label="Measured lean of Democratic-sponsored polls", value=3.6, unit="pts"),
 dict(key="sp_r_meas", label="Measured lean of Republican-sponsored polls", value=4.6, unit="pts"),
 dict(key="safe_d", label="House seats Safe D in every rating", value=SAFE_D, unit="seats"),
 dict(key="safe_r", label="House seats Safe R in every rating", value=SAFE_R, unit="seats"),
 dict(key="house_detail", label="House districts modelled one by one", value=len(house), unit="seats"),
 dict(key="sen_hold_d", label="Senate Democrats not up in 2026", value=SENATE_HOLDOVER["D"], unit="seats"),
 dict(key="sen_hold_r", label="Senate Republicans not up in 2026", value=SENATE_HOLDOVER["R"], unit="seats"),
 dict(key="sen_hold_i", label="Senate independents not up (Sanders, King)", value=SENATE_HOLDOVER["I"], unit="seats"),
 dict(key="gov_hold_d", label="Democratic governors not up", value=GOV_HOLDOVER["D"], unit="seats"),
 dict(key="gov_hold_r", label="Republican governors not up", value=GOV_HOLDOVER["R"], unit="seats"),
 dict(key="n_polls", label="Race polls in the database", value=int((polls.race != "GB").sum()), unit="polls"),
 dict(key="n_pollsters", label="Pollsters in the database", value=len(Q), unit="pollsters"),
 dict(key="w_sen_fund", label="Senate prior: weight on fundamentals", value=0.5, unit="x"),
 dict(key="w_gov_fund", label="Governor prior: weight on fundamentals", value=0.2, unit="x"),
 dict(key="k_sen", label="Senate prior strength (poll-weight units)", value=1.0, unit=""),
 dict(key="k_gov", label="Governor prior strength (poll-weight units)", value=0.6, unit=""),
 dict(key="w_house_fund", label="House: weight on fundamentals (rest on ratings)", value=0.5, unit="x"),
 dict(key="inc_sen", label="Incumbency, Senate and House", value=2.5, unit="pts"),
 dict(key="inc_gov", label="Incumbency, governor", value=4.0, unit="pts"),
 dict(key="hist_days", label="Window for historical accuracy", value=21, unit="days before election"),
 dict(key="hist_k", label="Shrinkage of pollster record (n / (n + k)), k", value=15, unit="polls"),
 dict(key="min_hist", label="Polls needed to use our own record", value=8, unit="polls"),
 dict(key="pen538", label="Penalty added to 538 rating when used", value=0.3, unit="pts"),
 dict(key="he_passes", label="House-effect passes", value=3, unit=""),
 dict(key="sen_needed", label="Senate seats for a majority", value=51, unit="seats"),
 dict(key="house_needed", label="House seats for a majority", value=218, unit="seats"),
 dict(key="gov_majority", label="Governorships for a majority", value=26, unit="seats"),
 dict(key="sen_total", label="Senate seats", value=100, unit="seats"),
 dict(key="sen_up", label="Senate seats up in 2026", value=35, unit="seats"),
 dict(key="gov_up", label="Governor races in 2026", value=36, unit="races"),
 dict(key="gov_notup", label="States without a 2026 governor race", value=14, unit="states"),
 dict(key="house_total", label="House seats", value=435, unit="seats"),
 dict(key="house_vacant", label="Vacant House seats today", value=2, unit="seats"),
 dict(key="pseudo_n", label="Governor races with aggregate averages only", value=sum(1 for r in gov if r["flags"].startswith("Aggregate only")), unit="races"),
 dict(key="w_gov_rate", label="Governor prior: weight on ratings", value=0.8, unit="x"),
 dict(key="w_sen_rate", label="Senate prior: weight on ratings", value=0.5, unit="x"),
])
print("datasets written")
print("GB", round(GB_MARGIN, 2), "LV-RV", round(LV_RV, 2))
for r in summary: print(r)
for r in control: print(r)
