"""Builds the static SVGs of the profile README (header, stack grid, contact buttons).

Everything is rendered into assets/ and committed, so the README never depends on
an external image service. Icons come from assets/icons/ (skill-icons, MIT).

Usage:  python scripts/build_static_assets.py
"""

import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = ASSETS / "icons"

FONT = "-apple-system, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"

THEMES = {
    "light": {"bg": "#ffffff", "panel": "#f6f8fa", "border": "#d0d7de", "fg": "#1f2328",
              "dim": "#59636e", "acc": "#0969da", "ok": "#1a7f37", "bad": "#cf222e"},
    "dark": {"bg": "#0d1117", "panel": "#161b22", "border": "#30363d", "fg": "#e6edf3",
             "dim": "#8b949e", "acc": "#58a6ff", "ok": "#3fb950", "bad": "#f85149"},
}

# (label, [(icon file stem, tooltip)]) — only tools backed by real work (see FICHA-MESTRA)
STACK = [
    ("Languages", [("TypeScript", "TypeScript"), ("JavaScript", "JavaScript"), ("Python", "Python"),
                   ("GoLang", "Go"), ("C", "C"), ("CPP", "C++"), ("Bash", "Bash")]),
    ("Front-end", [("React", "React"), ("NextJS", "Next.js"), ("Angular", "Angular"),
                   ("ReactiveX", "RxJS"), ("TailwindCSS", "Tailwind CSS"), ("Sass", "Sass")]),
    ("Back-end & data", [("NodeJS", "Node.js"), ("ExpressJS", "Express"), ("Django", "Django"),
                         ("PostgreSQL", "PostgreSQL"), ("Firebase", "Firebase")]),
    ("Testing & tooling", [("Vitest", "Vitest"), ("Jest", "Jest"), ("Cypress", "Cypress"),
                           ("Docker", "Docker"), ("GithubActions", "GitHub Actions"),
                           ("Linux", "Linux"), ("Git", "Git")]),
]
EXTRA_CHIPS = ["Playwright", "pytest", "Terminal-Bench / Harbor", "libFuzzer + sanitizers"]


def icon_data_uri(stem, theme):
    """Themed variant when it exists (Name-Dark.svg / Name-Light.svg), else the single file."""
    variant = ICONS / f"{stem}-{theme.capitalize()}.svg"
    path = variant if variant.exists() else ICONS / f"{stem}.svg"
    return "data:image/svg+xml;base64," + base64.b64encode(path.read_bytes()).decode()


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(theme):
    t = THEMES[theme]
    w, h = 900, 190
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">
  <title id="t">Glaucco Siqueira — Software Engineer · AI coding-agent evaluation · Full stack</title>
  <style>
    .cur {{ animation: blink 1.1s steps(1) infinite; }}
    @keyframes blink {{ 50% {{ opacity: 0; }} }}
    @media (prefers-reduced-motion: reduce) {{ .cur {{ animation: none; }} }}
  </style>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t['bg']}" stroke="{t['border']}"/>
  <text x="36" y="72" font-family="{FONT}" font-size="38" font-weight="700" fill="{t['fg']}">Glaucco Siqueira</text>
  <text x="36" y="108" font-family="{FONT}" font-size="19" fill="{t['acc']}" font-weight="600">Software Engineer · AI coding-agent evaluation · Full stack</text>
  <text x="36" y="140" font-family="{FONT}" font-size="15" fill="{t['dim']}">Benchmark tasks, verifiers and Docker environments for AI labs</text>
  <text x="36" y="166" font-family="{FONT}" font-size="15" fill="{t['dim']}">Brasília, Brazil · full-time in Brazil or remote for US teams</text>
  <g transform="translate(598 34)">
    <rect width="266" height="122" rx="10" fill="{t['panel']}" stroke="{t['border']}"/>
    <circle cx="16" cy="15" r="4.5" fill="#ff5f56"/><circle cx="31" cy="15" r="4.5" fill="#ffbd2e"/><circle cx="46" cy="15" r="4.5" fill="#27c93f"/>
    <text x="16" y="48" font-family="{MONO}" font-size="13" fill="{t['fg']}"><tspan fill="{t['acc']}">$</tspan> run --agent oracle</text>
    <text x="16" y="68" font-family="{MONO}" font-size="13" fill="{t['dim']}">  reward <tspan fill="{t['ok']}" font-weight="700">1.0</tspan></text>
    <text x="16" y="92" font-family="{MONO}" font-size="13" fill="{t['fg']}"><tspan fill="{t['acc']}">$</tspan> run --agent nop</text>
    <text x="16" y="112" font-family="{MONO}" font-size="13" fill="{t['dim']}">  reward <tspan fill="{t['bad']}" font-weight="700">0.0</tspan><tspan class="cur" fill="{t['fg']}"> ▍</tspan></text>
  </g>
</svg>
"""


def stack(theme):
    t = THEMES[theme]
    size, gap, label_w, row_h, pad = 44, 12, 190, 66, 24
    max_icons = max(len(icons) for _, icons in STACK)
    chips_w = 48 + sum(16 + 7.6 * len(c) + 10 for c in EXTRA_CHIPS) - 10
    w = int(pad * 2 + max(label_w + max_icons * (size + gap) - gap, chips_w))
    h = pad + len(STACK) * row_h + 46 + pad
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="t">',
           '  <title id="t">Tech stack: ' + esc("; ".join(f"{lab}: " + ", ".join(tip for _, tip in icons) for lab, icons in STACK)) + "</title>",
           f'  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{t["bg"]}" stroke="{t["border"]}"/>']
    y = pad
    for label, icons in STACK:
        out.append(f'  <text x="{pad}" y="{y + size / 2 + 6}" font-family="{FONT}" font-size="16" font-weight="600" fill="{t["fg"]}">{esc(label)}</text>')
        x = pad + label_w
        for stem, tip in icons:
            out.append(f'  <image x="{x}" y="{y}" width="{size}" height="{size}" href="{icon_data_uri(stem, theme)}"><title>{esc(tip)}</title></image>')
            x += size + gap
        y += row_h
    # chips for tools without an icon
    x = pad
    out.append(f'  <text x="{x}" y="{y + 20}" font-family="{FONT}" font-size="14" fill="{t["dim"]}">Also:</text>')
    x += 48
    for chip in EXTRA_CHIPS:
        cw = 16 + 7.6 * len(chip)
        out.append(f'  <rect x="{x}" y="{y + 3}" width="{cw:.0f}" height="26" rx="13" fill="{t["panel"]}" stroke="{t["border"]}"/>')
        out.append(f'  <text x="{x + cw / 2:.0f}" y="{y + 21}" text-anchor="middle" font-family="{MONO}" font-size="13" fill="{t["fg"]}">{esc(chip)}</text>')
        x += cw + 10
    out.append("</svg>\n")
    return "\n".join(out)


def button(text, bg, fg="#ffffff", w=None, stroke="none"):
    w = w or int(40 + 8.4 * len(text))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="40" viewBox="0 0 {w} 40" role="img" aria-label="{esc(text)}">
  <rect x="0.75" y="0.75" width="{w - 1.5}" height="38.5" rx="8" fill="{bg}" stroke="{stroke}" stroke-width="1.5"/>
  <text x="{w / 2}" y="26" text-anchor="middle" font-family="{FONT}" font-size="15" font-weight="600" fill="{fg}">{esc(text)}</text>
</svg>
"""


def main():
    ASSETS.mkdir(exist_ok=True)
    for theme in THEMES:
        (ASSETS / f"header-{theme}.svg").write_text(header(theme), encoding="utf-8")
        (ASSETS / f"stack-{theme}.svg").write_text(stack(theme), encoding="utf-8")
    (ASSETS / "btn-linkedin.svg").write_text(button("LinkedIn · glaucco-siqueira", "#0a66c2"), encoding="utf-8")
    (ASSETS / "btn-email.svg").write_text(button("Email · glauccoeng@gmail.com", "#1f2328", stroke="#8b949e"), encoding="utf-8")
    print("OK: header, stack and buttons written to", ASSETS)


if __name__ == "__main__":
    main()
