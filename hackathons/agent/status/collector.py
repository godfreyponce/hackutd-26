#!/usr/bin/env python3
"""Live status for one event. Writes hackathons/events/<slug>/status.json every 60 s and serves the page
on the port named in hackathons/events/<slug>/status-config.json.

Run: python3 hackathons/agent/status/collector.py <slug> [--once]   (stdlib + the logged-in `gh` CLI)
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HERE = os.path.dirname(os.path.realpath(__file__))
EVENTS_DIR = os.path.join(HERE, "..", "..", "events")
INTERVAL_S = 60
ISSUE_IN_BRANCH = re.compile(r"issue-(\d+)")
SEP = "\x1f"


def load_config(slug: str) -> dict:
    path = os.path.normpath(os.path.join(EVENTS_DIR, slug, "status-config.json"))
    try:
        with open(path) as f:
            cfg = json.load(f)
    except OSError as e:
        raise SystemExit(f"cannot read {path}: {e.strerror}")
    except ValueError as e:
        raise SystemExit(f"{path}: not valid JSON: {e}")
    for key in ("repo", "checkout", "port"):
        if key not in cfg:
            raise SystemExit(f"{path}: missing required key '{key}'")
    teammates = []
    for i, m in enumerate(cfg.get("teammates", [])):
        for key in ("github", "git"):
            if key not in m:
                raise SystemExit(f"{path}: teammates[{i}] is missing required key '{key}'")
        teammates.append({"github": m["github"], "git": re.compile(m["git"], re.I)})
    return {"repo": cfg["repo"], "checkout": os.path.abspath(os.path.expanduser(cfg["checkout"])),
            "port": int(cfg["port"]), "event_dir": os.path.dirname(path), "teammates": teammates}


def run(args, cwd=None):
    cwd = cwd or CHECKOUT
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=60)
    if p.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:3])}: {p.stderr.strip()[:200]}")
    return p.stdout


def gh_json(args):
    return json.loads(run(["gh", *args, "--repo", GH_REPO]))


def first_line(text):
    for line in (text or "").splitlines():
        if line.strip():
            return re.sub(r"\*\*|`", "", line).strip().lstrip("#*> ").strip()[:200]
    return ""


def git_log(rev_args, n):
    fmt = SEP.join(["%H", "%h", "%an", "%ae", "%cI", "%s"])
    out = run(["git", "log", *rev_args, f"-n{n}", f"--format={fmt}"])
    commits = []
    for line in out.splitlines():
        sha, short, name, email, when, subject = line.split(SEP, 5)
        commits.append({"sha": sha, "short": short, "author": name, "email": email,
                        "time": when, "subject": subject})
    return commits


def collect_issues():
    raw = gh_json(["issue", "list", "--state", "all", "--limit", "200", "--json",
                   "number,title,state,assignees,labels,updatedAt,createdAt,closedAt,comments,url"])
    issues = []
    for i in raw:
        last = i["comments"][-1] if i["comments"] else None
        issues.append({
            "number": i["number"], "title": i["title"], "state": i["state"], "url": i["url"],
            "assignees": [a["login"] for a in i["assignees"]],
            "labels": [l["name"] for l in i["labels"]],
            "updated": i["updatedAt"], "created": i["createdAt"], "closed": i["closedAt"],
            "last_comment": {"author": last["author"]["login"], "first_line": first_line(last["body"]),
                             "time": last["createdAt"], "url": last["url"]} if last else None,
            "comments": [{"author": c["author"]["login"], "first_line": first_line(c["body"]),
                          "time": c["createdAt"], "url": c["url"]} for c in i["comments"]],
        })
    return sorted(issues, key=lambda x: x["number"])


def check_state(rollup):
    if not rollup:
        return "none"
    states = {(c.get("conclusion") or c.get("state") or c.get("status") or "").upper() for c in rollup}
    if states & {"FAILURE", "ERROR", "CANCELLED", "TIMED_OUT", "ACTION_REQUIRED"}:
        return "failing"
    if states & {"PENDING", "IN_PROGRESS", "QUEUED", "EXPECTED", ""}:
        return "pending"
    return "passing"


def collect_prs():
    raw = gh_json(["pr", "list", "--state", "all", "--limit", "100", "--json",
                   "number,title,state,headRefName,author,updatedAt,createdAt,mergedAt,url,isDraft,statusCheckRollup,body"])
    prs = []
    for p in raw:
        refs = {int(n) for n in ISSUE_IN_BRANCH.findall(p["headRefName"])}
        refs |= {int(n) for n in re.findall(r"#(\d+)", (p["title"] or "") + " " + (p["body"] or ""))}
        prs.append({"number": p["number"], "title": p["title"], "state": p["state"], "branch": p["headRefName"],
                    "author": p["author"]["login"], "updated": p["updatedAt"], "created": p["createdAt"],
                    "merged": p["mergedAt"], "url": p["url"], "draft": p["isDraft"],
                    "checks": check_state(p["statusCheckRollup"]), "issues": sorted(refs)})
    return prs


def collect_branches():
    fmt = SEP.join(["%(refname:short)", "%(objectname:short)", "%(authorname)", "%(committerdate:iso-strict)", "%(subject)"])
    out = run(["git", "for-each-ref", "refs/remotes/origin", f"--format={fmt}", "--sort=-committerdate"])
    branches = []
    for line in out.splitlines():
        ref, short, author, when, subject = line.split(SEP, 4)
        if ref in ("origin", "origin/HEAD"):
            continue
        branches.append({"name": ref.removeprefix("origin/"), "short": short, "author": author,
                         "time": when, "subject": subject})
    return branches


def collect_unpushed():
    out = run(["git", "worktree", "list", "--porcelain"])
    waiting = []
    for block in out.strip().split("\n\n"):
        fields = dict(line.split(" ", 1) for line in block.splitlines() if " " in line)
        branch = fields.get("branch", "").removeprefix("refs/heads/")
        if not branch.startswith("issue-"):
            continue
        path = fields["worktree"]
        commits = git_log([branch, "--not", "--remotes=origin"], 50)
        if commits:
            waiting.append({"branch": branch, "path": path, "count": len(commits), "commits": commits,
                            "push": f"git -C {path} push -u origin {branch}"})
    return waiting


def collect_threads():
    threads = []
    for path in sorted(glob.glob(os.path.join(EVENT_DIR, "threads", "*.json"))):
        try:
            with open(path) as f:
                t = json.load(f)
            t["file"] = os.path.basename(path)
        except (OSError, ValueError) as e:
            t = {"name": os.path.basename(path).removesuffix(".json"), "state": "blocked", "note": f"Unreadable status file: {e}",
                 "updated": datetime.fromtimestamp(os.path.getmtime(path), timezone.utc).isoformat()}
        threads.append(t)
    return threads


def issue_of(name):
    m = ISSUE_IN_BRANCH.search(name or "")
    return int(m.group(1)) if m else None


def build_map(issues, prs, branches, unpushed, threads):
    by_num = {i["number"]: i for i in issues}
    nodes = {}
    for n in by_num:
        issue = by_num[n]
        times = [issue["updated"]] if issue else []
        its_prs = [p for p in prs if n in p["issues"]]
        its_threads = [t for t in threads if t.get("issue") == n]
        its_branches = [b for b in branches if issue_of(b["name"]) == n]
        its_local = [u for u in unpushed if issue_of(u["branch"]) == n]
        times += [p["updated"] for p in its_prs] + [t.get("updated", "") for t in its_threads]
        times += [b["time"] for b in its_branches]
        thread_states = {t.get("state") for t in its_threads}
        if any(p["merged"] for p in its_prs) or (issue and issue["state"] == "CLOSED"):
            state = "merged"
        elif any(p["state"] == "OPEN" for p in its_prs):
            state = "pr"
        elif thread_states & {"blocked", "needs-owner"}:
            state = "blocked"
        elif thread_states & {"working", "done"} or its_branches or its_local:
            state = "working"
        else:
            state = "not-started"
        note = max(its_threads, key=lambda t: t.get("updated", ""))["note"] if its_threads else ""
        nodes[n] = {"number": n, "title": issue["title"] if issue else f"#{n}", "state": state,
                    "updated": max((t for t in times if t), key=to_epoch, default=None),
                    "note": note, "url": issue["url"] if issue else None,
                    "assignees": issue["assignees"] if issue else []}
    return nodes


def to_epoch(iso):
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()


def build_feed(issues, prs, commits, threads):
    ev = []
    for i in issues:
        ev.append({"id": f"issue-open-{i['number']}", "time": i["created"], "kind": "issue", "who": "",
                   "text": f"#{i['number']} opened: {i['title']}", "url": i["url"]})
        if i["closed"]:
            ev.append({"id": f"issue-close-{i['number']}-{i['closed']}", "time": i["closed"], "kind": "issue",
                       "who": "", "text": f"#{i['number']} closed: {i['title']}", "url": i["url"]})
        for c in i["comments"]:
            ev.append({"id": f"comment-{c['url']}", "time": c["time"], "kind": "comment", "who": c["author"],
                       "text": f"on #{i['number']}: {c['first_line']}", "url": c["url"]})
    for p in prs:
        ev.append({"id": f"pr-{p['number']}", "time": p["created"], "kind": "pr", "who": p["author"],
                   "text": f"PR #{p['number']} opened: {p['title']}", "url": p["url"]})
        if p["merged"]:
            ev.append({"id": f"pr-merged-{p['number']}", "time": p["merged"], "kind": "pr", "who": p["author"],
                       "text": f"PR #{p['number']} merged: {p['title']}", "url": p["url"]})
    for c in commits:
        ev.append({"id": f"commit-{c['sha']}", "time": c["time"], "kind": "commit", "who": c["author"],
                   "text": f"{c['branch']}: {c['subject']}",
                   "url": f"https://github.com/{GH_REPO}/commit/{c['sha']}"})
    for t in threads:
        if t.get("updated"):
            ev.append({"id": f"thread-{t.get('name')}-{t['updated']}", "time": t["updated"], "kind": "thread",
                       "who": t.get("name", ""), "text": f"{t.get('state', '?')}: {t.get('note', '')}", "url": None})
    ev = [e for e in ev if e["time"]]
    ev.sort(key=lambda e: to_epoch(e["time"]), reverse=True)
    return ev[:80]


def remote_commits(branches):
    seen, commits = set(), []
    for b in branches:
        for c in git_log([f"origin/{b['name']}"], 30):
            if c["sha"] not in seen:
                seen.add(c["sha"])
                commits.append({**c, "branch": b["name"]})
    return commits


def collect():
    errors = []

    def attempt(fn, default):
        try:
            return fn()
        except Exception as e:  # one failing source must not blank the whole page
            errors.append(f"{fn.__name__}: {e}")
            return default

    attempt(lambda: run(["git", "fetch", "--prune", "-q", "origin"]), None)
    issues = attempt(collect_issues, [])
    prs = attempt(collect_prs, [])
    branches = attempt(collect_branches, [])
    unpushed = attempt(collect_unpushed, [])
    threads = attempt(collect_threads, [])
    commits = attempt(lambda: remote_commits(branches), [])
    main = attempt(lambda: {"commits": git_log(["origin/main"], 15),
                            "behind": int(run(["git", "rev-list", "--count", "main..origin/main"]).strip())},
                   {"commits": [], "behind": 0})
    teammates = []
    for m in TEAMMATES:
        events = [{"time": c["time"], "kind": "push", "text": f"{c['branch']}: {c['subject']}",
                   "url": f"https://github.com/{GH_REPO}/commit/{c['sha']}"}
                  for c in commits if m["git"].search(c["author"] + " " + c["email"])]
        events += [{"time": c["time"], "kind": "comment", "text": f"on #{i['number']}: {c['first_line']}",
                    "url": c["url"]}
                   for i in issues for c in i["comments"] if c["author"] == m["github"]]
        events.sort(key=lambda e: to_epoch(e["time"]), reverse=True)
        teammates.append({"github": m["github"], "events": events[:30]})
    feed = build_feed(issues, prs, commits, threads)
    for i in issues:
        del i["comments"]  # keep status.json small; the feed already carries them
    return {
        "generated": datetime.now(timezone.utc).isoformat(), "interval_s": INTERVAL_S, "repo": GH_REPO,
        "event": SLUG, "checkout": CHECKOUT,
        "errors": errors, "issues": issues, "prs": prs, "branches": branches, "main": main,
        "unpushed": unpushed, "threads": threads,
        "map": build_map(issues, prs, branches, unpushed, threads),
        "feed": feed,
        "teammates": teammates,
    }


def write_status():
    data = collect()
    tmp = os.path.join(EVENT_DIR, "status.json.tmp")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=1)
    os.replace(tmp, os.path.join(EVENT_DIR, "status.json"))
    return data


def loop():
    while True:
        try:
            d = write_status()
            print(f"{time.strftime('%H:%M:%S')} wrote status.json, {len(d['errors'])} errors", flush=True)
        except Exception as e:
            print(f"{time.strftime('%H:%M:%S')} collect failed: {e}", file=sys.stderr, flush=True)
        time.sleep(INTERVAL_S)


class NoCache(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, *args):
        pass

    def translate_path(self, path):
        route = path.split("?", 1)[0].split("#", 1)[0]
        if route == "/status.json":
            return os.path.join(EVENT_DIR, "status.json")
        if route in ("/", "/index.html"):
            return os.path.join(HERE, "index.html")
        return os.path.join(HERE, "no-such-route")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Live status page for one event.")
    parser.add_argument("slug", help="event folder name under hackathons/events/")
    parser.add_argument("--once", action="store_true", help="write status.json once and exit")
    args = parser.parse_args()
    cfg = load_config(args.slug)
    SLUG, GH_REPO, CHECKOUT, PORT = args.slug, cfg["repo"], cfg["checkout"], cfg["port"]
    EVENT_DIR, TEAMMATES = cfg["event_dir"], cfg["teammates"]
    os.makedirs(os.path.join(EVENT_DIR, "threads"), exist_ok=True)
    if args.once:
        print(json.dumps(write_status()["errors"]))
        sys.exit(0)
    threading.Thread(target=loop, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", PORT), partial(NoCache, directory=HERE))
    print(f"Serving http://localhost:{PORT}  (Ctrl-C to stop)", flush=True)
    server.serve_forever()
