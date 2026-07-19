#!/usr/bin/env python3
"""Generate a custom GitHub stats card (assets/stats.svg) in the Sleek Aurora style.

Runs in CI (see .github/workflows/stats.yml) using the repo's GITHUB_TOKEN.
Fetches all-time authored commits, last-12-months contributions, and language
count, then renders a small animated SVG. Self-hosted → no dependency on the
(frequently down) public github-readme-stats service.
"""
import json
import os
import urllib.request

USER = os.environ.get("USERNAME", "Akshit7103")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN") or ""


def _rest(url):
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "stats-gen",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def _graphql(query):
    body = json.dumps({"query": query}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {TOKEN}",
        "User-Agent": "stats-gen",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def total_commits():
    try:
        return _rest(f"https://api.github.com/search/commits?q=author:{USER}&per_page=1")["total_count"]
    except Exception as e:  # noqa: BLE001
        print("commits fetch failed:", e)
        return 0


def contributions_and_langs():
    q = ('{ user(login:"%s"){ '
         'contributionsCollection{ contributionCalendar{ totalContributions } } '
         'repositories(first:100, ownerAffiliations:OWNER){ nodes{ primaryLanguage{ name } } } } }') % USER
    try:
        d = _graphql(q)["data"]["user"]
        contribs = d["contributionsCollection"]["contributionCalendar"]["totalContributions"]
        langs = sorted({n["primaryLanguage"]["name"] for n in d["repositories"]["nodes"] if n.get("primaryLanguage")})
        return contribs, len(langs)
    except Exception as e:  # noqa: BLE001
        print("graphql fetch failed:", e)
        return 0, 0


commits = total_commits()
contribs, langs = contributions_and_langs()

tiles = [
    ("Total Commits", commits, "#36BCF7"),
    ("Contributions · 12 mo", contribs, "#eaf4f8"),
    ("Languages", langs, "#eaf4f8"),
]
centers = [110, 310, 510]

parts = []
for i, ((label, value, color), cx) in enumerate(zip(tiles, centers)):
    begin = 0.2 + i * 0.18
    parts.append(
        f'''  <g opacity="0">
    <animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{begin:.2f}s" fill="freeze"/>
    <animateTransform attributeName="transform" type="translate" from="0 10" to="0 0" dur="0.5s" begin="{begin:.2f}s" fill="freeze"/>
    <text x="{cx}" y="98" text-anchor="middle" font-size="33" font-weight="800" fill="{color}">{value:,}</text>
    <text x="{cx}" y="122" text-anchor="middle" font-size="11.5" letter-spacing="0.5" fill="#8fb3c6">{label}</text>
  </g>''')
tiles_block = "\n".join(parts)

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="620" height="150" viewBox="0 0 620 150" fill="none" font-family="'Segoe UI','Helvetica Neue',Helvetica,Arial,sans-serif" role="img" aria-label="GitHub activity stats">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#173540"/>
      <stop offset="1" stop-color="#0f2630"/>
    </linearGradient>
    <linearGradient id="edge" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="#36BCF7" stop-opacity="0"/>
      <stop offset="0.5" stop-color="#36BCF7" stop-opacity="0.9"/>
      <stop offset="1" stop-color="#36BCF7" stop-opacity="0"/>
    </linearGradient>
    <filter id="sh" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="5" stdDeviation="9" flood-color="#000000" flood-opacity="0.40"/>
    </filter>
  </defs>
  <rect x="10" y="10" width="600" height="130" rx="16" fill="url(#bg)" stroke="#36BCF7" stroke-opacity="0.3" filter="url(#sh)"/>
  <rect x="32" y="34" width="9" height="9" rx="2" fill="#36BCF7"/>
  <text x="50" y="42" font-size="13" font-weight="700" letter-spacing="2" fill="#8fb3c6">GITHUB ACTIVITY</text>
  <line x1="210" y1="60" x2="210" y2="120" stroke="#2c5364" stroke-opacity="0.55"/>
  <line x1="410" y1="60" x2="410" y2="120" stroke="#2c5364" stroke-opacity="0.55"/>
{tiles_block}
  <rect x="10" y="138" width="600" height="2" fill="url(#edge)"/>
</svg>
'''

os.makedirs("assets", exist_ok=True)
with open("assets/stats.svg", "w", encoding="utf-8") as f:
    f.write(svg)
print(f"generated stats.svg  commits={commits} contribs={contribs} langs={langs}")
