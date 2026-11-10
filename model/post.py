"""Writes out/benchmarks.json and out/sources.json for the 3 Nov 2026 rerun."""
import json
S = json.load(open("out/summary.json")); C = json.load(open("out/control.json"))
cen = {(r["chamber"], r["party"]): r["central"] for r in S}
ctl = {(r["chamber"], r["outcome"]): r["prob"] for r in C}
NW = "https://www.newsweek.com/nate-silver-says-gop-could-be-in-for-long-night-as-final-polls-drop-12648643"
bench = [
 dict(source="This model", date="2026-11-03", senate_dem_control=ctl[("senate", "D")], house_dem_control=ctl[("house", "D")],
      senate_dem_seats=cen[("senate", "D")] + 2, house_dem_seats=cen[("house", "D")], governors_dem=cen[("governors", "D")],
      note="Polls through 2 Nov; Senate seats include Sanders and King", url=""),
 dict(source="Silver Bulletin (FLIPR)", date="2026-11-01", senate_dem_control=0.801, house_dem_control=None, senate_dem_seats=None,
      house_dem_seats=None, governors_dem=None,
      note="Senate odds as reported 1-2 Nov; its final House odds were not in sources we could read (95% on 22 Oct)", url=NW),
 dict(source="Decision Desk HQ", date="2026-11-02", senate_dem_control=0.65, house_dem_control=0.84, senate_dem_seats=52,
      house_dem_seats=241, governors_dem=None, note="Final forecast", url="https://votes.decisiondeskhq.com/forecast/2026"),
 dict(source="Race to the WH", date="2026-11-01", senate_dem_control=0.794, house_dem_control=None, senate_dem_seats=53,
      house_dem_seats=None, governors_dem=None, note="As reported by Newsweek", url=NW),
 dict(source="Kalshi", date="2026-11-02", senate_dem_control=0.75, house_dem_control=0.941, senate_dem_seats=None,
      house_dem_seats=None, governors_dem=None, note="Market prices, 2 Nov, 2:11 pm ET", url="https://news.kalshi.com/p/2026-midterm-predictions"),
 dict(source="Sabato's Crystal Ball, final ratings", date="2026-11-02", senate_dem_control=None, house_dem_control=None,
      senate_dem_seats=53, house_dem_seats=239, governors_dem=28, note="Seats rated at least Leans D; no toss-ups left",
      url="https://centerforpolitics.org/crystalball/2026finalratings/"),
 dict(source="Cook Political Report ratings", date="2026-10-30", senate_dem_control=None, house_dem_control=None,
      senate_dem_seats=None, house_dem_seats=222, governors_dem=None,
      note="House seats rated Solid, Likely or Lean D; 17 toss-ups not counted", url="https://news.kalshi.com/p/2026-midterm-predictions"),
 dict(source="Dave Manuel forecast", date="2026-10-24", senate_dem_control=0.621, house_dem_control=0.947, senate_dem_seats=None,
      house_dem_seats=None, governors_dem=27, note="Last version we could read", url="https://www.davemanuel.com/2026-midterm-forecast.php"),
]
json.dump(bench, open("out/benchmarks.json", "w"), indent=0, ensure_ascii=False)

src = [
 ("PollCheck: US midterms 2026 polls", "https://www.pollcheck.co.uk/us-midterms-2026",
  "Poll-level data for every Senate and governor race with polls and generic ballot polls (updated 2 Nov); averages for 12 governor races"),
 ("PollCheck: governor races", "https://www.pollcheck.co.uk/us-midterms-2026/governors", "Governor averages used for aggregate-only races, 2 Nov"),
 ("Wikipedia: 2026 Senate elections", "https://en.wikipedia.org/wiki/2026_United_States_Senate_elections", "Nominees, PVI and forecaster ratings (late September)"),
 ("Wikipedia: 2026 gubernatorial elections", "https://en.wikipedia.org/wiki/2026_United_States_gubernatorial_elections", "Nominees, PVI and ratings"),
 ("Wikipedia: 2026 House election ratings", "https://en.wikipedia.org/wiki/2026_United_States_House_of_Representatives_election_ratings", "District PVI on 2026 maps and incumbents"),
 ("Sabato's Crystal Ball: final 2026 ratings", "https://centerforpolitics.org/crystalball/2026finalratings/", "Final Senate, governor and House ratings, 2 Nov; benchmark seat totals"),
 ("Sabato's Crystal Ball: rating changes with a week to go", "https://centerforpolitics.org/crystalball/democrats-appear-to-hold-narrow-senate-edge-with-week-to-go-rating-changes-for-senate-house-and-governors/", "Senate, governor and House changes, 27 Oct"),
 ("Sabato's Crystal Ball: Louisiana and Minnesota changes", "https://centerforpolitics.org/crystalball/a-rating-change-appetizer-senate-changes-in-louisiana-and-minnesota/", "Senate changes before the final ratings"),
 ("Yonkers Times: NY-17 final Crystal Ball rating", "https://yonkerstimes.com/ny-17-moves-from-toss-up-to-lean-republican-on-sabatos-crystal-ball", "Which final Crystal Ball toss-ups went to each party"),
 ("Yellowhammer News: AL-2 final Crystal Ball rating", "https://yellowhammernews.com/sabatos-crystal-ball-moves-alabamas-2nd-district-to-leans-democratic-in-final-2026-ratings/", "Final Crystal Ball House totals and AL-2"),
 ("270toWin: Crystal Ball governor ratings", "https://www.270towin.com/2026-governor-election/sabatos-crystal-ball-2026-governor", "Crystal Ball governor changes, 29 Sep and 6 Oct"),
 ("Political.org: 2026 House elections", "https://political.org/2026-house-elections/", "Cook House changes of 23 and 30 Oct"),
 ("Political.org: Cook Senate changes, 20 Oct", "https://political.org/2026/10/20/cook-political-report-shifts-minnesota-senate-race-toward-gop-south-carolina-toward-democrats/", "Cook ratings for Minnesota, South Carolina and Mississippi"),
 ("Washington Post via DNyuz: Cook governor changes", "https://dnyuz.com/?p=299745", "Cook governor changes, 13 Oct"),
 ("270toWin: Cook House ratings table", "https://270towin.com/2026-house-election/table/cook-political-report-2026-house-ratings", "Cook House ratings, 23 Oct"),
 ("270toWin: Sabato House ratings table", "https://www.270towin.com/2026-house-election/table/crystal-ball-2026-house-forecast/", "Crystal Ball House ratings, 27 Oct"),
 ("270toWin: Inside Elections House table", "https://www.270towin.com/2026-house-election/table/inside-elections-2026-house-ratings/", "Inside Elections House ratings, 15 Oct"),
 ("270toWin: House consensus table", "https://www.270towin.com/2026-house-election/table/consensus-2026-house-forecast/", "Consensus ratings and safe-seat totals, 23 Oct"),
 ("270toWin: Senate forecasts page", "https://www.270towin.com/2026-senate-election-predictions/", "October Senate rating changes"),
 ("FiveThirtyEight pollster-ratings data", "https://github.com/fivethirtyeight/data/tree/master/pollster-ratings", "Historical polls 1998-2022 and 2024 pollster ratings: pollster accuracy, sponsored-poll lean, state misses, margin compression"),
 ("ABC News/538: 2024 polls underestimated Trump", "https://abcnews.com/538/2024-polls-accurate-underestimated-trump/story?id=115652118", "2024 polling bias"),
 ("RealClearPolling: polls undercounted Democrats (2025)", "https://www.realclearpolling.com/stories/analysis/how-polls-undercounted-democratic-support-on-tuesday", "2025 New Jersey and Virginia polling misses"),
 ("Silver Bulletin: 2025 pollster review", "https://www.natesilver.net/p/actually-sometimes-polls-underestimate", "2025 pollster performance adjustments"),
 ("Policymap: redistricting tracker", "https://www.policymap.com/blog/redistricting-tracker", "Which new maps are in force"),
 ("Ballotpedia: redistricting ahead of 2026", "https://ballotpedia.org/Redistricting_ahead_of_the_2026_elections", "Mid-decade redistricting background"),
 ("Just the News: Kiley advances as independent", "https://justthenews.com/politics-policy/elections/former-republican-kevin-kiley-advances-california-general-election", "CA-6 independent incumbent"),
 ("Newsweek: final polls and forecasts, 2 Nov", NW, "Benchmark (Silver Bulletin, Race to the WH)"),
 ("Decision Desk HQ: 2026 forecast", "https://votes.decisiondeskhq.com/forecast/2026", "Benchmark"),
 ("Kalshi: 2026 midterm predictions", "https://news.kalshi.com/p/2026-midterm-predictions", "Benchmark (market prices, Cook House rating totals)"),
 ("Dave Manuel: 2026 midterm forecast", "https://www.davemanuel.com/2026-midterm-forecast.php", "Benchmark (24 Oct)"),
]
json.dump([dict(title=t, url=u, used_for=w) for t, u, w in src], open("out/sources.json", "w"), indent=0, ensure_ascii=False)
print(len(bench), "benchmarks;", len(src), "sources")
