"""The two charts at the bottom of my profile, drawn from data/activity.json.

  strata  commits per month, stacked by language, as a geological cross-section
  topo    when I commit (weekday x hour, Santiago time) as a contour map

Pure Python: a Gaussian KDE and marching squares, no numpy.
"""
import json
import math
from datetime import date

MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"
SERIF = "Georgia, 'Times New Roman', serif"
INK, INK2, MUTED, LINE, BORDER = "#e6edf3", "#9aa4b2", "#5d6675", "#232c3f", "#30363d"
SURFACE = "#0b1020"

# Stack order bottom -> top (older rock at the bottom). Hues are the validated
# reference categorical slots, dark-mode steps, checked adjacent-pairwise against
# SURFACE with the dataviz palette validator (CVD worst dE 13.2, normal 19.3).
LAYERS = [
    ("web & other", "#d55181", {"HTML", "CSS", "JavaScript", "Astro", "Cuda", "Other"}),
    ("Python", "#c98500", {"Python"}),
    ("Solidity", "#9085e9", {"Solidity"}),
    ("Circom", "#199e70", {"Circom"}),
    ("TypeScript", "#3987e5", {"TypeScript"}),
    ("Rust", "#d95926", {"Rust"}),
]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def frame(W, H, body, label, comment, style=""):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{esc(label)}">
<!--
{comment}
-->
<style>text{{font-family:{MONO}}}{style}</style>
<defs><clipPath id="frame"><rect width="{W}" height="{H}" rx="10"/></clipPath></defs>
<g clip-path="url(#frame)"><rect width="{W}" height="{H}" fill="{SURFACE}"/>
{body}
</g>
<rect x="0.5" y="0.5" width="{W - 1}" height="{H - 1}" rx="10" fill="none" stroke="{BORDER}"/>
</svg>
'''


def spline(pts):
    """Catmull-Rom through pts as a bezier path fragment (no leading M)."""
    out = []
    for i in range(len(pts) - 1):
        p0, p1, p2 = pts[max(i - 1, 0)], pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        out.append(f"C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}")
    return " ".join(out)


# --------------------------------------------------------------------------- strata

FERRIS = [  # 11x7, a fossil imprint
    "..#.....#..",
    ".##.....##.",
    "..#######..",
    ".#########.",
    "###########",
    ".#.#...#.#.",
    "#...#.#...#",
]


def months_between(a, b):
    y, m = a
    while (y, m) <= b:
        yield y, m
        y, m = (y, m + 1) if m < 12 else (y + 1, 1)


def render_strata(act, path):
    W, H = 860, 320
    X0, X1, Y0, Y1 = 22, 742, 66, 256
    n = len(LAYERS)
    per = {}
    for k, v in act["strata"].items():
        mo, lang = k.split(",")
        per.setdefault(mo, [0] * n)
        per[mo][next(i for i, (_, _, langs) in enumerate(LAYERS) if lang in langs)] += v
    first = min(per)
    gen = date.fromisoformat(act["generated"])
    months = [f"{y}-{m:02d}" for y, m in months_between((int(first[:4]), int(first[5:])), (gen.year, gen.month))]
    vals = [per.get(m, [0] * n) for m in months]
    N = len(months)

    # A long run of empty months is a gap in the record (an unconformity). Everything
    # before the last gap is old rock: shown compressed, and labelled as such.
    gap, i = None, 0
    while i < N:
        j = i
        while j < N and not sum(vals[j]):
            j += 1
        if j - i >= 6:
            gap = (i, j)
        i = max(j, i + 1)
    widths = [1.0] * N
    if gap:
        for q in range(gap[0]):
            widths[q] = 0.32
        for q in range(*gap):
            widths[q] = 1.4 / (gap[1] - gap[0])
    edges = [0.0]
    for w in widths:
        edges.append(edges[-1] + w)
    centres = [(a + b) / 2 for a, b in zip(edges, edges[1:])]
    sx = lambda u: X0 + (X1 - X0) * u / edges[-1]

    # Smooth each layer with a Gaussian over months (never crosses, never goes negative),
    # sampled finely between month centres.
    SUB, SIG = 10, 0.55
    ts = [t / SUB for t in range(0, (N - 1) * SUB + 1)]
    def smooth(t, li):
        return sum(v[li] * math.exp(-0.5 * ((t - m) / SIG) ** 2) for m, v in enumerate(vals)) / (SIG * math.sqrt(2 * math.pi))
    sm = [[smooth(t, li) for li in range(n)] for t in ts]
    xpos = []
    for t in ts:
        m = min(int(t), N - 2)
        xpos.append(sx(centres[m] + (centres[m + 1] - centres[m]) * (t - m)))

    # Wiggle baseline (Byron & Wattenberg 2008): minimise the layers' summed slope.
    tot = [sum(f) for f in sm]
    g0 = [-sum((n - li) * f[li] for li in range(n)) / (n + 1) for f in sm]
    lo_off, hi_off = min(g0), max(g + t for g, t in zip(g0, tot))
    k = (Y1 - Y0) / (hi_off - lo_off)
    y = lambda v: Y1 - (v - lo_off) * k

    bounds = []
    for li in range(n):
        bot = [g + sum(f[:li]) for g, f in zip(g0, sm)]
        bounds.append((bot, [b + f[li] for b, f in zip(bot, sm)]))

    body = []
    if gap:  # old rock: a faint band behind the compressed years
        ox = sx(edges[gap[0]])
        body.append(f'<rect x="{X0}" y="{Y0 - 6}" width="{ox - X0:.1f}" height="{Y1 - Y0 + 12}" fill="url(#oldrock)"/>')
    for li, (name, color, _) in enumerate(LAYERS):
        bot, top = bounds[li]
        pts = [(x, y(v)) for x, v in zip(xpos, top)] + [(x, y(v)) for x, v in zip(xpos, bot)][::-1]
        d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
        body.append(f'<path d="{d}" fill="{color}" stroke="{SURFACE}" stroke-width="1.5" stroke-linejoin="round"/>')
        body.append(f'<path d="{d}" fill="url(#bedding)"/>')

    def spot(li, width_px, min_px, avoid=None):
        """Sample index where the layer stays at least min_px thick across width_px."""
        bot, top = bounds[li]
        best, best_i = 0, None
        for c in range(len(ts)):
            span = [q for q in range(len(ts)) if abs(xpos[q] - xpos[c]) <= width_px / 2]
            if xpos[c] - width_px / 2 < xpos[0] or xpos[c] + width_px / 2 > xpos[-1]:
                continue
            if avoid is not None and abs(xpos[c] - avoid) < 70:
                continue
            m = min((top[q] - bot[q]) * k for q in span)
            if m > best:
                best, best_i = m, c
        return best_i if best >= min_px else None

    rust_label_x = None
    for li, (name, _, _) in enumerate(LAYERS):
        c = spot(li, len(name) * 6.6 + 8, 13)
        if c is not None:
            bot, top = bounds[li]
            body.append(f'<text x="{xpos[c]:.1f}" y="{y((bot[c] + top[c]) / 2) + 3.6:.1f}" text-anchor="middle" '
                        f'fill="{SURFACE}" style="font-size:10.5px;font-weight:700">{esc(name)}</text>')
            if li == n - 1:
                rust_label_x = xpos[c]

    # Ferris, fossilised somewhere else in the Rust layer
    c = spot(n - 1, 26, 18, avoid=rust_label_x)
    if c is not None:
        bot, top = bounds[-1]
        fx, fy = xpos[c] - 9, y((bot[c] + top[c]) / 2) - 5.5
        body.append("".join(f'<rect x="{fx + cc * 1.6:.1f}" y="{fy + r * 1.6:.1f}" width="1.6" height="1.6" fill="#5e1f08" opacity=".7"/>'
                            for r, row in enumerate(FERRIS) for cc, ch in enumerate(row) if ch == "#"))

    if gap:
        a, b = gap
        gx0, gx1 = sx(edges[a]), sx(edges[b])
        cx_ = (gx0 + gx1) / 2
        zig = " ".join(f"L{cx_ + (3.5 if s % 2 else -3.5):.1f},{Y0 + 4 + s * 8:.1f}" for s in range(1, int((Y1 - Y0) / 8)))
        body.append(f'<path d="M{cx_:.1f},{Y0 - 2} {zig}" fill="none" stroke="{INK2}" stroke-width="1" stroke-dasharray="2 2.5"/>')
        body.append(f'<text x="{cx_ + 8:.1f}" y="{Y0 + 2}" fill="{INK2}" style="font-size:10px;font-style:italic">unconformity</text>'
                    f'<text x="{cx_ + 8:.1f}" y="{Y0 + 13}" fill="{MUTED}" style="font-size:9px">{b - a} months missing</text>')
        body.append(f'<text x="{(X0 + gx0) / 2:.1f}" y="{Y0 - 10}" text-anchor="middle" fill="{MUTED}" style="font-size:9px">compressed</text>')

    # time axis: ticks at the first month and every January, plus where the record resumes
    tick_at = {0} | {q for q, m in enumerate(months) if m.endswith("-01")}
    if gap:
        tick_at = {q for q in tick_at if not gap[0] <= q < gap[1]} | {gap[1]}
    for q in sorted(tick_at):
        tx = sx(edges[q])
        lbl = months[q][:4] if months[q].endswith("-01") or q == 0 else date(int(months[q][:4]), int(months[q][5:]), 1).strftime("%b %Y")
        body.append(f'<line x1="{tx:.1f}" y1="{Y1 + 6}" x2="{tx:.1f}" y2="{Y1 + 11}" stroke="{MUTED}"/>'
                    f'<text x="{tx + 3:.1f}" y="{Y1 + 20}" fill="{MUTED}" style="font-size:10px">{lbl}</text>')

    # rock hammer over the busiest month
    totals = [sum(v) for v in vals]
    jp = totals.index(max(totals))
    c = jp * SUB
    pm = date(int(months[jp][:4]), int(months[jp][5:]), 1).strftime("%b %Y")
    body.append(f'<text x="{xpos[c]:.1f}" y="{y(g0[c] + tot[c]) - 8:.1f}" text-anchor="middle" fill="{INK}" '
                f'style="font-size:11px">⚒ {pm} · {totals[jp]}</text>')

    # drill core: the whole record as one column, with shares
    total = sum(totals)
    shares = [sum(v[li] for v in vals) for li in range(n)]
    cx0, cw = 776, 16
    cy, chh = Y0, Y1 - Y0
    body.append(f'<text x="{cx0 + cw / 2}" y="{Y0 - 10}" text-anchor="middle" fill="{INK2}" style="font-size:10px">core</text>')
    yy = cy + chh
    for li, (name, color, _) in enumerate(LAYERS):
        hseg = chh * shares[li] / total
        yy -= hseg
        body.append(f'<rect x="{cx0}" y="{yy:.1f}" width="{cw}" height="{max(hseg - 1.5, 0.6):.1f}" fill="{color}"/>')
        if hseg >= 11:
            body.append(f'<text x="{cx0 + cw + 5}" y="{yy + hseg / 2 + 3.5:.1f}" fill="{INK2}" style="font-size:9.5px">{100 * shares[li] / total:.0f}%</text>')
    body.append(f'<rect x="{cx0 - 0.5}" y="{cy - 0.5}" width="{cw + 1}" height="{chh + 1}" rx="2" fill="none" stroke="{MUTED}" stroke-opacity=".6"/>')

    legend, lx = [], 22
    for name, color, _ in reversed(LAYERS):
        legend.append(f'<rect x="{lx}" y="36" width="9" height="9" rx="2" fill="{color}"/>'
                      f'<text x="{lx + 14}" y="44.5" fill="{INK2}" style="font-size:10.5px">{esc(name)}</text>')
        lx += 14 + len(name) * 6.6 + 16
    body.insert(0, f'<text x="22" y="22" fill="{INK}" style="font-size:12.5px;font-weight:700">strata</text>'
                   f'<text x="84" y="22" fill="{INK2}" style="font-size:12px">what I have been writing, commits per month by language</text>'
                   + "".join(legend))
    body.append(f'<text x="22" y="{H - 14}" fill="{MUTED}" style="font-size:10.5px">{total:,} commits · {act["repos"]} repos, public and private · '
                f'language = each repo\'s main language · as of {act["generated"]}</text>')

    defs = ('<defs><pattern id="bedding" width="44" height="7" patternUnits="userSpaceOnUse">'
            '<path d="M0,3.5 Q11,2 22,3.5 T44,3.5" fill="none" stroke="#000" stroke-opacity=".22" stroke-width=".7"/></pattern>'
            '<pattern id="oldrock" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">'
            f'<line y2="6" stroke="{LINE}" stroke-width="1.2"/></pattern></defs>')
    gap_note = (f"{months[gap[0]]} to {months[gap[1] - 1]}: {gap[1] - gap[0]} months with no commits. "
                "Geologists call a gap in the rock record an unconformity.") if gap else "no gaps in the record"
    comment = f"""  strata.svg, a cross-section of my commit history.
  - a streamgraph with the wiggle baseline (Byron & Wattenberg, 2008), Gaussian-smoothed per layer
  - older languages sit lower, like older rock
  - {gap_note}
  - the years before the gap are compressed, and say so
  - there is a fossil in the Rust layer
  - colors validated for deuteranopia and protanopia (adjacent pairs, worst dE 13.2)"""
    label = (f"Streamgraph of {total} commits per month by language since {months[0]}. "
             + ", ".join(f"{name} {100 * s / total:.0f}%" for (name, _, _), s in zip(reversed(LAYERS), reversed(shares)))
             + f". Busiest month {pm} with {totals[jp]} commits.")
    path.write_text(frame(W, H, defs + "".join(body), label, comment))


# --------------------------------------------------------------------------- topo

DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
RAMP = ["#111a33", "#15213f", "#1b2a4d", "#22355c", "#2b426d", "#36517f", "#436293"]  # one hue, dark to light


def kde(clock, nx, ny, su=1.1, sv=0.65):
    """Gaussian KDE over a torus (hours wrap at 24, weekdays wrap at 7), in commits per hour per weekday."""
    pts = [(int(k.split(",")[1]) + 0.5, int(k.split(",")[0]) + 0.5, v) for k, v in clock.items()]
    norm = 1 / (2 * math.pi * su * sv)
    grid = []
    for j in range(ny):
        v = (j + 0.5) * 7 / ny
        row = []
        for i in range(nx):
            u = (i + 0.5) * 24 / nx
            s = 0.0
            for pu, pv, c in pts:
                du = min(abs(u - pu), 24 - abs(u - pu))
                dv = min(abs(v - pv), 7 - abs(v - pv))
                s += c * math.exp(-0.5 * ((du / su) ** 2 + (dv / sv) ** 2))
            row.append(s * norm)
        grid.append(row)
    return grid


def march(grid, level):
    """Marching squares: contour segments at `level`, in grid coordinates."""
    segs = []
    ny, nx = len(grid), len(grid[0])
    for j in range(ny - 1):
        for i in range(nx - 1):
            a, b, c, d = grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]
            idx = (a > level) | (b > level) << 1 | (c > level) << 2 | (d > level) << 3
            if idx in (0, 15):
                continue
            t = lambda p, q: (level - p) / (q - p)
            e = {"top": (i + t(a, b), j), "right": (i + 1, j + t(b, c)),
                 "bottom": (i + t(d, c), j + 1), "left": (i, j + t(a, d))}
            pairs = {1: [("left", "top")], 2: [("top", "right")], 3: [("left", "right")], 4: [("right", "bottom")],
                     5: [("left", "top"), ("right", "bottom")], 6: [("top", "bottom")], 7: [("left", "bottom")],
                     8: [("bottom", "left")], 9: [("bottom", "top")], 10: [("top", "right"), ("bottom", "left")],
                     11: [("bottom", "right")], 12: [("right", "left")], 13: [("right", "top")], 14: [("top", "left")]}
            for p, q in pairs[idx]:
                segs.append((e[p], e[q]))
    return segs


def render_topo(act, path):
    W, H = 860, 320
    X0, X1, Y0, Y1 = 64, 796, 46, 254
    nx, ny = 288, 84
    grid = kde(act["clock"], nx, ny)
    gx = lambda i: X0 + (i + 0.5) * (X1 - X0) / nx
    gy = lambda j: Y0 + (j + 0.5) * (Y1 - Y0) / ny
    peak = max(max(r) for r in grid)
    levels = [2 ** p for p in range(1, 12) if 2 ** p < peak]
    band = lambda v: sum(v > l for l in levels)

    body = []
    # hypsometric tint: run-length rows of the same band
    cw, chh = (X1 - X0) / nx, (Y1 - Y0) / ny
    for j, row in enumerate(grid):
        i = 0
        while i < nx:
            b = band(row[i])
            k2 = i
            while k2 < nx and band(row[k2]) == b:
                k2 += 1
            if b:
                body.append(f'<rect x="{X0 + i * cw:.1f}" y="{Y0 + j * chh:.1f}" width="{(k2 - i) * cw + 0.3:.1f}" height="{chh + 0.8:.2f}" fill="{RAMP[min(b, len(RAMP) - 1)]}"/>')
            i = k2

    # graticule
    for h in range(0, 25, 3):
        x = X0 + h * (X1 - X0) / 24
        body.append(f'<line x1="{x:.1f}" y1="{Y0}" x2="{x:.1f}" y2="{Y1}" stroke="{LINE}" stroke-dasharray="1 3"/>')
        if h < 24:
            body.append(f'<text x="{x:.1f}" y="{Y1 + 15}" text-anchor="middle" fill="{MUTED}" style="font-size:10px">{h:02d}h</text>')
    for d, name in enumerate(DAYS):
        body.append(f'<text x="{X0 - 10}" y="{Y0 + (d + 0.5) * (Y1 - Y0) / 7 + 3.5:.1f}" text-anchor="end" fill="{MUTED}" style="font-size:10px">{name}</text>')

    # contours; every other level is an index contour, thicker and labelled
    for li, lv in enumerate(levels):
        segs = march(grid, lv)
        index = li % 2 == 1
        d = " ".join(f"M{gx(a[0]):.1f},{gy(a[1]):.1f}L{gx(b[0]):.1f},{gy(b[1]):.1f}" for a, b in segs)
        body.append(f'<path d="{d}" fill="none" stroke="#e8dcc4" stroke-opacity="{.75 if index else .38}" '
                    f'stroke-width="{1.1 if index else .6}" stroke-linecap="round"/>')
    # summit
    pj, pi = max(((j, i) for j in range(ny) for i in range(nx)), key=lambda p: grid[p[0]][p[1]])
    ph = (pi + 0.5) * 24 / nx
    pd = DAYS[min(int((pj + 0.5) * 7 / ny), 6)]
    sxp, syp = gx(pi), gy(pj)
    # spot heights: every contour labelled where it crosses the row of the summit, left of it
    for lv in levels:
        cross = [(a[0] + (b[0] - a[0]) * (pj + 0.5 - a[1]) / (b[1] - a[1])) for a, b in march(grid, lv)
                 if (a[1] - pj - 0.5) * (b[1] - pj - 0.5) < 0]
        left = [c for c in cross if gx(c) < sxp - 14]
        if left:
            cxl = max(left)
            body.append(f'<text x="{gx(cxl):.1f}" y="{gy(pj + 0.5) + 3.2:.1f}" text-anchor="middle" fill="#e8dcc4" '
                        f'style="font-size:9px;paint-order:stroke" stroke="{RAMP[min(band(grid[pj][int(cxl)]), len(RAMP) - 1)]}" stroke-width="4">{lv}</text>')
    body.append(f'<path d="M{sxp:.1f},{syp - 5:.1f} l5,8 l-10,0 z" fill="{INK}"/>'
                f'<text x="{sxp + 9:.1f}" y="{syp + 3:.1f}" fill="{INK}" style="font-size:10.5px;paint-order:stroke" stroke="{SURFACE}" stroke-width="3">{peak:.0f} · {pd} {int(ph):02d}:{int(ph % 1 * 60):02d}</text>')

    # you are here: the latest commit
    ld, lh = act["last"].split(",")
    yx = X0 + float(lh) * (X1 - X0) / 24
    yy = Y0 + (int(ld) + 0.5) * (Y1 - Y0) / 7
    body.append(f'<circle cx="{yx:.1f}" cy="{yy:.1f}" r="3.2" fill="#d95926" stroke="{SURFACE}" stroke-width="1.5"/>'
                f'<circle cx="{yx:.1f}" cy="{yy:.1f}" r="3.2" fill="none" stroke="#d95926"><animate attributeName="r" values="3.2;11" dur="2.4s" repeatCount="indefinite"/>'
                f'<animate attributeName="stroke-opacity" values=".9;0" dur="2.4s" repeatCount="indefinite"/></circle>'
                f'<text x="{yx - 8:.1f}" y="{yy + 3.5:.1f}" text-anchor="end" fill="{INK}" style="font-size:10px;font-style:italic;paint-order:stroke" stroke="{SURFACE}" stroke-width="3">you are here</text>')

    # here be dragons: the emptiest stretch of the night
    quiet = min(range(0, 9), key=lambda h: sum(grid[j][int(h * nx / 24) + q] for j in range(ny) for q in range(nx // 24)))
    qx = X0 + (quiet + 0.5) * (X1 - X0) / 24
    body.append(f'<text x="{qx:.1f}" y="{(Y0 + Y1) / 2 + 4:.1f}" text-anchor="middle" fill="{INK2}" opacity=".8" '
                f'transform="rotate(-90 {qx:.1f} {(Y0 + Y1) / 2:.1f})" style="font-family:{SERIF};font-size:12px;font-style:italic">here be dragons</text>')

    # map furniture: neatline, north arrow, scale bar, sheet title
    body.append(f'<rect x="{X0 - 0.5}" y="{Y0 - 0.5}" width="{X1 - X0 + 1}" height="{Y1 - Y0 + 1}" fill="none" stroke="{INK2}" stroke-opacity=".7"/>'
                f'<rect x="{X0 - 4}" y="{Y0 - 4}" width="{X1 - X0 + 8}" height="{Y1 - Y0 + 8}" fill="none" stroke="{MUTED}" stroke-opacity=".5"/>')
    nx_, ny_ = X1 + 30, Y0 + 26
    body.append(f'<path d="M{nx_},{ny_ - 16} l6,18 l-6,-5 l-6,5 z" fill="{INK}"/><path d="M{nx_},{ny_ - 16} l6,18 l-6,-5 z" fill="{MUTED}"/>'
                f'<text x="{nx_}" y="{ny_ + 16}" text-anchor="middle" fill="{INK2}" style="font-size:10px">N</text>')
    sb = 3 * (X1 - X0) / 24
    body.append(f'<g transform="translate({X1 - sb},{Y1 + 28})"><rect width="{sb / 2:.1f}" height="4" fill="{INK2}"/>'
                f'<rect x="{sb / 2:.1f}" width="{sb / 2:.1f}" height="4" fill="none" stroke="{INK2}" stroke-width=".8"/>'
                f'<text y="15" fill="{MUTED}" style="font-size:9.5px">0</text><text x="{sb:.1f}" y="15" text-anchor="end" fill="{MUTED}" style="font-size:9.5px">3 h</text></g>')
    contour_note = "contour interval: powers of two, commits per hour"
    body.insert(0, f'<text x="22" y="24" fill="{INK}" style="font-size:12.5px;font-weight:700">topo</text>'
                   f'<text x="68" y="24" fill="{INK2}" style="font-size:12px">when I commit, Santiago time</text>'
                   f'<text x="{W - 22}" y="24" text-anchor="end" fill="{MUTED}" style="font-size:10.5px">sheet 0x2A · 33°27′S</text>')
    body.append(f'<text x="22" y="{H - 14}" fill="{MUTED}" style="font-size:10.5px">{act["commits"]:,} commits · Gaussian KDE on a torus (24 h × 7 days wrap) · {contour_note}</text>')

    comment = """  topo.svg, a contour map of when I commit.
  - kernel density estimate on a torus: Sunday night flows into Monday morning, 23:59 into 00:00
  - contours by marching squares, written by hand; index contours every other level
  - the contour interval is powers of two, because of course it is
  - the dragons live where the commits don't
  - sheet 0x2A: you know why"""
    label = (f"Contour map of {act['commits']} commits by weekday and hour, Santiago time. "
             f"Busiest: {pd} around {int(ph):02d}:00. Fewest commits around {quiet:02d}:00.")
    path.write_text(frame(W, H, "".join(body), label, comment))


def render_all(root):
    act = json.loads((root / "data" / "activity.json").read_text())
    render_strata(act, root / "assets" / "strata.svg")
    render_topo(act, root / "assets" / "topo.svg")
