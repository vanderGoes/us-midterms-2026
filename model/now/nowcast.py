"""Election-night nowcast: the 3 Nov forecast, conditioned on called races.

A race counts as called when AP, or at least two of NBC, CNN, Fox News, ABC and CBS,
have projected a winner (now/calls.csv). Called races are fixed to their winner. Races
not yet called keep the forecast's distribution, updated through the errors the forecast
shares between races (national, regional, state): each call says something about the
size and direction of the polling miss, and that moves the races still open.

Method: draw the shared errors from the forecast's distribution; weight each draw by the
probability that every called race goes the way it was called (exact, because the
race-specific errors are independent once the shared errors are known); resample draws
by weight; then draw race-specific errors for the races not yet called.

Usage: python3 now/nowcast.py [--nocalls]   (--nocalls reproduces the forecast, as a check)
Writes dashboard datasets to now/out/.
"""
import contextlib, csv, io, json, math, os, sys
from datetime import datetime, timedelta
import numpy as np
from scipy.stats import t as student_t

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.dirname(HERE)
os.chdir(MODEL)
sys.path.insert(0, MODEL)
NOCALLS = "--nocalls" in sys.argv

# ---- race list exactly as the forecast builds it (small NSIM, scratch output)
src = open("model_final.py").read()
assert "NSIM = 40000" in src and 'OUT = "out"' in src
src = src.replace("NSIM = 40000", "NSIM = 2000").replace('OUT = "out"', 'OUT = "now/scratch"')
ns = {"__name__": "forecast"}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, "model_final.py", "exec"), ns)
sen, gov, house = ns["sen"], ns["gov"], ns["house"]
NAT_SD, REG_SD, STATE_SD, T_DF = ns["NAT_SD"], ns["REG_SD"], ns["STATE_SD"], ns["T_DF"]
SEN_HOLD, GOV_HOLD = ns["SENATE_HOLDOVER"], ns["GOV_HOLDOVER"]
SAFE_D, SAFE_R = ns["SAFE_D"], ns["SAFE_R"]
REG, STATE_NAME = ns["REG"], ns["STATE_NAME"]

races = ([("S", r, "S-" + r["state"]) for r in sen] + [("G", r, "G-" + r["state"]) for r in gov]
         + [("H", r, "H-" + r["district"]) for r in house])
ids = [k for _, _, k in races]
assert len(set(ids)) == len(ids)
idx = {k: j for j, k in enumerate(ids)}
R = len(races)

# ---- calls
def read(fn):
    p = os.path.join(HERE, fn)
    return list(csv.DictReader(open(p, newline=""))) if os.path.exists(p) else []
calls, pending = read("calls.csv"), read("pending.csv")
if NOCALLS: calls, pending = [], []
called = {}
for c in calls:
    k = c["id"]
    if k not in idx: sys.exit(f"Call for a race the model does not have: {k}")
    if k in called: sys.exit(f"Duplicate call: {k}")
    r = races[idx[k]][1]
    if c["party"] not in (r["pos"], r["neg"]): sys.exit(f"{k}: called for {c['party']}, race is {r['pos']} vs {r['neg']}")
    called[k] = c
for p in pending:
    if p["id"] in called: sys.exit(f"{p['id']} is in both calls.csv and pending.csv")
cj = np.array([idx[k] for k in called], dtype=int)
csign = np.array([1.0 if called[k]["party"] == races[idx[k]][1]["pos"] else -1.0 for k in called])

# ---- simulation
mean = np.array([r["_mean"] for _, r, _ in races])
sd = np.array([r["sd"] for _, r, _ in races])
states = sorted(set(REG)); regions = sorted(set(REG.values()))
st_i = np.array([states.index(r["state"]) for _, r, _ in races])
rg_i = np.array([regions.index(r["region"]) for _, r, _ in races])
tscale = 1 / math.sqrt(T_DF / (T_DF - 2))
rng = np.random.default_rng(20261104)
from scipy.stats import norm
NR, NS = len(regions), len(states)
K = 1 + NR + NS
prior_sd = np.r_[NAT_SD, np.full(NR, REG_SD), np.full(NS, STATE_SD)]
def loglik(Z):
    ll = np.zeros(len(Z))
    for j, sg in zip(cj, csign):
        shared = mean[j] + Z[:, 0] + Z[:, 1 + rg_i[j]] + Z[:, 1 + NR + st_i[j]]
        ll += student_t.logcdf(sg * shared / (sd[j] * tscale), T_DF)
    return ll
def logw_of(Z, m, s):
    return (norm.logpdf(Z, 0, prior_sd).sum(1) - norm.logpdf(Z, m, s).sum(1)) + loglik(Z)
# adaptive importance sampling: move the proposal for the shared errors toward their posterior
m, s = np.zeros(K), prior_sd.copy()
for _ in range(3):
    Z = rng.normal(m, s, (100_000, K)); lw = logw_of(Z, m, s)
    w = np.exp(lw - lw.max()); w /= w.sum()
    m = w @ Z; s = np.clip(np.sqrt(w @ (Z - m) ** 2) * 1.25, 0.25 * prior_sd, prior_sd)
S, N = 300_000, 60_000
Z = np.concatenate([rng.normal(m, s, (150_000, K)) for _ in range(2)])
lw = np.concatenate([logw_of(Z[i:i + 150_000], m, s) for i in (0, 150_000)])
w = np.exp(lw - lw.max()); w /= w.sum()
ess = float(1 / np.sum(w ** 2))
pick = np.minimum(np.searchsorted(np.cumsum(w), (rng.random() + np.arange(N)) / N), S - 1)
e_nat, e_reg, e_st = Z[:, 0], Z[:, 1:1 + NR], Z[:, 1 + NR:]
nat_shift = float(np.sum(w * e_nat))
M = (mean + e_nat[pick, None] + e_reg[pick][:, rg_i] + e_st[pick][:, st_i]
     + rng.standard_t(T_DF, (N, R)) * sd * tscale)
win = M > 0
if len(cj):
    win[:, cj] = csign > 0
    M[:, cj] = np.nan
print(f"{len(called)} calls; effective sample of shared-error draws {ess:,.0f} of {S:,}; "
      f"implied national shift {nat_shift:+.2f} pts toward D")

# ---- tallies
HOLD = {"senate": SEN_HOLD, "governors": GOV_HOLD, "house": {"D": SAFE_D, "R": SAFE_R, "I": 0}}
CODE = {"senate": "S", "governors": "G", "house": "H"}
TOTAL = {"senate": 100, "governors": 50, "house": 435}
def tally(ch):
    c = {p: np.full(N, HOLD[ch].get(p, 0), dtype=np.int64) for p in ("D", "R", "I")}
    for j, (cc, r, _) in enumerate(races):
        if cc != CODE[ch]: continue
        c[r["pos"]] += win[:, j]; c[r["neg"]] += ~win[:, j]
    return c
T = {ch: tally(ch) for ch in HOLD}
for ch in T: assert np.all(sum(T[ch].values()) == TOTAL[ch]), ch
p_now = win.mean(0)

OUT = os.path.join(HERE, "out"); os.makedirs(OUT, exist_ok=True)
def r1(x): return None if x is None or (isinstance(x, float) and math.isnan(x)) else round(float(x), 1)
def r3(x): return round(float(x), 3)
def dump(name, rows):
    json.dump(rows, open(os.path.join(OUT, name + ".json"), "w"), ensure_ascii=False, separators=(",", ":"))

pre_sum = {(r["chamber"], r["party"]): r for r in json.load(open("out/summary.json"))}
pre_ctl = {(r["chamber"], r["outcome"]): r["prob"] for r in json.load(open("out/control.json"))}
name_to_st = {v: k for k, v in STATE_NAME.items()}
pre_race = {}
for f, cc in (("senate_races", "S"), ("governor_races", "G")):
    for r in json.load(open(f"out/{f}.json")):
        st = r.get("state") or name_to_st[r["race"].replace(" (special)", "")]
        pre_race[cc + "-" + st] = r
for r in json.load(open("out/house_races.json")): pre_race["H-" + r["district"]] = r
assert set(pre_race) == set(ids), set(ids) ^ set(pre_race)

def rating(p, pos, neg):
    x = max(p, 1 - p); side = pos if p >= 0.5 else neg
    if x < 0.60: return "Toss-up"
    return ("Tilt" if x < 0.70 else "Lean" if x < 0.85 else "Likely" if x < 0.97 else "Safe") + " " + side

# ---- per-race rows
rows = {"S": [], "G": [], "H": []}
secured = {ch: dict(HOLD[ch]) for ch in HOLD}
leaning = {ch: {"D": 0, "R": 0, "I": 0} for ch in HOLD}
tossup = {ch: 0 for ch in HOLD}
n_called = {ch: 0 for ch in HOLD}
CH = {"S": "senate", "G": "governors", "H": "house"}
for j, (cc, r, k) in enumerate(races):
    pre = pre_race[k]; c = called.get(k); ch = CH[cc]
    p = float(p_now[j]); p0 = float(pre["p_win"])
    if c:
        party = c["party"]; secured[ch][party] += 1; n_called[ch] += 1
        won_pos = party == r["pos"]
        base = dict(status="Called", winner=f'{c["winner"]} ({party})', winner_party=party, called_by=c["called_by"],
                    seen_et=c["seen_et"], margin=None, margin_lo=None, margin_hi=None,
                    rating_now="Won by " + party, favored=party,
                    flip="Yes" if party != r["holder"] else "No",
                    upset="Yes" if (p0 < 0.5 if won_pos else p0 > 0.5) else "No")
    else:
        fav = r["pos"] if p >= 0.5 else r["neg"]
        if max(p, 1 - p) >= 0.6: leaning[ch][fav] += 1
        else: tossup[ch] += 1
        m = M[:, j]
        base = dict(status="Not called", winner="", winner_party="", called_by="", seen_et="",
                    margin=r1(m.mean()), margin_lo=r1(np.percentile(m, 10)), margin_hi=r1(np.percentile(m, 90)),
                    rating_now=rating(p, r["pos"], r["neg"]), favored=fav, flip="", upset="")
    base.update(id=k, p_pre=r3(p0), p_win=r3(p), change=r3(p - p0), rating_pre=pre.get("model_rating", ""),
                holder=r["holder"], pos=r["pos"], neg=r["neg"])
    if cc == "H":
        base.update(district=r["district"], race=r["district"], pvi=pre.get("pvi", r.get("pvi")),
                    cook=r["cook"], sabato=r["sabato"], ie=r["ie"], note=pre.get("note", ""))
    else:
        base.update(race=pre["race"], state=r["state"], dem=r["dem"], rep=r["rep"], chal=r["chal"],
                    poll_avg=pre.get("poll_avg"), polls=pre.get("polls"))
    rows[cc].append(base)

order = lambda x: (x["status"] == "Called", -min(x["p_win"], 1 - x["p_win"]), x["race"])
for cc, name in (("S", "senate_races"), ("G", "governor_races"), ("H", "house_races")):
    dump(name, sorted(rows[cc], key=order))
dump("senate_open", [r for r in rows["S"] if r["status"] == "Not called"])
dump("governor_open", [r for r in rows["G"] if r["status"] == "Not called"])
watch = []
for cc, office in (("S", "Senate"), ("G", "Governor")):
    for r in rows[cc]:
        if r["status"] == "Called": continue
        fav_pos = r["p_win"] >= 0.5
        watch.append(dict(race=office + " · " + r["race"], favored=r["favored"],
                          fav_name=(r["dem"] if fav_pos else r["rep"]),
                          p_fav=r3(r["p_win"] if fav_pos else 1 - r["p_win"]),
                          p_fav_pre=r3(r["p_pre"] if fav_pos else 1 - r["p_pre"]),
                          rating_now=r["rating_now"], holder=r["holder"],
                          flip_if_fav="Yes" if r["favored"] != r["holder"] else "No"))
watch.sort(key=lambda x: (x["p_fav"], x["race"]))
dump("watch", watch[:12])

# ---- summary, control, distributions
summary = []
for ch in ("senate", "house", "governors"):
    for p in ("D", "R", "I"):
        v = T[ch][p]; pre = pre_sum[(ch, p)]
        summary.append(dict(chamber=ch, party=p, secured=secured[ch][p], leaning=leaning[ch][p], mean=r1(v.mean()),
                            p10=int(np.percentile(v, 10)), p90=int(np.percentile(v, 90)),
                            pre_mean=pre["mean"], pre_central=pre["central"], change_mean=r1(v.mean() - pre["mean"]),
                            now=pre["now"]))
dump("summary", summary)

WON = {"senate": "won or not up", "governors": "won or not up", "house": "safe or called"}
bars = []
for ch in ("senate", "house", "governors"):
    segs = [("D", "won", secured[ch]["D"]), ("D", "lean", leaning[ch]["D"]), ("I", "won", secured[ch]["I"]),
            ("I", "lean", leaning[ch]["I"]), ("", "tossup", tossup[ch]), ("R", "lean", leaning[ch]["R"]),
            ("R", "won", secured[ch]["R"])]
    assert sum(s for _, _, s in segs) == TOTAL[ch], ch
    who = {"D": "Democrats", "R": "Republicans", "I": "Independents", "": "Toss-up"}
    for o, (p, kind, n) in enumerate(segs):
        lab = who[p] + (": " + WON[ch] if kind == "won" else ": favored 60% or more, not called" if kind == "lean"
                        else " (40% to 60%), not called")
        bars.append(dict(chamber=ch, order=o, party=p, kind=kind, seats=n, label=lab, total=TOTAL[ch]))
dump("seatbar", bars)

def pr(x): return r3(np.mean(x))
sc, hc, gc = T["senate"], T["house"], T["governors"]
control = [
    dict(chamber="senate", outcome="D", label="Democrats control (with Sanders and King)", prob_now=pr(sc["D"] + 2 >= 51)),
    dict(chamber="senate", outcome="R", label="Republicans control (50 seats plus VP Vance)", prob_now=pr(sc["R"] >= 50)),
    dict(chamber="senate", outcome="other", label="Majority depends on newly elected independents", prob_now=None),
    dict(chamber="house", outcome="D", label="Democrats win 218+", prob_now=pr(hc["D"] >= 218)),
    dict(chamber="house", outcome="R", label="Republicans win 218+", prob_now=pr(hc["R"] >= 218)),
    dict(chamber="house", outcome="other", label="No party reaches 218", prob_now=None),
    dict(chamber="governors", outcome="D", label="Democrats hold 26+ governorships", prob_now=pr(gc["D"] >= 26)),
    dict(chamber="governors", outcome="R", label="Republicans hold 26+ governorships", prob_now=pr(gc["R"] >= 26)),
    dict(chamber="governors", outcome="other", label="Even split", prob_now=None),
]
for ch in ("senate", "house", "governors"):
    a, b, o = [r for r in control if r["chamber"] == ch]
    o["prob_now"] = round(max(0.0, 1 - a["prob_now"] - b["prob_now"]), 3)
for r in control:
    r["prob_pre"] = pre_ctl[(r["chamber"], r["outcome"])]; r["change"] = r3(r["prob_now"] - r["prob_pre"])
dump("control", control)

dist = []
for ch, thr in (("senate", 49), ("house", 218), ("governors", 26)):
    vals, cnt = np.unique(T[ch]["D"], return_counts=True)
    dist += [dict(chamber=ch, seats=int(s), prob=round(n / N, 4), threshold=thr) for s, n in zip(vals, cnt)]
dump("seat_dist", dist)

# ---- calls log
OFF = {"S": "Senate", "G": "Governor", "H": "House"}
def label(k):
    cc, rest = k[0], k[2:]
    if cc == "H": return "House · " + rest
    return OFF[cc] + " · " + STATE_NAME[rest] + (" (special)" if cc == "S" and rest in ("FL", "OH") else "")
def site(u):
    host = u.split("/")[2].replace("www.", "") if "//" in u else u
    return {"cnn.com": "CNN", "foxnews.com": "Fox News", "nbcnews.com": "NBC News", "apnews.com": "AP",
            "cbsnews.com": "CBS News", "abcnews.go.com": "ABC News", "abcnews.com": "ABC News"}.get(host, host)
row_of = {r["id"]: r for cc in rows for r in rows[cc]}
log = []
for k, c in called.items():
    rr = row_of[k]
    log.append(dict(race=label(k), id=k, winner=c["winner"], party=c["party"], called_by=c["called_by"],
                    seen_et=c["seen_et"], status="Counted", flip=rr["flip"], upset=rr["upset"],
                    p_pre_winner=r3(rr["p_pre"] if c["party"] == rr["pos"] else 1 - rr["p_pre"]),
                    note=c.get("note", ""), url=c["url"], source=site(c["url"])))
for p in pending:
    if p["id"] not in row_of: continue
    rr = row_of[p["id"]]
    log.append(dict(race=label(p["id"]), id=p["id"] + "*", winner=p["leader"], party=p["party"], called_by=p["called_by"],
                    seen_et=p["seen_et"], status="Not yet counted", flip="", upset="",
                    p_pre_winner=r3(rr["p_pre"] if p["party"] == rr["pos"] else 1 - rr["p_pre"]),
                    note=p.get("note", ""), url=p["url"], source=site(p["url"])))
log.sort(key=lambda x: (x["status"] != "Counted", x["seen_et"], x["race"]), reverse=False)
log = [x for x in log if x["status"] == "Counted"][::-1] + [x for x in log if x["status"] != "Counted"]
dump("calls", log)
dump("latest", [dict(race=x["race"], winner=x["winner"], party=x["party"], called_by=x["called_by"], seen_et=x["seen_et"]) for x in log if x["status"] == "Counted"][:10])

# ---- params
cp = os.path.join(HERE, "control_calls.json")
CTRL = json.load(open(cp)) if os.path.exists(cp) and not NOCALLS else {}
chk_path = os.path.join(HERE, "checked.txt")
chk = open(chk_path).read().strip() if os.path.exists(chk_path) else max([c["seen_et"] for c in calls] or ["2026-11-03 19:00"])
et = datetime.strptime(chk, "%Y-%m-%d %H:%M"); ams = et + timedelta(hours=6)
def clock(d): return d.strftime("%-I:%M %p").lower().replace(" ", " ")
as_of = f"{clock(et)} ET on {et.strftime('%b %-d')} ({ams.strftime('%H:%M')} in Amsterdam, {ams.strftime('%b %-d')})"
upsets = sum(1 for x in log if x["status"] == "Counted" and x["upset"] == "Yes")
flips = sum(1 for x in log if x["status"] == "Counted" and x["flip"] == "Yes")
dump("params", [
    dict(key="as_of", label="Calls checked up to", value=as_of),
    dict(key="as_of_et", label="Check time (ET)", value=chk),
    dict(key="called_sen", label="Senate races called", value=n_called["senate"]),
    dict(key="called_gov", label="Governor races called", value=n_called["governors"]),
    dict(key="called_house", label="Competitive House districts called", value=n_called["house"]),
    dict(key="calls_n", label="Calls counted", value=len(called)),
    dict(key="pending_n", label="Calls seen but not counted", value=len(pending)),
    dict(key="upsets", label="Called races won by the forecast's underdog", value=upsets),
    dict(key="flips", label="Called races where the seat changed party", value=flips),
    dict(key="sen_up", label="Senate races", value=35),
    dict(key="gov_up", label="Governor races", value=36),
    dict(key="house_detail", label="Competitive House districts (modelled one by one)", value=len(house)),
    dict(key="safe_d", label="Safe Democratic House seats, counted as won", value=SAFE_D),
    dict(key="safe_r", label="Safe Republican House seats, counted as won", value=SAFE_R),
    dict(key="sen_hold_d", label="Democratic senators not up", value=SEN_HOLD["D"]),
    dict(key="sen_hold_r", label="Republican senators not up", value=SEN_HOLD["R"]),
    dict(key="sen_hold_i", label="Independent senators not up (Sanders, King)", value=SEN_HOLD.get("I", 0)),
    dict(key="gov_hold_d", label="Democratic governors not up", value=GOV_HOLD["D"]),
    dict(key="gov_hold_r", label="Republican governors not up", value=GOV_HOLD["R"]),
    dict(key="draws", label="Shared-error draws", value=S),
    dict(key="ess", label="Effective draws after weighting by the calls", value=int(round(ess))),
    dict(key="nsim", label="Simulated elections after resampling", value=N),
    dict(key="nat_shift", label="Implied national polling miss so far (pts toward D)", value=round(nat_shift, 2)),
    dict(key="nat_sd", label="National polling-miss SD", value=NAT_SD),
    dict(key="control_senate", label="Senate control projected by networks", value=CTRL.get("senate") or "none yet"),
    dict(key="control_house", label="House control projected by networks", value=CTRL.get("house") or "none yet"),
])

# ---- sources
seen = {}
for x in log: seen.setdefault(x["url"], x["source"])
srcs = [dict(title="This model's forecast of 3 November 2026", url="", used_for="probabilities for races not yet called")]
srcs += [dict(title=v, url=u, used_for="race calls") for u, v in seen.items()]
dump("sources", srcs)

print("written to", OUT)
for r in summary: print(r)
for r in control: print(r)
if NOCALLS:
    worst = max(abs(p_now[j] - float(pre_race[k]["p_win"])) for j, k in enumerate(ids))
    print(f"--nocalls check: largest race-probability gap vs the published forecast {worst:.3f}")
