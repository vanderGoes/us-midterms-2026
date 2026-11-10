"""Builds the two self-contained pages, forecast.html and results.html, from the
page templates in model/ and the datasets the model wrote. No network needed.

Usage: python3 build.py
"""
import json, os

ROOT = os.path.dirname(os.path.abspath(__file__))
V = lambda f: open(os.path.join(ROOT, "vendor", f), encoding="utf-8").read()

PAGES = [
    dict(out="forecast.html", page="model/page", data="model/out",
         title="US 2026 midterms: forecast",
         datasets=["summary", "control", "seat_dist", "senate_races", "governor_races", "house_races",
                   "scenarios", "benchmarks", "pollsters", "polls", "cycle_bias", "state_bias", "params", "sources"],
         foot="Forecast of 3 November 2026, polls through 2 November. Not updated with results."),
    dict(out="results.html", page="model/now/page", data="model/now/out",
         title="US 2026 midterms: results and forecast",
         datasets=["summary", "seatbar", "control", "seat_dist", "senate_races", "governor_races", "house_races",
                   "senate_open", "governor_open", "watch", "latest", "calls", "params", "sources"],
         foot="Snapshot of race calls checked to 07:50 ET on 4 November 2026. Races not called by then are filled in by the 3 November forecast. Not updated since."),
]


def build(p):
    rd = lambda f: open(os.path.join(ROOT, p["page"], f), encoding="utf-8").read()
    body = rd("index.html").replace('<meta name="dash-one-writer">\n', "")
    body = body.replace('<link rel="stylesheet" href="style.css">\n', "").replace('<script src="app.js"></script>', "")
    data = {k: json.load(open(os.path.join(ROOT, p["data"], k + ".json"), encoding="utf-8")) for k in p["datasets"]}
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{p["title"]}</title>
<style>
{V("base.css")}
{rd("style.css")}</style></head>
<body><div id="dash-root">
{body.rstrip()}
<p class="mt-foot">{p["foot"]} Built with the help of Claude (Anthropic). Code and data: see README.</p>
</div>
<script>{V("d3.v7.9.1.min.js")}</script>
<script>window.__DASH_DATA__ = {blob};</script>
<script>
{V("dash-shim.js")}</script>
<script>{rd("app.js")}</script>
<script>window.__dashRunAll();</script>
</body></html>
"""
    open(os.path.join(ROOT, p["out"]), "w", encoding="utf-8").write(html)
    print("wrote", p["out"], len(html) // 1024, "KB")


if __name__ == "__main__":
    for p in PAGES:
        build(p)
