#!/usr/bin/env python3
"""List recent stories from the EBD news feeds, or search Google News.

Usage:
  python3 tools/feeds.py [--hours 36] [--grep WORD]   # all feeds in tools/feeds.txt
  python3 tools/feeds.py --search "Hocco ChrysCapital stake" [--hours 168]

Feeds mode prints one line per item: IST time | source | title | link,
newest first, filtered to the last N hours (default 36).
Search mode queries Google News RSS (India edition), which is the fastest
way to find other outlets covering a story whose own page is blocked.
"""
import datetime as dt
import email.utils
import html
import os
import re
import sys
import urllib.parse
import urllib.request

UA = "EBD-Daily-Agent/1.0 (news summary bot)"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
HERE = os.path.dirname(os.path.abspath(__file__))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=25) as r:
        return r.read().decode("utf-8", errors="ignore")


def tag(block, name):
    m = re.search(r"<%s[^>]*>(.*?)</%s>" % (name, name), block, re.S)
    if not m:
        m = re.search(r'<%s[^>]*href="([^"]+)"' % name, block)  # Atom <link href>
    v = m.group(1) if m else ""
    v = re.sub(r"<!\[CDATA\[|\]\]>", "", v)
    return html.unescape(re.sub(r"<[^>]+>", "", v)).strip()


def parse_date(s):
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except Exception:
        try:
            d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
        except Exception:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d.astimezone(IST)


def items(xml, default_source):
    out = []
    for b in re.findall(r"<(?:item|entry)\b.*?</(?:item|entry)>", xml, re.S):
        title = tag(b, "title")
        link = tag(b, "link")
        when = parse_date(tag(b, "pubDate") or tag(b, "published") or tag(b, "updated") or tag(b, "dc:date"))
        source = tag(b, "source") or default_source
        out.append((when, source, title, link))
    return out


def main(argv):
    hours = 36
    if "--hours" in argv:
        i = argv.index("--hours"); hours = float(argv[i + 1]); del argv[i : i + 2]
    word = None
    if "--grep" in argv:
        i = argv.index("--grep"); word = argv[i + 1].lower(); del argv[i : i + 2]
    feeds = []
    if "--search" in argv:
        i = argv.index("--search"); q = argv[i + 1]
        if "--hours" not in sys.argv:
            hours = 24 * 14
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
            {"q": q, "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
        feeds = [("Google News", url)]
    else:
        for line in open(os.path.join(HERE, "feeds.txt"), encoding="utf-8"):
            line = line.strip()
            if line and not line.startswith("#"):
                name, url = [x.strip() for x in line.split("|", 1)]
                feeds.append((name, url))
    cutoff = dt.datetime.now(IST) - dt.timedelta(hours=hours)
    rows, errors, counts = [], [], {}
    for name, url in feeds:
        try:
            got = items(get(url), name)
        except Exception as e:
            errors.append("%s: %s" % (name, str(e)[:120]))
            continue
        counts[name] = 0
        for when, source, title, link in got:
            if when and when < cutoff:
                continue
            if word and word not in title.lower():
                continue
            rows.append((when, source, title, link))
            counts[name] += 1
    seen, uniq = set(), []
    for r in rows:
        key = (r[2].lower(), r[1])
        if key not in seen:
            seen.add(key); uniq.append(r)
    rows = uniq
    rows.sort(key=lambda r: r[0] or dt.datetime.min.replace(tzinfo=IST), reverse=True)
    for when, source, title, link in rows:
        stamp = when.strftime("%d %b %H:%M IST") if when else "(no date)"
        print("%s | %s | %s | %s" % (stamp, source, title, link))
    if not rows:
        print("(no items in the last %g hours)" % hours)
    print("-- items per feed: " + ", ".join("%s %d" % kv for kv in counts.items()), file=sys.stderr)
    for e in errors:
        print("FEED FAILED:", e, file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
