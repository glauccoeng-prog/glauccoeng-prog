"""Generates the profile activity card (assets/activity-{light,dark}.svg).

Runs daily via GitHub Actions (.github/workflows/stats.yml) with the repository's own
GITHUB_TOKEN — no external stats service, no personal token. The contribution calendar
already includes private contributions as anonymous counts (the profile setting
"Include private contributions" is on), so no private repository is ever read or named.

Safety rules:
- everything is built in memory; files are written only if every API call succeeded,
  otherwise the script exits non-zero and the previous SVGs stay online;
- the card only shows numbers (never repository names).

Local use:  GITHUB_TOKEN=<token> python scripts/generate_stats.py
"""

import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

USER = "glauccoeng-prog"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
API = "https://api.github.com/graphql"

FONT = "-apple-system, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
THEMES = {
    "light": {"bg": "#ffffff", "border": "#d0d7de", "fg": "#1f2328", "dim": "#59636e",
              "acc": "#0969da", "bar": "#2da44e", "bar_dim": "#aceebb", "grid": "#eaeef2"},
    "dark": {"bg": "#0d1117", "border": "#30363d", "fg": "#e6edf3", "dim": "#8b949e",
             "acc": "#58a6ff", "bar": "#3fb950", "bar_dim": "#196c2e", "grid": "#21262d"},
}
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      restrictedContributionsCount
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}"""


def fetch(token):
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "Authorization": f"Bearer {token}", "User-Agent": "profile-activity-card",
        "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    if data.get("errors") or not data.get("data", {}).get("user"):
        raise RuntimeError(f"GraphQL error: {data.get('errors')}")
    col = data["data"]["user"]["contributionsCollection"]
    cal = col["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    if not days:
        raise RuntimeError("empty contribution calendar")
    return cal["totalContributions"], col["restrictedContributionsCount"], days


def monthly(days):
    """Sum per calendar month, oldest first (the first and last months may be partial)."""
    buckets = {}
    for d in days:
        key = d["date"][:7]
        buckets[key] = buckets.get(key, 0) + d["contributionCount"]
    keys = sorted(buckets)[-12:]
    return [(k, buckets[k]) for k in keys]


def card(theme, total, private, months, today):
    t = THEMES[theme]
    w, h = 900, 250
    pct = round(100 * private / total) if total else 0
    chart_x, chart_y, chart_w, chart_h = 440, 44, 424, 150
    peak = max(v for _, v in months) or 1
    slot = chart_w / len(months)
    bar_w = slot * 0.62
    out = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">',
        f'  <title id="t">GitHub activity, last 12 months: {total:,} contributions, {pct}% in private repositories. Monthly totals: '
        + ", ".join(f"{MONTHS[int(k[5:]) - 1]} {k[:4]} {v}" for k, v in months) + "</title>",
        f'  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>',
        f'  <text x="36" y="56" font-family="{FONT}" font-size="15" font-weight="600" fill="{t["dim"]}">ACTIVITY · LAST 12 MONTHS</text>',
        f'  <text x="36" y="112" font-family="{FONT}" font-size="52" font-weight="700" fill="{t["fg"]}">{total:,}</text>',
        f'  <text x="36" y="140" font-family="{FONT}" font-size="17" fill="{t["fg"]}">contributions on GitHub</text>',
        f'  <text x="36" y="180" font-family="{FONT}" font-size="17" fill="{t["fg"]}"><tspan font-weight="700" fill="{t["acc"]}">{pct}%</tspan> in private repositories</text>',
        f'  <text x="36" y="204" font-family="{FONT}" font-size="14" fill="{t["dim"]}">client work under NDA — counted, never shown</text>',
        f'  <text x="36" y="232" font-family="{FONT}" font-size="12" fill="{t["dim"]}">Updated {today} by GitHub Actions in this repository</text>',
    ]
    for i in range(4):
        gy = chart_y + chart_h * i / 3
        out.append(f'  <line x1="{chart_x}" y1="{gy:.1f}" x2="{chart_x + chart_w}" y2="{gy:.1f}" stroke="{t["grid"]}"/>')
    for i, (key, value) in enumerate(months):
        bh = max(2, chart_h * value / peak)
        x = chart_x + i * slot + (slot - bar_w) / 2
        y = chart_y + chart_h - bh
        color = t["bar"] if value >= peak * 0.25 else t["bar_dim"]
        label = MONTHS[int(key[5:]) - 1]
        out.append(f'  <rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" rx="3" fill="{color}"><title>{label} {key[:4]}: {value}</title></rect>')
        out.append(f'  <text x="{x + bar_w / 2:.1f}" y="{chart_y + chart_h + 20}" text-anchor="middle" font-family="{FONT}" font-size="12" fill="{t["dim"]}">{label}</text>')
    out.append(f'  <text x="{chart_x + chart_w}" y="{chart_y - 12}" text-anchor="end" font-family="{FONT}" font-size="12" fill="{t["dim"]}">peak month: {peak:,}</text>')
    out.append("</svg>\n")
    return "\n".join(out)


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is required", file=sys.stderr)
        return 1
    try:
        total, private, days = fetch(token)
        months = monthly(days)
        today = dt.date.today().isoformat()
        svgs = {f"activity-{theme}.svg": card(theme, total, private, months, today) for theme in THEMES}
    except Exception as exc:  # keep the previous SVGs online
        print(f"ERROR, nothing written: {exc}", file=sys.stderr)
        return 1
    OUT_DIR.mkdir(exist_ok=True)
    for name, svg in svgs.items():
        tmp = OUT_DIR / (name + ".tmp")
        tmp.write_text(svg, encoding="utf-8")
        os.replace(tmp, OUT_DIR / name)
    print(f"OK: total={total} private={private} months={months}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
