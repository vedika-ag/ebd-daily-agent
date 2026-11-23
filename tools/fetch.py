#!/usr/bin/env python3
"""Open a news article and print its headline, date, publisher and text.

Usage: python3 tools/fetch.py URL [URL ...] [--max 6000]

Tries a plain HTTPS request first. If the site refuses it or returns a page
with no article text (bot wall, JavaScript-only page), it retries once in
headless Chromium (pre-installed with Playwright). Output is plain text so it
can be read directly. Exit code 0 if at least one URL produced article text.

Only fetches what is asked for: one page per URL, no crawling, no retries
beyond the single browser fallback.
"""
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request

UA = "EBD-Daily-Agent/1.0 (news summary bot)"
TIMEOUT = 25


def http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-IN,en"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")


def browser_get(url):
    """Render the page in headless Chromium via the Node Playwright install."""
    import subprocess

    js = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_fetch.js")
    r = subprocess.run(["node", js, url], capture_output=True, text=True, timeout=90)
    m = re.search(r"HTTP (\d+)", r.stderr or "")
    if r.returncode != 0 or not r.stdout:
        raise RuntimeError((r.stderr or "browser failed").strip()[:200])
    return (int(m.group(1)) if m else 0), r.stdout


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def meta(doc, *names):
    for n in names:
        m = re.search(
            r'<meta[^>]+(?:property|name|itemprop)=["\']%s["\'][^>]*content=["\']([^"\']*)' % re.escape(n), doc, re.I
        ) or re.search(
            r'<meta[^>]+content=["\']([^"\']*)["\'][^>]*(?:property|name|itemprop)=["\']%s["\']' % re.escape(n), doc, re.I
        )
        if m and m.group(1).strip():
            return clean(m.group(1))
    return ""


def jsonld_article(doc):
    for block in re.findall(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', doc, re.S | re.I):
        try:
            data = json.loads(block.strip())
        except Exception:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop()
            if isinstance(d, list):
                stack.extend(d)
                continue
            if not isinstance(d, dict):
                continue
            if "@graph" in d:
                stack.extend(d["@graph"] if isinstance(d["@graph"], list) else [d["@graph"]])
            t = d.get("@type")
            t = " ".join(t) if isinstance(t, list) else str(t or "")
            if "Article" in t or "NewsArticle" in t:
                pub = d.get("publisher")
                return {
                    "headline": clean(d.get("headline", "")),
                    "date": d.get("datePublished", "") or d.get("dateModified", ""),
                    "publisher": clean(pub.get("name", "")) if isinstance(pub, dict) else "",
                    "body": clean(d.get("articleBody", "")),
                }
    return {}


def extract(doc):
    doc_noscript = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", " ", doc, flags=re.S | re.I)
    art = jsonld_article(doc)
    headline = art.get("headline") or meta(doc, "og:title", "twitter:title") or clean(
        (re.search(r"<h1[^>]*>(.*?)</h1>", doc_noscript, re.S | re.I) or [None, ""])[1]
    )
    date = art.get("date") or meta(doc, "article:published_time", "datePublished", "publish-date", "pubdate")
    publisher = art.get("publisher") or meta(doc, "og:site_name")
    summary = meta(doc, "og:description", "description")
    body = art.get("body", "")
    if len(body) < 300:
        paras = [clean(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", doc_noscript, re.S | re.I)]
        paras = [p for p in paras if len(p) > 60 and not re.search(r"cookie|subscribe|sign in|newsletter|all rights reserved", p, re.I)]
        body = "\n".join(paras) if len("\n".join(paras)) > len(body) else body
    if len(body) < 300:
        # Text held in div blocks instead of <p>: take long text runs, skipping repeats and promos.
        txt = html.unescape(re.sub(r"<[^>]+>", "\n", doc_noscript))
        seen, runs = set(), []
        for line in (re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")):
            if len(line) > 100 and line not in seen and not re.search(
                r"cookie|subscribe|sign in|newsletter|all rights reserved|summit|awards|register now", line, re.I
            ):
                seen.add(line)
                runs.append(line)
        if len("\n".join(runs)) > len(body):
            body = "\n".join(runs)
    return headline, date, publisher, summary, body


def fetch(url, maxlen):
    status, doc, how, err = 0, "", "", ""
    try:
        status, doc = http_get(url)
        how = "direct"
    except urllib.error.HTTPError as e:
        status, err = e.code, "HTTP %s" % e.code
    except Exception as e:  # DNS / proxy refusal / timeout
        err = str(e)[:200]
    body = extract(doc)[4] if doc else ""
    if len(body) < 300 and "Tunnel connection failed: 403" not in err:
        try:
            status, doc = browser_get(url)
            how = "browser"
        except Exception as e:
            err = (err + " | browser: " + str(e)[:200]).strip(" |")
    print("=" * 80)
    print("URL:", url)
    if not doc:
        print("FAILED:", err or "no content")
        if "Tunnel connection failed" in err:
            print("HINT: this host is not on the ebd-daily-agent environment's network allowlist. Search for other coverage.")
        elif "HTTP 403" in err or "HTTP 401" in err:
            print("HINT: the site itself refused the request (bot wall or paywall). Search for other coverage.")
        return False
    headline, date, publisher, summary, body = extract(doc)
    print("FETCHED VIA:", how, "| HTTP", status)
    print("PUBLISHER:", publisher or "(unknown)")
    print("HEADLINE:", headline or "(none found)")
    print("DATE:", date or "(none found)")
    if summary:
        print("SUMMARY:", summary)
    if body:
        print("TEXT:\n" + body[:maxlen] + ("\n[...truncated]" if len(body) > maxlen else ""))
        return True
    print("TEXT: (no article text found; likely paywalled or blocked. Use the headline and search for other coverage.)")
    return bool(headline)


def main(argv):
    maxlen = 6000
    if "--max" in argv:
        i = argv.index("--max")
        maxlen = int(argv[i + 1])
        del argv[i : i + 2]
    urls = [a for a in argv if a.startswith("http")]
    if not urls:
        print(__doc__)
        return 2
    ok = [fetch(u, maxlen) for u in urls]
    return 0 if any(ok) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
