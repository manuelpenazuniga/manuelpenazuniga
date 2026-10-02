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


def catmull(pts):
    """Catmull-Rom through pts, as cubic bezier segments (p1, c1, c2, p2)."""
    segs = []
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        segs.append((p1, c1, c2, p2))
    return segs


def smooth_path(pts):
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for _, c1, c2, p2 in catmull(pts):
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d


def sample(pts, n=24):
    """Points along the spline with cumulative arc length: [(x, y, s)]."""
    out = []
    for p1, c1, c2, p2 in catmull(pts):
        for k in range(n):
            t = k / n
            a, b, c, d = (1 - t) ** 3, 3 * (1 - t) ** 2 * t, 3 * (1 - t) * t * t, t ** 3
            out.append((a * p1[0] + b * c1[0] + c * c2[0] + d * p2[0],
                        a * p1[1] + b * c1[1] + c * c2[1] + d * p2[1]))
    out.append(pts[-1])
    s, res = 0.0, [(out[0][0], out[0][1], 0.0)]
    for (x0, y0), (x1, y1) in zip(out, out[1:]):
        s += math.hypot(x1 - x0, y1 - y0)
        res.append((x1, y1, s))
    return res


def at_x(samples, x):
    """(y, fraction of arc length) where the spline reaches x."""
    for sx, sy, s in samples:
        if sx >= x:
            return sy, s / samples[-1][2]
    return samples[-1][1], 1.0


def far_range(rng, W, base, amp, step):
    pts, y = [], base
    for x in range(-step, W + 2 * step, step):
        y = max(base - amp, min(base, y + rng.uniform(-amp, amp) * 0.5))
        pts.append((x, y))
    return pts


# 13x13 alpaca facing right, feet on the bottom row. r/t/y: an Andean blanket.
ALPACA_BODY = [
    "........#.#..",
    "........###..",
    "........####.",
    "........#o###",
    "........###..",
    "........##...",
    "........##...",
    "..##rtyrt##..",
    ".##########..",
    ".##########..",
]
LEGS = {
    "a": ["..#.#...#.#..", "..#.#...#.#..", "..#.#...#.#.."],
    "b": ["..#.#...#.#..", ".#...#.#...#.", ".#...#.#...#."],
}
PIX = {"#": "#f3e9d7", "o": "#1f2328", "r": "#d1495b", "t": "#2a9d8f", "y": "#edae49"}


def sprite(rows, top, px=2.2):
    out = []
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch in PIX:
                out.append(f'<rect x="{(c - 6.5) * px:.1f}" y="{(top + r - 13) * px:.1f}" '
                           f'width="{px + 0.15:.2f}" height="{px + 0.15:.2f}" fill="{PIX[ch]}"/>')
    return "".join(out)


MORSE = {"4": "....-", "2": "..---"}


def morse_keyframes(msg, unit=0.22):
    events, t = [], 0.0
    for ch in msg:
        for sym in MORSE[ch]:
            events.append((t, 1))
            t += unit if sym == "." else 3 * unit
            events.append((t, 0))
            t += unit
        t += 2 * unit
    t += 8 * unit
    stops = "".join(f"{100 * a / t:.2f}%{{opacity:{'1' if on else '.25'}}}" for a, on in events)
    return f"@keyframes morse{{0%{{opacity:.25}}{stops}100%{{opacity:.25}}}}", t


CONDOR = ("M0,0 C-4,-2 -9,-3.2 -14,-2.2 L-18,-1.4 L-15.5,-0.6 L-18.5,0.4 L-15.5,0.6 L-17.5,1.6 "
          "L-13,1 C-9,0.8 -4,1.2 0,2.2 C4,1.2 9,0.8 13,1 L17.5,1.6 L15.5,0.6 L18.5,0.4 L15.5,-0.6 "
          "L18,-1.4 L14,-2.2 C9,-3.2 4,-2 0,0 Z")


def render_andes(total, weeks):
    W, H = 860, 300
    base = H - 48
    rng = random.Random(USER)
    counts = [c for _, c in weeks]
    top = max(counts) or 1
    step = W / (len(weeks) - 1)
    ridge = [(i * step, base - 6 - 150 * math.sqrt(c / top)) for i, c in enumerate(counts)]
    ridge_d = smooth_path(ridge)
    samples = sample(ridge)
    mountain = f"{ridge_d} L{W},{H} L0,{H} Z"
    snowline = base - 6 - 150 * 0.62

    peak_i = counts.index(top)
    px_, py_ = ridge[peak_i]
    peak_day = date.fromisoformat(weeks[peak_i][0]).strftime("%b %-d")
    right_half = px_ > W / 2
    css = [
        f"text{{font-family:{MONO}}}",
        "@keyframes tw{0%,100%{opacity:1}50%{opacity:.2}}.tw{animation:tw 4s ease-in-out infinite}",
        "@keyframes ss{0%{transform:translate(0,0);opacity:0}.6%{opacity:1}3.5%,100%{transform:translate(-210px,105px);opacity:0}}",
        ".ss1{animation:ss 19s linear 4s infinite;opacity:0}.ss2{animation:ss 31s linear 15s infinite;opacity:0}",
        f"@keyframes sl{{0%{{transform:translate(-140px,46px)}}32%,100%{{transform:translate({W + 80}px,-34px)}}}}",
        ".sl{animation:sl 61s linear 9s infinite;transform:translate(-140px,46px)}",
        "@keyframes mist{from{transform:translateX(0)}to{transform:translateX(-50px)}}",
        ".mist{animation:mist 26s ease-in-out infinite alternate}",
        "@keyframes flick{0%,100%{transform:scaleY(1);opacity:.95}25%{transform:scaleY(.8);opacity:.8}"
        "55%{transform:scaleY(1.12)}80%{transform:scaleY(.9)}}",
        ".fl{transform-box:fill-box;transform-origin:50% 100%;animation:flick .9s ease-in-out infinite}",
        ".fl2{animation-duration:1.3s;animation-delay:-.4s}",
        "@keyframes glow{0%,100%{opacity:.5}50%{opacity:.32}}.glow{animation:glow 1.7s ease-in-out infinite}",
        "@keyframes ember{0%{transform:translate(0,0);opacity:0}15%{opacity:1}100%{transform:translate(3px,-20px);opacity:0}}",
        ".em{animation:ember 2.4s ease-out infinite}",
    ]

    # sky: background stars, the Milky Way, then the bright stuff
    stars = []
    for _ in range(110):
        x, y = rng.uniform(0, W), rng.uniform(0, base - 110)
        r, o = rng.choice([0.5, 0.7, 0.9, 1.1]), rng.uniform(0.3, 0.9)
        if rng.random() < 0.3:
            stars.append(f'<circle class="tw" cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" fill-opacity="{o:.2f}" '
                         f'style="animation-duration:{rng.uniform(2.5, 6):.1f}s;animation-delay:-{rng.uniform(0, 6):.1f}s"/>')
        else:
            stars.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="#fff" fill-opacity="{o:.2f}"/>')
    mw_angle = math.radians(-14)
    for _ in range(160):  # dust along the galactic band
        u, v = rng.uniform(-470, 470), rng.gauss(0, 13)
        x = W * 0.52 + u * math.cos(mw_angle) - v * math.sin(mw_angle)
        y = 72 + u * math.sin(mw_angle) + v * math.cos(mw_angle)
        if 0 < x < W and 0 < y < base - 100:
            stars.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{rng.uniform(0.3, 0.6):.1f}" fill="#dfe6ff" fill-opacity="{rng.uniform(0.25, 0.6):.2f}"/>')

    # Crux and the Pointers (alpha and beta Centauri) on the side away from the summit
    cx, cy = (W - 130 if not right_half else 128), 30
    crux = [(0, 0, 1.9), (6, 60, 2.3), (-21, 27, 2.0), (23, 21, 1.5), (9, 38, 0.9)]
    pointers = [(-62, 70, 2.4), (-44, 56, 1.8)]
    crux_svg = "".join(f'<circle cx="{cx + x}" cy="{cy + y}" r="{r}" fill="#fff"/>' for x, y, r in crux + pointers)

    mx, my = (W * 0.40 if right_half else W * 0.60), 44
    morse_css, morse_T = morse_keyframes("42")
    css.append(morse_css + f".morse{{animation:morse {morse_T:.2f}s steps(1,end) infinite}}")

    # far ranges, the data range, snow
    snow_pts = [(x, snowline + 7 * math.sin(x / 23) + rng.uniform(-5, 5)) for x in range(0, W + 9, 9)]
    snow_clip = "M0,0 " + " ".join(f"L{x},{y:.1f}" for x, y in snow_pts) + f" L{W},0 Z"
    far = smooth_path(far_range(rng, W, base - 72, 70, 60)) + f" L{W},{H} L0,{H} Z"
    mid = smooth_path(far_range(rng, W, base - 36, 55, 45)) + f" L{W},{H} L0,{H} Z"

    # the summit flag and its label
    label = f"week of {peak_day} · {top}"
    label_right = px_ < W - 190
    lx, anchor = (px_ + 9, "start") if label_right else (px_ - 9, "end")

    # camp near the start of the trail
    tx = 58
    ty, _ = at_x(samples, tx)
    fx = tx + 26
    fy, _ = at_x(samples, fx)

    # alpaca: walk out, rest beside the flag, walk on, turn around, walk home to camp
    stop_x = px_ - 15
    _, f = at_x(samples, stop_x)
    speed = 34.0  # seconds for the full ridge
    t1 = speed * f
    t2 = t1 + 4.5 + speed * (1 - f)
    t3 = t2 + 1.2 + speed
    D = t3 + 3.0
    kt = lambda *ts: ";".join(f"{t / D:.4f}" for t in ts)
    motion = (f'<animateMotion dur="{D:.2f}s" repeatCount="indefinite" calcMode="linear" '
              f'keyPoints="0;{f:.4f};{f:.4f};1;1;0;0" keyTimes="{kt(0, t1, t1 + 4.5, t2, t2 + 1.2, t3, D)}" path="{ridge_d}"/>')

    moving = [(0, t1), (t1 + 4.5, t2), (t2 + 1.2, t3)]
    frames, t = [(0.0, "a")], 0.0
    for a, b in moving:
        t, k = a, 0
        while t < b:
            frames.append((t, "b" if k % 2 else "a"))
            t += 0.28
            k += 1
        frames.append((b, "a"))
    frames.sort()
    times = ";".join(f"{min(t / D, 1):.4f}" for t, _ in frames)
    vis = lambda which: ";".join("1" if fr == which else "0" for _, fr in frames)

    def alpaca(facing):
        legs = "".join(
            f'<g>{sprite(LEGS[k], 10)}<animate attributeName="opacity" calcMode="discrete" dur="{D:.2f}s" '
            f'repeatCount="indefinite" keyTimes="{times}" values="{vis(k)}"/></g>' for k in "ab")
        flip = ' transform="scale(-1,1)"' if facing == "left" else ""
        values = "1;0" if facing == "right" else "0;1"
        return (f'<g opacity="{values[0]}"><g{flip}>{sprite(ALPACA_BODY, 0)}{legs}</g>'
                f'<animate attributeName="opacity" calcMode="discrete" dur="{D:.2f}s" repeatCount="indefinite" '
                f'keyTimes="0;{(t2 + 0.6) / D:.4f}" values="{values}"/></g>')

    # the speech bubble rides along with the alpaca, so it always points at its head
    bubble_text = "it compiles."
    bw = len(bubble_text) * 7.2 + 14
    bx, by = 12 - bw, (-52 if label_right else -68)
    bubble = (f'<g opacity="0"><rect x="{bx:.1f}" y="{by}" width="{bw:.0f}" height="19" rx="9" fill="#f3e9d7"/>'
              f'<path d="M{bx + bw - 16:.1f},{by + 19} l6,0 l-1,7 z" fill="#f3e9d7"/>'
              f'<text x="{bx + bw / 2:.1f}" y="{by + 13.5}" text-anchor="middle" fill="#1f2328" style="font-size:11.5px">{bubble_text}</text>'
              f'<animate attributeName="opacity" calcMode="discrete" dur="{D:.2f}s" repeatCount="indefinite" '
              f'keyTimes="{kt(0, t1 + 0.3, t1 + 4.4)}" values="0;1;0"/></g>')

    starlink = "".join(f'<circle cx="{i * 11}" cy="{-i * 1.6:.1f}" r="0.9" fill="#fff" fill-opacity=".85"/>' for i in range(7))
    embers = "".join(f'<circle class="em" cx="{fx + dx}" cy="{fy - 8}" r="0.8" fill="#ffb347" style="animation-delay:-{d}s"/>'
                     for dx, d in ((-2, 0.3), (1, 1.1), (3, 1.9)))

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{total:,} contributions in the last year, drawn as a mountain range under the southern sky, with an alpaca walking the ridge. Redrawn daily.">
<!--
  You opened the source. Nice.
  - the ridge is a Catmull-Rom spline through {len(weeks)} weeks of my contributions
  - the alpaca rests at the busiest week and says what every Rust dev wants to hear
  - one star near the moon is blinking in Morse. It's the answer.
  - the Southern Cross and its two Pointers are roughly where they belong
  - the flag is Ferris orange
  - redrawn every day by .github/workflows/andes.yml
-->
<style>{"".join(css)}@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}</style>
<defs>
<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#05080f"/><stop offset=".65" stop-color="#121a30"/><stop offset="1" stop-color="#26304f"/></linearGradient>
<linearGradient id="rock" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#46547a"/><stop offset=".5" stop-color="#2a3352"/><stop offset="1" stop-color="#12172a"/></linearGradient>
<linearGradient id="snowg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#b9c6e4"/></linearGradient>
<linearGradient id="mistg" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#a9b8de" stop-opacity="0"/><stop offset=".5" stop-color="#a9b8de" stop-opacity=".13"/><stop offset="1" stop-color="#a9b8de" stop-opacity="0"/></linearGradient>
<linearGradient id="ssg" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="70" y2="-35"><stop offset="0" stop-color="#fff"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
<radialGradient id="moonglow"><stop offset="0" stop-color="#f4f1e6" stop-opacity=".22"/><stop offset="1" stop-color="#f4f1e6" stop-opacity="0"/></radialGradient>
<radialGradient id="fireglow"><stop offset="0" stop-color="#ff9a3c" stop-opacity=".55"/><stop offset="1" stop-color="#ff9a3c" stop-opacity="0"/></radialGradient>
<filter id="blur" x="-20%" y="-50%" width="140%" height="200%"><feGaussianBlur stdDeviation="16"/></filter>
<mask id="crescent"><rect width="{W}" height="{H}" fill="#fff"/><circle cx="{mx + 5}" cy="{my - 4}" r="10.5" fill="#000"/></mask>
<clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath>
<clipPath id="snow"><path d="{snow_clip}"/></clipPath>
</defs>
<g clip-path="url(#frame)">
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<ellipse cx="{W * 0.52}" cy="72" rx="470" ry="34" fill="#8ea2e8" opacity=".09" filter="url(#blur)" transform="rotate(-14 {W * 0.52} 72)"/>
<ellipse cx="{W * 0.52}" cy="72" rx="300" ry="12" fill="#cdd8ff" opacity=".06" filter="url(#blur)" transform="rotate(-14 {W * 0.52} 72)"/>
{"".join(stars)}{crux_svg}
<circle cx="{mx}" cy="{my}" r="46" fill="url(#moonglow)"/>
<circle cx="{mx}" cy="{my}" r="11" fill="#f4f1e6" mask="url(#crescent)"/>
<circle class="morse" cx="{mx + 46:.0f}" cy="{my + 30}" r="1.5" fill="#fff"/>
<g class="sl">{starlink}</g>
<g transform="translate({W * 0.78:.0f},26)"><g class="ss1"><line x2="70" y2="-35" stroke="url(#ssg)" stroke-width="1.3" stroke-linecap="round"/></g></g>
<g transform="translate({W * 0.34:.0f},18)"><g class="ss2"><line x2="70" y2="-35" stroke="url(#ssg)" stroke-width="1.1" stroke-linecap="round"/></g></g>
<g><path d="{CONDOR}" fill="#04060c"><animateTransform attributeName="transform" type="rotate" values="-4;4;-4" dur="7s" repeatCount="indefinite"/></path>
<animateMotion dur="83s" begin="6s" repeatCount="indefinite" calcMode="linear" keyPoints="0;1;1" keyTimes="0;.55;1" path="M{W + 40},96 C{W * 0.7:.0f},58 {W * 0.4:.0f},120 -40,70"/></g>
<path d="{far}" fill="#1f2741"/>
<rect class="mist" x="-60" y="{base - 96}" width="{W + 120}" height="60" fill="url(#mistg)"/>
<path d="{mid}" fill="#283150"/>
<rect class="mist" x="-60" y="{base - 52}" width="{W + 120}" height="46" fill="url(#mistg)" style="animation-duration:34s;animation-delay:-9s"/>
<path d="{mountain}" fill="url(#rock)"/>
<path d="{mountain}" fill="url(#snowg)" clip-path="url(#snow)"/>
<path d="{ridge_d}" fill="none" stroke="#cfdcff" stroke-opacity=".45" stroke-width=".8"/>
<rect y="{base + 8}" width="{W}" height="{H}" fill="#0d1117" opacity=".6"/>
<line x1="{px_:.1f}" y1="{py_ - 1:.1f}" x2="{px_:.1f}" y2="{py_ - 24:.1f}" stroke="#f3e9d7" stroke-width="1.2"/>
<path fill="#f74c00" transform="translate({px_ + 0.6:.1f},{py_ - 24:.1f})" d="M0,0 Q7,-1.5 14,2 Q7,4.5 0,8 Z"><animate attributeName="d" dur="1.6s" repeatCount="indefinite" values="M0,0 Q7,-1.5 14,2 Q7,4.5 0,8 Z;M0,0 Q7,1.5 14,3 Q7,7 0,8 Z;M0,0 Q7,-1.5 14,2 Q7,4.5 0,8 Z"/></path>
<text x="{lx:.1f}" y="{py_ - 30:.1f}" text-anchor="{anchor}" fill="#f3e9d7" style="font-size:11px">{label}</text>
<g transform="translate({tx},{ty + 1:.1f})">
<line x1="-24" y1="0" x2="-24" y2="-15" stroke="#8a6a4a" stroke-width="1.4"/><rect x="-31" y="-21" width="14" height="9" rx="1.5" fill="#c9a77c"/>
<text x="-24" y="-13.6" text-anchor="middle" fill="#2b2118" style="font-size:9px;font-weight:700">~</text>
<path d="M-14,0 L0,-19 L14,0 Z" fill="#c2593a"/><path d="M0,-19 L14,0 L6,0 Z" fill="#9b4129"/><path d="M-4,0 L0,-8 L4,0 Z" fill="#1a1410"/>
</g>
<circle class="glow" cx="{fx}" cy="{fy - 3:.1f}" r="22" fill="url(#fireglow)"/>
<g transform="translate({fx},{fy + 1:.1f})"><rect x="-6" y="-2.4" width="12" height="2.4" rx="1" fill="#5a3b22" transform="rotate(12)"/><rect x="-6" y="-2.4" width="12" height="2.4" rx="1" fill="#6b4529" transform="rotate(-12)"/>
<path class="fl" d="M-3.5,-1 Q-4,-6 0,-11 Q4,-6 3.5,-1 Z" fill="#ff8a2a"/><path class="fl fl2" d="M-2,-1 Q-2,-4 0,-7 Q2,-4 2,-1 Z" fill="#ffd166"/></g>
{embers}
<g>{alpaca("right")}{alpaca("left")}{bubble}{motion}</g>
<text x="18" y="{H - 17}" fill="{C["dim"]}" style="font-size:12px">{total:,} contributions in the last year, as a mountain range · redrawn daily</text>
<text x="{W - 18}" y="{H - 17}" text-anchor="end" fill="#484f58" style="font-size:12px">33°27′S 70°40′W</text>
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{C["border"]}"/>
</svg>
'''
    (ASSETS / "andes.svg").write_text(svg)


if __name__ == "__main__":
    ASSETS.mkdir(exist_ok=True)
    render_terminal()
    render_andes(*fetch_weeks())
