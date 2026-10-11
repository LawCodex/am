#!/usr/bin/env python3
"""Download the Constitution, codes and laws in force from ARLIS (www.arlis.am), the
official Armenian Legal Information System, plus the English translations hosted there.

Search used (same as the site's advanced search):
  hy: act_type = Constitution, Constitutional law, Code, Law; status = in force /
      partly in force; "exclude changing acts" (no amending laws)
  en: act_type = CONSTITUTION, CODE, LAW; status = Active / Partly active
Raw HTML is cached in ../_raw/am/ (relative to the repo root). One request at a time,
>= 1.5 s apart (arlis.am has no robots.txt)."""
import json, os, re, sys, time, urllib.parse, requests

UA = "LawCodex/1.0 (+https://github.com/LawCodex)"
BASE = "https://www.arlis.am"
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "am")
DELAY = 1.5
S = requests.Session()
S.headers["User-Agent"] = UA
_last = [0.0]
QUERIES = {
    "hy": {"act_type": "1,3,5,7", "status": "1,4", "exclude_changing_acts": True},
    "en": {"act_type": "84,83,88", "status": "5,7", "exclude_changing_acts": True},
}


def get(url, **kw):
    for attempt in range(6):
        wait = _last[0] + DELAY - time.time()
        if wait > 0:
            time.sleep(wait)
        _last[0] = time.time()
        try:
            r = S.get(url, timeout=180, **kw)
            if r.status_code == 200:
                return r
            print("HTTP", r.status_code, url, file=sys.stderr)
            if r.status_code == 404:
                return None
        except requests.RequestException as e:
            print("ERR", e, url, file=sys.stderr)
        time.sleep(20 * (attempt + 1))
    return None


def search(lang):
    path = os.path.join(RAW, f"index_{lang}.json")
    if os.path.exists(path):
        return json.load(open(path))
    q = urllib.parse.quote(json.dumps(QUERIES[lang]))
    items, seen, page, total = [], set(), 1, None
    while True:
        r = get(f"{BASE}/{lang}/search/page/{page}?{q}&order_by=",
                headers={"X-Requested-With": "XMLHttpRequest"})
        html = r.json()["html"]
        if total is None:
            total = int(re.search(r"\$\{(\d+)\}", html).group(1))
        cards = re.split(r'<div class="act-card ', html)[1:]
        for c in cards:
            m = re.search(r'href="/\w+/acts/(\d+)/latest"', c)
            if not m or int(m.group(1)) in seen:
                continue
            seen.add(int(m.group(1)))
            title = re.search(r'act-card__title[^>]*>(.*?)</', c, re.S)
            flat = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", c))
            num = re.search(r"(?:Ակտի համար|Act Number)` (.*?) (?:Ընդունման ամսաթիվ|Enactment date)`", flat)
            items.append(dict(id=int(m.group(1)),
                              title=re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", title.group(1))).strip() if title else "",
                              number=num.group(1).strip() if num else ""))
        print(lang, "page", page, len(items), "/", total, flush=True)
        if not cards or len(items) >= total or page > total // 10 + 2:
            break
        page += 1
    json.dump(items, open(path, "w"), ensure_ascii=False, indent=1)
    return items


def main():
    for lang in ("hy", "en"):
        os.makedirs(os.path.join(RAW, lang), exist_ok=True)
        items = search(lang)
        for n, it in enumerate(items):
            path = os.path.join(RAW, lang, f"{it['id']}.html")
            if os.path.exists(path):
                continue
            r = get(f"{BASE}/{lang}/acts/{it['id']}/latest")
            if r is None:
                continue
            open(path, "w", encoding="utf-8").write(f"<!-- url: {r.url} -->\n" + r.text)
            print(lang, n + 1, len(items), it["id"], len(r.text), flush=True)


if __name__ == "__main__":
    main()
