#!/usr/bin/env python3
"""Convert ARLIS act pages (cached by am_fetch.py in ../_raw/am/) to Markdown."""
import datetime, json, os, re, sys
from bs4 import BeautifulSoup, NavigableString, Tag

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "am")
HY2LAT = {"ա": "a", "բ": "b", "գ": "g", "դ": "d", "ե": "e", "զ": "z", "է": "e", "ը": "y", "թ": "t", "ժ": "zh",
          "ի": "i", "լ": "l", "խ": "kh", "ծ": "ts", "կ": "k", "հ": "h", "ձ": "dz", "ղ": "gh", "ճ": "ch", "մ": "m",
          "յ": "y", "ն": "n", "շ": "sh", "ո": "o", "չ": "ch", "պ": "p", "ջ": "j", "ռ": "r", "ս": "s", "վ": "v",
          "տ": "t", "ր": "r", "ց": "ts", "ւ": "v", "փ": "p", "ք": "k", "օ": "o", "ֆ": "f", "և": "ev"}
UPPER_HY = "ԱԲԳԴԵԶԸԹԺԼԽԾԿՀՁՂՃՄՅՆՇՉՊՋՌՍՎՏՐՑՓՔՕՖ"  # without Ի, Է (single-letter words)
KINDS = {
    "hy": [("book", r"(Գ\s?Ի\s?Ր\s?Ք|Գիրք)\s*[IVXLC\d]|(ԱՌԱՋԻՆ|[Ա-Ֆ]+ՐՈՐԴ)\s+ԳԻՐՔ\s*$"),
           ("part", r"([IVXLC\d]+\.\s*)?(ԸՆԴՀԱՆՈՒՐ|ՀԱՏՈՒԿ|Ընդհանուր|Հատուկ)\s+(ՄԱՍ|մաս)\b|(Մ\s?Ա\s?Ս|Մաս)\s+[IVXLC\d]|(ԱՌԱՋԻՆ|[Ա-Ֆ]+ՐՈՐԴ)\s+ՄԱՍ\s*$"),
           ("section", r"(Հ\s?Ա\s?Տ\s?Վ\s?Ա\s?Ծ|Բ\s?Ա\s?Ժ\s?Ի\s?Ն|Բաժին|Հատված)\s*[IVXLC\d]|(ԱՌԱՋԻՆ|[Ա-Ֆ]+ՐՈՐԴ)\s+(ԲԱԺԻՆ|ՀԱՏՎԱԾ)\s*$"),
           ("subsection", r"(Ե\s?Ն\s?Թ\s?Ա\s?Բ\s?Ա\s?Ժ\s?Ի\s?Ն|Ենթաբաժին)\s*[IVXLC\d]"),
           ("chapter", r"(Գ\s?Լ\s?Ո\s?Ւ\s?Խ|Գլուխ)\s*[IVXLC\d]"), ("article", r"(Հ\s?ՈԴՎԱԾ|Հոդված)\s*\d")],
    "en": [("book", r"(BOOK|Book)\s+[IVXLC\dOTF]"), ("part", r"(GENERAL|SPECIAL|General|Special)\s+(PART|Part)\b|(PART|Part)\s+[IVXLC\dOTF]"),
           ("section", r"(SECTION|Section)\s+[IVXLC\d]"), ("subsection", r"(SUB-?SECTION|Sub-?section)\s+[IVXLC\d]"),
           ("chapter", r"(CHAPTER|Chapter)\s+[IVXLC\d]"), ("article", r"(Article|ARTICLE)\s*\d")],
}
HEAD_KINDS = ("book", "part", "section", "subsection", "chapter")


def translit(s):
    s = s.lower().replace("ու", "u")
    s = "".join(HY2LAT.get(ch, ch) for ch in s)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def slug(title, n=70):
    s = translit(title)
    if len(s) > n:
        s = s[:n].rsplit("-", 1)[0]
    return s or "untitled"


def fix_spacing(t):
    """Undo letter-spacing artefacts of the Word sources: 'Գ Լ ՈՒ Խ' -> 'ԳԼՈՒԽ', 'Տ նտեսական' -> 'Տնտեսական'."""
    t = re.sub(r"\b(Գ Լ ՈՒ Խ|Օ Ր Ե Ն Ք Ը|Օ Ր Ե Ն Ս Գ Ի Ր Ք)\b", lambda m: m.group(0).replace(" ", ""), t)
    t = re.sub(rf"(?<![\w])([{UPPER_HY}]) (?=[ա-ֆ]{{2,}}|[{UPPER_HY}Ի]{{2,}})", r"\1", t)
    return t


def text_of(el):
    out = []
    for d in el.descendants:
        if isinstance(d, NavigableString):
            if d.parent.name in ("script", "style"):
                continue
            out.append(str(d))
        elif isinstance(d, Tag) and d.name == "br":
            out.append("\n")
    t = "".join(out).replace("\xa0", " ").replace("\u200b", "").replace("\u2696", "")  # U+2696 = link to case law
    t = re.sub(r"[ \t\r\f\v]+", " ", t)
    t = "\n".join(x.strip() for x in t.split("\n"))
    return re.sub(r"\n{2,}", "\n", t).strip()


def frac(el, tags):
    t = re.sub(r"\s", "", el.get_text())
    if not t:
        return 0
    x = "".join(re.sub(r"\s", "", i.get_text()) for i in el.find_all(tags))
    return len(x) / len(t)


def esc(t):
    return re.sub(r"^(#+|>|[-+*] )", lambda m: "\\" + m.group(0), t)


def table_html(tb):
    rows = []
    for tr in tb.find_all("tr"):
        if tr.find_parent("table") is not tb:
            continue
        cells = []
        for td in tr.find_all(["td", "th"], recursive=False):
            attrs = "".join(f' {a}="{td[a]}"' for a in ("colspan", "rowspan") if td.get(a) and td.get(a) != "1")
            cells.append(f"<{td.name}{attrs}>{fix_spacing(text_of(td)).replace(chr(10), '<br>')}</{td.name}>")
        rows.append("<tr>" + "".join(cells) + "</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def kind_of(t, lang):
    for k, rx in KINDS[lang]:
        if re.match(rx, t):
            return k
    return None


def blocks(root):
    for el in root.children:
        if not isinstance(el, Tag):
            continue
        if el.name == "table":
            yield el
        elif el.name in ("div", "center", "blockquote", "section", "font") and el.find(["p", "table", "div"]):
            yield from blocks(el)
        elif el.name in ("ol", "ul"):
            for li in el.find_all("li", recursive=False):
                yield li
        elif el.name in ("style", "script"):
            continue
        elif el.name == "p" and el.find("table"):
            yield from blocks(el)
        else:
            yield el


def convert_body(root, lang):
    items = []
    for el in blocks(root):
        if el.name == "table":
            rows = el.find_all("tr")
            cells = rows[0].find_all("td", recursive=False) if len(rows) == 1 else []
            if len(cells) == 2:
                a, b = fix_spacing(text_of(cells[0])), fix_spacing(text_of(cells[1]))
                if kind_of(a, lang) == "article":
                    items.append(("article", re.sub(r"\s+", " ", f"{a} {b}").strip()))
                    continue
            if not el.get_text(strip=True):
                continue
            items.append(("table", table_html(el)))
            continue
        t = fix_spacing(text_of(el))
        if not t or t == "Բովանդակություն":
            continue
        one = re.sub(r"\s+", " ", t)
        bold, ital = frac(el, ["strong", "b"]), frac(el, ["em", "i"])
        k = kind_of(one, lang)
        if k and (bold > 0.5 or len(one) < 200 and k != "article" or k == "article" and len(one) < 300):
            items.append((k, one))
        elif ital > 0.8 and re.match(r"^\(.*\)$", one, re.S):
            items.append(("note", one))
        elif bold > 0.9 and len(one) < 250 and (one.upper() == one or el.get("align") == "center"
                                                 or "center" in (el.get("style") or "").lower()):
            items.append(("other", one))
        else:
            items.append(("para", t))
    # merge "ԳԼՈՒԽ 1" + "ԸՆԴՀԱՆՈՒՐ ԴՐՈՒՅԹՆԵՐ"
    merged = []
    for k, t in items:
        if k == "other" and merged and merged[-1][0] in HEAD_KINDS and len(merged[-1][1].split()) <= 3 \
                and not re.search(r"[.:–—]\s*\S", merged[-1][1]):
            merged[-1] = (merged[-1][0], merged[-1][1].rstrip(".") + ". " + t)
        else:
            merged.append((k, t))
    items = merged
    for n, (k, t) in enumerate(items):  # title block before the first heading
        if k == "other":
            items[n] = ("bold", t)
        elif k in HEAD_KINDS or k == "article":
            break
    order = []
    for k, _ in items:
        if k in HEAD_KINDS and k not in order:
            order.append(k)
    level = {k: 2 + n for n, k in enumerate(order)}
    art_level = min(6, 2 + len(order))
    out = []
    last = 1
    for k, t in items:
        if k == "para":
            out.append(esc(t).replace("\n", "  \n"))
        elif k == "note":
            out.append("*" + t.replace("\n", " ").replace("*", "\\*") + "*")
        elif k == "table":
            out.append(t)
        elif k == "bold":
            out.append("**" + t.replace("*", "\\*") + "**")
        elif k == "other":
            lv = min(max(last + 1, 2), art_level - 1) if art_level > 2 else 2
            if last == art_level:
                lv = max(art_level - 1, 2)
            out.append("#" * min(lv, 6) + " " + t)
        else:
            lv = art_level if k == "article" else level[k]
            last = lv
            out.append("#" * min(lv, 6) + " " + t)
    return "\n\n".join(out) + "\n"


def dmy(s):
    m = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", s or "")
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else None


def yq(s):
    return '"' + (s or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


CATS = {"Սահմանադրություն": ("sahmanadrutyun", "constitution"),
        "Սահմանադրական օրենք": ("sahmanadrakan-orenqner", "constitutional_law"),
        "Օրենսգիրք": ("orensgrqer", "code"), "Օրենք": ("orenqner", "act"),
        "CONSTITUTION": ("constitution", "constitution"), "CODE": ("codes", "code"), "LAW": ("laws", "act")}


# ARLIS lists these as "in force", but they are superseded texts or not Armenian law:
EXCLUDE = {1: "1995 Constitution, original text (superseded by the 2005 and 2015 revisions)",
           75780: "1995 Constitution as revised in 2005 (superseded by the 2015 revision, id 143723)",
           77862: "Constitution of the World Health Organization (international treaty)"}


def main():
    today = datetime.date.today().isoformat()
    counts = {}
    for lang in ("hy", "en"):
        ip = os.path.join(RAW, f"index_{lang}.json")
        if not os.path.exists(ip):
            continue
        for it in json.load(open(ip)):
            if lang == "hy" and it["id"] in EXCLUDE:
                continue
            p = os.path.join(RAW, lang, f"{it['id']}.html")
            if not os.path.exists(p):
                continue
            html = open(p, encoding="utf-8").read()
            url = re.match(r"<!-- url: (\S+) -->", html)
            soup = BeautifulSoup(html, "lxml")
            sec = soup.select_one("#act_body .act-block__section")
            if sec is None:
                print("no body", p, file=sys.stderr)
                continue
            info = {}
            for x in soup.select(".act-info__item"):
                lab, val = x.select_one(".act-info__label"), x.select_one(".act-info__value")
                if lab and val:
                    info[lab.get_text(strip=True)] = re.sub(r"\s+", " ", val.get_text(" ", strip=True))
            g = lambda *ks: next((info[k] for k in ks if info.get(k)), "")
            typ_txt = g("Տիպ", "Type")
            cat, typ = CATS.get(typ_txt, CATS.get(typ_txt.upper(), ("orenqner" if lang == "hy" else "laws", "act")))
            title = re.sub(r"\s+", " ", soup.title.get_text(" ", strip=True)) if soup.title else it["title"]
            date = dmy(g("Ընդունման ամսաթիվ", "Enactment date", "Adoption date"))
            status_txt = g("Կարգավիճակ", "Status")
            cons = re.search(r"\((\d{2}\.\d{2}\.\d{4})-", status_txt)
            year = (date or "0000")[:4]
            fn = f"{it['id']}-{slug(title)}.md"
            sub = os.path.join(lang, cat, year) if cat in ("orenqner", "laws") else os.path.join(lang, cat)
            body = convert_body(sec, lang)
            warn = soup.select_one(".act-content__info .info-block-description")
            if warn and warn.get_text(strip=True):
                body = "> " + re.sub(r"\s+", " ", warn.get_text(" ", strip=True)) + "\n\n" + body
            fm = ["---", f"title: {yq(title)}", f"identifier: {yq(it.get('number', ''))}", f"arlis_id: {it['id']}",
                  f"type: {typ}", f"document_kind: {yq(g('Փաստաթղթի տեսակ', 'Document type'))}",
                  f"issuer: {yq(g('Ընդունող մարմին', 'Enactment body', 'Enactment organisation'))}",
                  "jurisdiction: am", f"language: {lang}"]
            if date:
                fm.append(f"date: {date}")
            if dmy(g("Ուժի մեջ մտնելու ամսաթիվ", "Actual start date", "Effective date")):
                fm.append(f"entry_into_force: {dmy(g('Ուժի մեջ մտնելու ամսաթիվ', 'Actual start date', 'Effective date'))}")
            if cons:
                fm.append(f"last_amended: {dmy(cons.group(1))}  # start of the current version")
            fm += [f"status_text: {yq(status_txt)}", "status: in_force",
                   f"publication: {yq(g('Սկզբնաղբյուր', 'Source'))}",
                   f"source: \"{url.group(1) if url else f'https://www.arlis.am/{lang}/acts/{it[chr(105)+chr(100)]}/latest'}\""]
            if lang == "en":
                fm.append("translation: true  # English translation hosted on ARLIS; the Armenian text is authoritative")
            fm += [f"retrieved: {today}", "---", "", f"# {title}", "", ""]
            out = os.path.join(REPO, sub, fn)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write("\n".join(fm) + body)
            counts[(lang, cat)] = counts.get((lang, cat), 0) + 1
    for k, v in sorted(counts.items()):
        print(k, v)


if __name__ == "__main__":
    main()
