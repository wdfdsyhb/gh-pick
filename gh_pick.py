#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""gh-pick - score GitHub repos for maintenance & health before you depend on them.

Uses the local `gh` CLI (no token handling of its own) to fetch repo data and
produces a 0-100 health score: release activity, community traction, issue
backlog, and metadata hygiene (license, archive status).

Zero third-party dependencies (needs `gh` on PATH, logged in or not).
"""

import argparse
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

__version__ = "0.1.0"

URL_RE = re.compile(r"^https?://github\.com/")


def parse_repo(arg):
    """Accept 'o/r', a github.com URL, or '.../.git' and return 'owner/repo'."""
    s = arg.strip().rstrip("/")
    s = URL_RE.sub("", s)
    if s.endswith(".git"):
        s = s[:-4]
    parts = s.split("/")
    if len(parts) != 2 or not all(parts):
        raise ValueError(f"expected 'owner/repo' or a github.com URL, got: {arg}")
    return s


def parse_dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def fetch_repo(slug):
    """Fetch repo metadata via the gh CLI (list args only, no shell)."""
    out = subprocess.run(["gh", "api", f"repos/{slug}"],
                         capture_output=True, text=True, timeout=60)
    if out.returncode != 0:
        raise SystemExit(f"gh api failed for {slug}: {out.stderr.strip().splitlines()[-1] if out.stderr else 'unknown error'}")
    return json.loads(out.stdout)


def score(repo, now=None):
    """Score one repo dict (as returned by gh api repos/...). Returns component dict."""
    now = parse_dt(now) if isinstance(now, str) else (now or datetime.now(timezone.utc))
    pushed = parse_dt(repo["pushed_at"])
    days = max(0, (now - pushed).days)

    if days <= 30:
        activity = 30.0
    elif days <= 90:
        activity = 25.0
    elif days <= 180:
        activity = 18.0
    elif days <= 365:
        activity = 10.0
    elif days <= 730:
        activity = 4.0
    else:
        activity = 0.0

    stars = max(0, repo.get("stargazers_count", 0))
    forks = max(0, repo.get("forks_count", 0))
    community = min(25.0, 5 * math.log10(stars + 1) + min(5.0, 3 * math.log10(forks + 1)))

    stars_soft = max(stars, 1)
    ratio = max(0, repo.get("open_issues_count", 0)) / stars_soft
    if ratio < 0.05:
        issues = 20.0
    elif ratio < 0.1:
        issues = 15.0
    elif ratio < 0.3:
        issues = 10.0
    elif ratio < 1.0:
        issues = 5.0
    else:
        issues = 2.0

    meta = 0.0
    if not repo.get("archived"):
        meta += 10.0
    if repo.get("license"):
        meta += 10.0
    if repo.get("description"):
        meta += 2.5
    if repo.get("language"):
        meta += 2.5
    meta = min(20.0, meta)

    total = round(min(100.0, activity + community + issues + meta))
    return {"total": total,
            "activity": round(activity), "community": round(community),
            "issues": round(issues), "meta": round(meta),
            "days_since_push": days}


def verdict(total):
    if total >= 80:
        return "healthy - safe to depend on"
    if total >= 60:
        return "usable - check recent activity yourself"
    return "caution - possibly abandoned or poorly maintained"


def render(results):
    lines = []
    for r in results:
        s = r["score"]
        lines.append(f"{r['full_name']:<40} {s['total']:>3}/100  "
                     f"(act {s['activity']}, comm {s['community']}, iss {s['issues']}, meta {s['meta']}) "
                     f"pushed {s['days_since_push']}d ago - {verdict(s['total'])}")
    return "\n".join(lines)


EXAMPLES = """examples:
  python gh_pick.py owner/repo
  python gh_pick.py owner/repo other/repo --json out.json
  python gh_pick.py https://github.com/owner/repo
"""


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="gh-pick", description=__doc__.strip().splitlines()[0],
        epilog=EXAMPLES, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("repos", nargs="+", help="owner/repo or github.com URL (repeatable)")
    ap.add_argument("--json", dest="json_out", help="write full JSON report to file")
    ap.add_argument("-V", "--version", action="version", version=f"gh-pick {__version__}")
    args = ap.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    try:
        slugs = [parse_repo(r) for r in args.repos]
    except ValueError as e:
        ap.error(str(e))

    results = []
    for slug in slugs:
        repo = fetch_repo(slug)
        s = score(repo)
        results.append({"full_name": repo.get("full_name", slug), "url": repo.get("html_url", ""),
                        "description": repo.get("description") or "",
                        "stars": repo.get("stargazers_count", 0),
                        "open_issues": repo.get("open_issues_count", 0),
                        "archived": repo.get("archived", False),
                        "license": (repo.get("license") or {}).get("spdx_id"),
                        "score": s})
    print(render(results), flush=True)
    if args.json_out:
        Path(args.json_out).expanduser().write_text(
            json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
