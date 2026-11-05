"""Build streak.svg from GitHub's contribution calendar (all years)."""
import datetime as dt, json, os, urllib.request

USER = os.environ["GITHUB_USER"]
TOKEN = os.environ["GITHUB_TOKEN"]


def gql(query):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query}).encode(),
        headers={"Authorization": f"bearer {TOKEN}"},
    )
    return json.load(urllib.request.urlopen(req))["data"]["user"]


years = gql(f'{{user(login:"{USER}"){{contributionsCollection{{contributionYears}}}}}}')
days = {}
for y in years["contributionsCollection"]["contributionYears"]:
    cal = gql(
        f'{{user(login:"{USER}"){{contributionsCollection(from:"{y}-01-01T00:00:00Z",to:"{y}-12-31T23:59:59Z")'
        "{contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}"
    )["contributionsCollection"]["contributionCalendar"]
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]

today = dt.date.today()
dates = sorted(d for d in days if dt.date.fromisoformat(d) <= today)
total = sum(days[d] for d in dates)
first = next(d for d in dates if days[d])

longest = run = 0
best = (None, None)
start = None
for d in dates:
    if days[d]:
        start = start or d
        run += 1
        if run > longest:
            longest, best = run, (start, d)
    else:
        run, start = 0, None

# Current streak: today counts if it has contributions; otherwise start from yesterday.
cur, i = 0, len(dates) - 1
if not days[dates[i]]:
    i -= 1
cur_end = dates[i]
while i >= 0 and days[dates[i]]:
    cur, i = cur + 1, i - 1
cur_start = dates[i + 1]


def fmt(d):
    return dt.date.fromisoformat(d).strftime("%b %-d, %Y")


def span(a, b):
    return f"{fmt(a)} - {fmt(b)}" if a and b else ""


cols = [
    (f"{total:,}", "Total Contributions", f"{fmt(first)} - Present", "#70a5fd"),
    (str(cur), "Current Streak", span(cur_start, cur_end) if cur else "", "#bf91f3"),
    (str(longest), "Longest Streak", span(*best), "#38bdae"),
]
parts = []
for n, (num, label, sub, color) in enumerate(cols):
    x = 82 + n * 165
    parts.append(
        f'<text x="{x}" y="72" fill="{color}" font-size="28" font-weight="700" text-anchor="middle">{num}</text>'
        f'<text x="{x}" y="106" fill="{color}" font-size="14" text-anchor="middle">{label}</text>'
        f'<text x="{x}" y="132" fill="#a9b1d6" font-size="12" text-anchor="middle">{sub}</text>'
    )
lines = "".join(f'<line x1="{165 * k}" y1="35" x2="{165 * k}" y2="160" stroke="#414868"/>' for k in (1, 2))
svg = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="495" height="175" viewBox="0 0 495 175" '
    "font-family=\"Segoe UI, Ubuntu, sans-serif\">"
    '<rect width="495" height="175" rx="4.5" fill="#1a1b27"/>'
    f"{lines}{''.join(parts)}</svg>"
)
open("streak.svg", "w").write(svg)
print(f"total={total} current={cur} longest={longest} {best}")
