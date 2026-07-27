"""Gera os cards de estatísticas do perfil como SVGs estáticos em assets/.

Roda diariamente via GitHub Actions (.github/workflows/stats.yml) usando o
GITHUB_TOKEN do próprio repositório — sem depender de serviços externos que
sofrem rate limit (github-readme-stats, summary-cards etc.).

Uso local:  GITHUB_TOKEN=<token> python scripts/generate_stats.py
Sem token o script ainda funciona (API anônima), apenas omite as métricas
de contribuição que exigem GraphQL.
"""

import json
import os
import sys
import urllib.request
from pathlib import Path

USER = "glauccoeng-prog"
OUT_DIR = Path(__file__).resolve().parent.parent / "assets"
API = "https://api.github.com"

# Cores oficiais de linguagem do GitHub (fallback: paleta do perfil)
LANG_COLORS = {
    "TypeScript": "#3178C6",
    "JavaScript": "#F1E05A",
    "Java": "#B07219",
    "Python": "#3572A5",
    "Go": "#00ADD8",
    "HTML": "#E34C26",
    "CSS": "#563D7C",
    "SCSS": "#C6538C",
    "Shell": "#89E051",
    "Dockerfile": "#384D54",
}
FALLBACK_COLORS = ["#70A5FD", "#BF91F3", "#414868", "#C0CAF5"]

THEMES = {
    "dark": {
        "bg": "#1A1B27",
        "border": "#414868",
        "title": "#70A5FD",
        "label": "#C0CAF5",
        "value": "#C0CAF5",
        "track": "#414868",
        "bullet": "#BF91F3",
    },
    "light": {
        "bg": "#FFFFFF",
        "border": "#D0D7DE",
        "title": "#4A6FD0",
        "label": "#24292F",
        "value": "#24292F",
        "track": "#EAEEF2",
        "bullet": "#4A6FD0",
    },
}

FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"


def clip(text, limit=18):
    """Trunca nomes longos para não estourar a largura fixa (420px) do card."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def request(url, token=None, data=None):
    headers = {"User-Agent": "profile-stats-generator", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def fetch_data(token):
    repos = []
    page = 1
    while True:
        batch = request(f"{API}/users/{USER}/repos?per_page=100&page={page}", token)
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1

    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in repos)

    langs = {}
    for repo in own:
        for lang, size in request(repo["languages_url"], token).items():
            langs[lang] = langs.get(lang, 0) + size

    user = request(f"{API}/users/{USER}", token)

    contributions = None
    if token:
        query = """
        query($login: String!) {
          user(login: $login) {
            contributionsCollection {
              contributionCalendar { totalContributions }
            }
          }
        }"""
        result = request(f"{API}/graphql", token, {"query": query, "variables": {"login": USER}})
        contributions = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

    return {
        "stars": stars,
        "own_repos": len(own),
        "followers": user["followers"],
        "contributions": contributions,
        "langs": sorted(langs.items(), key=lambda kv: kv[1], reverse=True),
    }


def svg_header(theme, title, height):
    t = THEMES[theme]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="420" height="{height}" '
        f'viewBox="0 0 420 {height}" role="img" aria-label="{title}">\n'
        f'  <rect x="0.5" y="0.5" width="419" height="{height - 1}" rx="10" '
        f'fill="{t["bg"]}" stroke="{t["border"]}"/>\n'
        f'  <text x="24" y="38" font-family="{FONT}" font-size="18" font-weight="700" '
        f'fill="{t["title"]}">{title}</text>\n'
    )


def stats_rows(data):
    rows = [("Repositórios próprios", data["own_repos"]),
            ("Estrelas recebidas", data["stars"]),
            ("Seguidores", data["followers"])]
    if data["contributions"] is not None:
        rows.insert(0, ("Contribuições no último ano", data["contributions"]))
    if data["langs"]:
        rows.append(("Linguagem principal", clip(data["langs"][0][0])))
    return rows[:5]


def build_stats_card(theme, data, height):
    t = THEMES[theme]
    rows = stats_rows(data)

    parts = [svg_header(theme, "Visão geral do GitHub", height)]
    y = 72
    for label, value in rows:
        parts.append(f'  <circle cx="30" cy="{y - 5}" r="4" fill="{t["bullet"]}"/>\n')
        parts.append(
            f'  <text x="46" y="{y}" font-family="{FONT}" font-size="14" '
            f'fill="{t["label"]}">{label}</text>\n'
        )
        parts.append(
            f'  <text x="396" y="{y}" text-anchor="end" font-family="{FONT}" font-size="14" '
            f'font-weight="700" fill="{t["value"]}">{value}</text>\n'
        )
        y += 30
    parts.append("</svg>\n")
    return "".join(parts)


def build_langs_card(theme, data, height):
    t = THEMES[theme]
    top = data["langs"][:5]
    total = sum(size for _, size in top) or 1

    parts = [svg_header(theme, "Linguagens mais usadas", height)]
    y = 72
    for i, (lang, size) in enumerate(top):
        pct = 100.0 * size / total
        color = LANG_COLORS.get(lang, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])
        bar_w = max(4, round(150 * pct / 100))
        parts.append(f'  <rect x="24" y="{y - 13}" width="10" height="10" rx="2" fill="{color}"/>\n')
        parts.append(
            f'  <text x="42" y="{y - 3}" font-family="{FONT}" font-size="14" '
            f'fill="{t["label"]}">{clip(lang)}</text>\n'
        )
        parts.append(f'  <rect x="185" y="{y - 12}" width="150" height="8" rx="4" fill="{t["track"]}"/>\n')
        parts.append(f'  <rect x="185" y="{y - 12}" width="{bar_w}" height="8" rx="4" fill="{color}"/>\n')
        parts.append(
            f'  <text x="396" y="{y - 3}" text-anchor="end" font-family="{FONT}" font-size="14" '
            f'font-weight="700" fill="{t["value"]}">{pct:.1f}%</text>\n'
        )
        y += 30
    parts.append("</svg>\n")
    return "".join(parts)


def main():
    token = os.environ.get("GITHUB_TOKEN") or None
    data = fetch_data(token)

    OUT_DIR.mkdir(exist_ok=True)
    # altura única para os dois cards ficarem alinhados lado a lado
    n_rows = max(len(stats_rows(data)), len(data["langs"][:5]))
    height = 62 + 30 * n_rows + 14
    for theme in THEMES:
        (OUT_DIR / f"stats-{theme}.svg").write_text(build_stats_card(theme, data, height), encoding="utf-8")
        (OUT_DIR / f"langs-{theme}.svg").write_text(build_langs_card(theme, data, height), encoding="utf-8")

    print(f"OK: 4 SVGs gerados em {OUT_DIR}")
    print(json.dumps({k: v for k, v in data.items() if k != "langs"}, ensure_ascii=False))
    print("langs:", [(lang, size) for lang, size in data["langs"][:5]])


if __name__ == "__main__":
    sys.exit(main())
