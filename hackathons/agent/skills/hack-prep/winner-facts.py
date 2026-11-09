#!/usr/bin/env python3
import html
import json
import re
import subprocess
import sys

# Devpost answers WebFetch with 403 but serves curl with a browser User-Agent.
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
REPO_LINK = re.compile(r"https://(?:www\.)?(?:github|gitlab)\.com/[^\s\"'<>]+")


def fetch(url: str) -> tuple[int, str]:
    # --max-time 30 is a guess, not a measured figure.
    r = subprocess.run(["curl", "-fsSL", "--max-time", "30", "-A", UA, url], capture_output=True, text=True)
    return r.returncode, r.stdout


def visible_text(fragment: str) -> str:
    fragment = re.sub(r"(?is)<(script|style)\b.*?</\1\s*>", " ", fragment)
    fragment = re.sub(r"(?s)<[^>]+>", " ", fragment)
    return html.unescape(fragment)


def between(page_html: str, start: str, end: str) -> str:
    i = page_html.find(start)
    if i < 0:
        return ""
    j = page_html.find(end, i)
    return page_html[i : j if j >= 0 else len(page_html)]


def winning_projects(profile_html: str) -> list[tuple[str, list[str]]]:
    found = []
    for block in re.findall(r'(?is)<script type="application/ld\+json">(.*?)</script>', profile_html):
        data = json.loads(block)
        if data.get("award"):
            found.append((data["url"], data["award"]))
    return found


def write_up(page_html: str) -> str:
    gallery = page_html.find('id="gallery"')
    if gallery >= 0:
        slick = page_html.find('data-slick="true"', gallery)
        start = page_html.find("</ul>", slick) + len("</ul>")
    else:
        start = page_html.find('id="app-details-left"')
    end = page_html.find('id="built-with"', start)
    return page_html[start : end if end >= 0 else len(page_html)]


def write_up_words(page_html: str) -> int:
    return sum(1 for tok in visible_text(write_up(page_html)).split() if re.search(r"\w", tok))


def video_url(page_html: str) -> str | None:
    gallery = between(page_html, 'id="gallery"', 'id="built-with"')
    m = re.search(r"youtube\.com/embed/([\w-]+)", gallery)
    if m:
        return f"https://www.youtube.com/watch?v={m.group(1)}"
    m = re.search(r"player\.vimeo\.com/video/(\d+)", gallery)
    if m:
        return f"https://vimeo.com/{m.group(1)}"
    return None


def video_seconds(url: str) -> int | str:
    r = subprocess.run(["yt-dlp", "--skip-download", "--print", "duration", url], capture_output=True, text=True)
    if r.returncode != 0:
        return f"unknown (yt-dlp exit {r.returncode})"
    out = r.stdout.strip()
    try:
        return round(float(out))
    except ValueError:
        return f"unknown (yt-dlp printed {out})"


def repo_place(page_html: str) -> str:
    try_it_out = between(page_html, 'aria-label="Try it out"', 'id="app-details-right"')
    updates = between(page_html, 'id="updates"', 'id="submission-history"')
    if REPO_LINK.search(try_it_out):
        return "Try it out"
    if REPO_LINK.search(write_up(page_html)):
        return "write-up"
    if REPO_LINK.search(updates):
        return "updates only"
    return "no"


def prizes(page_html: str) -> list[str]:
    found = []
    submissions = between(page_html, 'id="submissions"', 'id="app-team"')
    for event in submissions.split('class="software-list-content"')[1:]:
        name = re.search(r"(?s)<p>\s*<a[^>]*>(.*?)</a>", event)
        event_name = html.unescape(name.group(1)).strip() if name else ""
        for li in re.findall(r"(?s)<li>(.*?)</li>", event):
            if "winner label" in li:
                prize = " ".join(visible_text(li).split()).removeprefix("Winner").strip()
                found.append(f"{prize} ({event_name})" if event_name else prize)
    return found


def title(page_html: str) -> str:
    m = re.search(r"(?s)<title>(.*?)</title>", page_html)
    return html.unescape(m.group(1)).split(" | Devpost")[0].strip() if m else ""


def median(values: list[int]) -> int:
    s = sorted(values)
    mid = len(s) // 2
    m = s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2
    return int(m + 0.5)


def mss(seconds: int) -> str:
    return f"{seconds // 60}:{seconds % 60:02d}"


def links(items: list[tuple[int, str]]) -> str:
    return " ".join(f"[{i}]({url})" for i, url in items)


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: winner-facts.py <devpost user>", file=sys.stderr)
        return 2
    profile = f"https://devpost.com/{sys.argv[1]}"
    code, profile_html = fetch(profile)
    if code != 0:
        print(f"profile fetch failed: {profile} (curl exit {code})", file=sys.stderr)
        return 1
    projects = winning_projects(profile_html)
    if not projects:
        print(f"no winning projects on {profile}", file=sys.stderr)
        return 1

    rows, pages = [], []
    for i, (url, _awards) in enumerate(projects, 1):
        code, page = fetch(url)
        if code != 0:
            rows.append(f"| [{i}]({url}) |  |  | fetch failed (exit {code}) |  |  |")
            continue
        words = write_up_words(page)
        video = video_url(page)
        seconds = video_seconds(video) if video else "no video"
        repo = repo_place(page)
        won = prizes(page)
        pages.append((i, url, words, video, seconds, repo, won))
        video_cell = f"[{mss(seconds)}]({video})" if isinstance(seconds, int) else seconds
        rows.append(f"| [{i}]({url}) | {title(page)} | {'; '.join(won)} | {words} | {video_cell} | {repo} |")

    if not pages:
        print(f"no winning project page could be fetched from {profile}", file=sys.stderr)
        return 1

    n = len(pages)
    words = [(p[0], p[1], p[2]) for p in pages]
    videos = [(p[0], p[3], p[4]) for p in pages if isinstance(p[4], int)]
    repos = [(p[0], p[1]) for p in pages if p[5] == "Try it out"]
    won = [(p[0], p[1]) for p in pages if p[6]]
    word_counts = [w for _, _, w in words]
    video_secs = [s for _, _, s in videos]

    print("### Pages measured")
    print("| # | Project | Prizes shown under Submitted to | Write-up words | Video | Repo link |")
    print("|---|---|---|---|---|---|")
    print("\n".join(rows))
    print()
    print("### Measured")
    print("| Measure | Value | From |")
    print("|---|---|---|")
    print(
        f"| Write-up words | range {min(word_counts)} to {max(word_counts)}, median {median(word_counts)}"
        f" ({len(words)} of {n} pages) | {links([(i, u) for i, u, _ in words])} |"
    )
    if videos:
        video_value = f"range {mss(min(video_secs))} to {mss(max(video_secs))}, median {mss(median(video_secs))}"
    else:
        video_value = "not measured"
    print(f"| Video length | {video_value} ({len(videos)} of {n} pages) | {links([(i, u) for i, u, _ in videos])} |")
    print(f"| Repo in Try it out | {len(repos)} of {n} pages | {links(repos)} |")
    print(f"| Prizes shown under Submitted to | {len(won)} of {n} pages (at least 1 prize) | {links(won)} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
