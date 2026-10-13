#!/usr/bin/env python3
"""Collects my commit history into data/activity.json for the strata and topo charts.

Run locally (it needs tokens that can see private repos):

    GH_TOKENS="$(gh auth token -u manuelpenazuniga) $(gh auth token -u entrenatupaes)" python3 tools/collect.py

Only aggregates are written: commits per (weekday, hour) in Santiago time,
commits per (month, language), and commits per month for the two side-project
accounts in SIDE (my personal page charts those). No repo names, no messages.
"""
import json
import os
import sys
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ME = {"manuelpenazuniga", "entrenatupaes", "fundacionrescatedemascotas", "manuelpzdev-bit"}
SIDE = {"entrenatupaes", "fundacionrescatedemascotas"}  # accounts where I'm the only developer
MY_EMAILS = {"manuelpz.dev@gmail.com"}
TZ = ZoneInfo("America/Santiago")
OUT = Path(__file__).resolve().parent.parent / "data" / "activity.json"


def get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"bearer {token}",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as r:
        return json.load(r), r.headers.get("Link", "")


def pages(url, token):
    while url:
        data, link = get(url, token)
        yield from data
        url = next((p.split(";")[0].strip("<> ") for p in link.split(",") if 'rel="next"' in p), None)


def mine(c):
    login = (c.get("author") or {}).get("login")
    email = (c["commit"]["author"] or {}).get("email", "")
    return login in ME or email in MY_EMAILS


def main():
    tokens = os.environ.get("GH_TOKENS", "").split()
    if not tokens:
        sys.exit("set GH_TOKENS")
    repos = {}
    for tok in tokens:
        for r in pages("https://api.github.com/user/repos?per_page=100&affiliation=owner,collaborator,organization_member", tok):
            if not r["fork"] and r["full_name"] not in repos:
                repos[r["full_name"]] = (r["language"] or "Other", tok, r["owner"]["login"])

    clock, strata, seen, last = Counter(), Counter(), set(), None
    owners = {o: {"repos": 0, "commits": 0, "months": Counter()} for o in sorted(SIDE)}
    for name, (lang, tok, owner) in sorted(repos.items()):
        side = owners.get(owner)
        if side:
            side["repos"] += 1
        try:
            commits = list(pages(f"https://api.github.com/repos/{name}/commits?per_page=100", tok))
        except urllib.error.HTTPError:  # empty repo
            continue
        n = 0
        for c in commits:
            if c["sha"] in seen or not mine(c):
                continue
            seen.add(c["sha"])
            t = datetime.fromisoformat(c["commit"]["author"]["date"].replace("Z", "+00:00")).astimezone(TZ)
            clock[f"{t.weekday()},{t.hour}"] += 1
            last = max(last or t, t)
            strata[f"{t:%Y-%m},{lang}"] += 1
            if side:
                side["commits"] += 1
                side["months"][f"{t:%Y-%m}"] += 1
            n += 1
        if not os.environ.get("CI"):  # Actions logs are public; private repo names stay out of them
            print(f"{n:5d}  {lang:12s} {name}", file=sys.stderr)

    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps({
        "generated": datetime.now(TZ).date().isoformat(),
        "timezone": "America/Santiago",
        "commits": len(seen),
        "repos": len(repos),
        "last": f"{last.weekday()},{last.hour + last.minute / 60:.2f}",
        "clock": dict(sorted(clock.items())),
        "strata": dict(sorted(strata.items())),
        "owners": {o: {**v, "months": dict(sorted(v["months"].items()))} for o, v in owners.items()},
    }, indent=1) + "\n")
    print(f"{len(seen)} commits across {len(repos)} repos -> {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
