#!/usr/bin/env python3
"""Renders the two SVGs on my profile.

  assets/terminal.svg  a replayed shell session (static content, animated with CSS)
  assets/andes.svg     the last year of contributions drawn as a mountain range

Needs GITHUB_TOKEN (or GH_TOKEN) for the GraphQL contributions query.
Runs daily from .github/workflows/andes.yml.
"""
import json
import math
import os
import random
import urllib.request
from datetime import date
from pathlib import Path

USER = "manuelpenazuniga"
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
C = {
    "bg": "#0d1117", "border": "#30363d", "fg": "#c9d1d9", "dim": "#8b949e",
    "green": "#3fb950", "red": "#f85149", "yellow": "#d29922",
    "blue": "#58a6ff", "purple": "#bc8cff", "orange": "#f0883e",
}


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- terminal

# (kind, [(text, color)])   kind: "cmd" is typed out, "out" just appears
SESSION = [
    ("cmd", [("clawcrate run --profile install -- npm install", "fg")]),
    ("out", [("  mode   ", "dim"), ("replica: .env and .git/config never copied", "fg")]),
    ("out", [("  env    ", "dim"), ("scrubbed AWS_SECRET_ACCESS_KEY, GITHUB_TOKEN, SSH_AUTH_SOCK", "fg")]),
    ("out", [("  deny   ", "red"), ("postinstall → open(\"~/.aws/credentials\")  EACCES", "fg")]),
    ("out", [("  done   ", "green"), ("exit 0 · evidence → ~/.clawcrate/runs/exec_7f3a", "fg")]),
    ("cmd", [("clawcrate verify exec_7f3a", "fg")]),
    ("out", [("  ok     ", "green"), ("hash chain intact · ed25519 signature valid", "fg")]),
    ("cmd", [("pennyprompt tail", "fg")]),
    ("out", [("  14:02:11  sonnet  $0.041  session=fix-typo", "dim")]),
    ("out", [("  14:02:13  sonnet  $0.044  session=fix-typo  ", "dim"), ("same tool error ×12", "yellow")]),
    ("out", [("  pause  ", "yellow"), ("runaway loop · burn rate 3.1× baseline", "fg")]),
    ("out", [("  block  ", "red"), ("HTTP 402 {\"retryable\": false} · daily cap $10.00", "fg")]),
    ("cmd", [("# the model proposes. something deterministic decides.", "purple")]),
]


def render_terminal():
    W, LH, FS = 860, 22, 13.5
    CW = FS * 0.62  # generous monospace advance so the typing mask always clears the text
    PAD_X, TOP = 22, 58
    H = TOP + LH * len(SESSION) + 6
    T = 26.0  # seconds per loop

    t, timeline = 0.8, []
    for kind, segs in SESSION:
        n = sum(len(s) for s, _ in segs)
        typing = n * 0.045 if kind == "cmd" else 0
        timeline.append((t, typing))
        t += typing + (0.55 if kind == "cmd" else 0.32)

    pct = lambda s: f"{min(s / T * 100, 99.9):.2f}"
    css, body = [], []
    css.append(f"text{{font-family:{MONO};font-size:{FS}px;white-space:pre}}")
    css.append("@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}")
    css.append(".caret{animation:blink 1s steps(1) infinite}")

    for i, ((kind, segs), (t0, typing)) in enumerate(zip(SESSION, timeline)):
        y = TOP + i * LH
        css.append(
            f"@keyframes l{i}{{0%,{pct(t0)}%{{opacity:0}}{pct(t0 + 0.01)}%,97%{{opacity:1}}100%{{opacity:0}}}}"
            f".l{i}{{opacity:0;animation:l{i} {T}s linear infinite}}"
        )
        x = PAD_X
        parts = []
        if kind == "cmd":
            parts.append(f'<tspan fill="{C["green"]}">~ ❯ </tspan>')
            x += 4 * CW
        parts += [f'<tspan fill="{C[c]}">{esc(s)}</tspan>' for s, c in segs]
        body.append(f'<g class="l{i}"><text x="{PAD_X}" y="{y}" xml:space="preserve">{"".join(parts)}</text>')
        if kind == "cmd":
            n = sum(len(s) for s, _ in segs)
            w = n * CW + 12
            css.append(
                f"@keyframes m{i}{{0%,{pct(t0)}%{{transform:translateX(0)}}"
                f"{pct(t0 + typing)}%,100%{{transform:translateX({w:.0f}px)}}}}"
                f".m{i}{{animation:m{i} {T}s infinite;animation-timing-function:steps({n},end)}}"
            )
            body.append(f'<rect class="m{i}" x="{x - 2:.1f}" y="{y - FS}" width="{w:.0f}" height="{LH}" fill="{C["bg"]}"/>')
        body.append("</g>")

    css.append(
        "@media (prefers-reduced-motion: reduce){g[class^=l]{animation:none;opacity:1}"
        "rect[class^=m]{display:none}.caret{animation:none}}"
    )

    last_y = TOP + (len(SESSION) - 1) * LH
    caret_x = PAD_X + (4 + sum(len(s) for s, _ in SESSION[-1][1])) * FS * 0.6 + 4

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="Terminal session: ClawCrate denies a postinstall script access to AWS credentials and leaves a signed audit trail; PennyPrompt pauses a runaway agent loop and blocks it at the daily budget cap.">
<style>{"".join(css)}</style>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="{C["bg"]}" stroke="{C["border"]}"/>
<circle cx="22" cy="20" r="6" fill="#ff5f57"/><circle cx="42" cy="20" r="6" fill="#febc2e"/><circle cx="62" cy="20" r="6" fill="#28c840"/>
<text x="{W / 2}" y="24" text-anchor="middle" fill="{C["dim"]}" style="font-size:12px">mpz@andes: ~</text>
<line x1="0" y1="38" x2="{W}" y2="38" stroke="{C["border"]}"/>
{"".join(body)}
<g class="l{len(SESSION) - 1}"><rect class="caret" x="{caret_x:.0f}" y="{last_y - FS + 2}" width="8" height="{FS + 3}" fill="{C["fg"]}"/></g>
</svg>
'''
    (ASSETS / "terminal.svg").write_text(svg)


# --------------------------------------------------------------------------- andes

QUERY = """query($login:String!){user(login:$login){contributionsCollection{contributionCalendar{
totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def fetch_weeks():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    cal = json.load(urllib.request.urlopen(req))["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    weeks = [(w["contributionDays"][0]["date"], sum(d["contributionCount"] for d in w["contributionDays"]))
             for w in cal["weeks"]]
    return cal["totalContributions"], weeks


def smooth_path(pts):
    """Catmull-Rom through pts, as cubic beziers."""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def far_range(rng, W, base, amp, step):
    pts, y = [], base
    for x in range(-step, W + 2 * step, step):
        y = max(base - amp, min(base, y + rng.uniform(-amp, amp) * 0.5))
        pts.append((x, y))
    return pts


# a 13x13 alpaca, facing right; feet at the bottom row
ALPACA = [
    "........#.#..",
    "........###..",
    "........####.",
    "........#o###",
    "........###..",
    "........##...",
    "........##...",
    "..#########..",
    ".##########..",
    ".##########..",
    "..#.#...#.#..",
    "..#.#...#.#..",
    "..#.#...#.#..",
]


def alpaca(px=2.2):
    rects = []
    for r, row in enumerate(ALPACA):
        for c, ch in enumerate(row):
            if ch in "#o":
                color = "#1f2328" if ch == "o" else "#f3e9d7"
                rects.append(f'<rect x="{(c - 6.5) * px:.1f}" y="{(r - 13) * px:.1f}" width="{px + 0.15:.2f}" height="{px + 0.15:.2f}" fill="{color}"/>')
    return "".join(rects)


def render_andes(total, weeks):
    W, H = 860, 280
    base = H - 46
    rng = random.Random(USER)
    counts = [c for _, c in weeks]
    top = max(counts) or 1
    step = W / (len(weeks) - 1)
    ridge = [(i * step, base - 6 - 150 * math.sqrt(c / top)) for i, c in enumerate(counts)]
    ridge_d = smooth_path(ridge)
    mountain = f"{ridge_d} L{W},{H} L0,{H} Z"
    snowline = base - 6 - 150 * 0.62

    stars = "".join(
        f'<circle cx="{rng.uniform(0, W):.0f}" cy="{rng.uniform(0, base - 120):.0f}" r="{rng.choice([0.6, 0.8, 1.1])}" '
        f'fill="#fff" opacity="{rng.uniform(0.35, 0.9):.2f}"/>'
        for _ in range(90)
    )
    # Crux, the Southern Cross: Gacrux (top), Acrux (bottom), Becrux (left), Delta (right), Epsilon
    peak_x = ridge[counts.index(top)][0]
    cx, cy = (110 if peak_x > W / 2 else W - 120), 34
    crux = [(0, 0, 2.0), (6, 62, 2.4), (-22, 28, 2.1), (24, 22, 1.6), (9, 40, 1.0)]
    crux_svg = "".join(f'<circle cx="{cx + x}" cy="{cy + y}" r="{r}" fill="#fff"/>' for x, y, r in crux)

    snow_pts = [(x, snowline + 7 * math.sin(x / 23) + rng.uniform(-5, 5)) for x in range(0, W + 9, 9)]
    snow_clip = "M0,0 " + " ".join(f"L{x},{y:.1f}" for x, y in snow_pts) + f" L{W},0 Z"
    far = smooth_path(far_range(rng, W, base - 70, 70, 60)) + f" L{W},{H} L0,{H} Z"
    mid = smooth_path(far_range(rng, W, base - 35, 55, 45)) + f" L{W},{H} L0,{H} Z"

    peak_i = counts.index(top)
    px_, py_ = ridge[peak_i]
    peak_day = date.fromisoformat(weeks[peak_i][0]).strftime("%b %-d")
    anchor = "end" if px_ > W - 160 else "start"
    dx = -8 if anchor == "end" else 8

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total} contributions in the last year, drawn as a mountain range. Redrawn daily.">
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#070b16"/><stop offset="1" stop-color="#1c2541"/></linearGradient>
<linearGradient id="rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#3d4a6b"/><stop offset="1" stop-color="#151b2c"/></linearGradient>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
<clipPath id="snow"><path d="{snow_clip}"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
{stars}{crux_svg}
<path d="{far}" fill="#232c47"/>
<path d="{mid}" fill="#2b3554"/>
<path d="{mountain}" fill="url(#rock)"/>
<path d="{mountain}" fill="#e8edf5" clip-path="url(#snow)" opacity="0.92"/>
<path d="{ridge_d}" fill="none" stroke="#9fb0d6" stroke-opacity="0.35"/>
<rect y="{base + 8}" width="{W}" height="{H}" fill="#0d1117" opacity="0.55"/>
<line x1="{px_:.1f}" y1="{py_ - 2:.1f}" x2="{px_:.1f}" y2="{py_ - 22:.1f}" stroke="#f3e9d7"/>
<path d="M{px_:.1f},{py_ - 22:.1f} l12,4 l-12,4 z" fill="{C["red"]}"/>
<text x="{px_ + dx:.1f}" y="{py_ - 28:.1f}" text-anchor="{anchor}" fill="#f3e9d7" style="font-family:{MONO};font-size:11px">week of {peak_day} · {top}</text>
<g>{alpaca()}<animateMotion dur="60s" repeatCount="indefinite" path="{ridge_d}"/></g>
<text x="18" y="{H - 16}" fill="{C["dim"]}" style="font-family:{MONO};font-size:12px">{total:,} contributions in the last year, as a mountain range · redrawn daily</text>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{C["border"]}"/>
</svg>
'''
    (ASSETS / "andes.svg").write_text(svg)


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    render_terminal()
    render_andes(*fetch_weeks())
