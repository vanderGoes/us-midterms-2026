# US 2026 midterms: forecast and results

These are two archived dashboards for the US elections of 3 November 2026: the Senate, the House and the governorships.

| Page | What it shows | As of |
|---|---|---|
| [forecast.html](forecast.html) | A polling-based forecast for every Senate, governor and competitive House race | Polls published up to 2 November 2026 |
| [results.html](results.html) | Races called by news organizations; the forecast fills in the races not yet called | Calls checked up to the evening of 9 November 2026 (ET) |

Both pages are snapshots. They are not updated, and the results page is not an official result. For final results, use the state certifications or the Associated Press.

## Standards

- **Independence.** This is an independent project. It has no funding from, and no affiliation with, any party, campaign, candidate or advocacy group. It does not endorse anyone. Blue and red are the conventional US party colors and carry no other meaning.
- **What counts as a call.** A race is counted once the AP, or at least two of NBC, CNN, Fox News, ABC and CBS, has projected a winner. Calls reported by one outlet only are listed in `model/now/pending.csv` and are not counted. Every call is logged with its source URL in `model/now/calls.csv`.
- **Sources.** Every source used is listed on each page under "How this works" and in the `sources.json` files under `model/`. Some AP calls were taken from outlets that republish them (CNBC, Fox News, States Newsroom, PollsterGraph); the call log gives the URL for each. For most House races called after 4 November, the AP call is inferred: the race was missing from the AP's list of uncalled races on the evening of 9 November. The winner's party for those races comes from CBS's list of seats that changed party, and the call log marks each race where this applies.
- **Corrections.** If you find an error, please open an issue and include a source. Corrections are noted in the commit history.
- **Use of AI.** The model, pages and call log were built with the help of Claude (Anthropic). The code and inputs are published here so the results can be checked and reproduced.

## Method in brief

**Forecast.**
- Each race starts from a prior built from the state's partisan lean, incumbency and expert ratings (Cook, Sabato's Crystal Ball, Inside Elections).
- Polls move the race away from that prior, and more polls move it further. They are weighted for recency, sample size, pollster track record (FiveThirtyEight ratings) and partisan sponsorship.
- Competitive House districts rely on the ratings and partisan lean only.
- 40,000 elections are simulated. The polling errors are correlated at the national, regional and state level and drawn from a fat-tailed distribution.

**Results.** Each called race is fixed to its winner. The calls also tell us how far off the polls were, and the races still open are updated accordingly. The national, regional and state errors are re-estimated from the called races by importance sampling.

## Limitations

- The results page uses calls only, not vote counts. A race with a narrow lead in the count can still show a lopsided probability. Mississippi's Senate race is an example.
- Only 95 competitive House districts are modelled individually. The rest are fixed as safe seats, so seat totals move less than network projections did on the night.
- Expert ratings and some poll data came from secondary sources; these are listed in the sources.

## Reproduce

Requires Python 3 with numpy, pandas and scipy.

```
cd model
mkdir data_raw   # add pollster-ratings-combined.csv and raw_polls.csv from
                 # https://github.com/fivethirtyeight/data/tree/master/pollster-ratings
                 # (rename the first to pollster-ratings_pollster-ratings-combined.csv)
python3 model_final.py && python3 post.py   # forecast  -> model/out/
python3 now/nowcast.py                      # results   -> model/now/out/
cd .. && python3 build.py                   # pages     -> forecast.html, results.html
```

`hist.py` and `hist2.py` rebuild the historical pollster and state error tables from `raw_polls.csv`. With fixed random seeds, the three runs above reproduce the published files exactly.

## License

The code is under the MIT license. Data compiled here is under CC BY 4.0. The pollster ratings and historical polls come from FiveThirtyEight (CC BY 4.0).
