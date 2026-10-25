#!/usr/bin/env python3
"""Build the Great Books reading-path datasets from public-domain sources.
Usage: python3 build.py [--fetch]   (--fetch downloads sources into ./src first)
Outputs: stoics.json, shakespeare.json, homer.json, plato.json, dante.json, tragedies.json
All source URLs are listed in sources.md and in SOURCES below."""
import re, json, html, os, sys, glob, time, math, urllib.request, urllib.parse
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
TODAY = date.today().isoformat()
UA = {"User-Agent": "GreatBooksBuilder/1.0 (public-domain reading plan)"}

SOURCES = {
    "marcus": "https://www.gutenberg.org/cache/epub/15877/pg15877.txt",
    "marcus_html": "https://www.gutenberg.org/cache/epub/15877/pg15877-images.html",
    "shakespeare_txt": "https://www.gutenberg.org/cache/epub/100/pg100.txt",
    "shakespeare_html": "https://www.gutenberg.org/cache/epub/100/pg100-images.html",
}
EPI = "The Discourses of Epictetus; with the Encheiridion and Fragments"
SEN = "Moral letters to Lucilius"
WS = "https://en.wikisource.org/wiki/"

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()

def ws_url(title):
    return WS + urllib.parse.quote(title.replace(" ", "_"), safe="/;,()'")

def ws_file(title, ext):
    return os.path.join(SRC, "wsr" if ext == "html" else "ws", title.replace("/", "__").replace(" ", "_") + "." + ext)

def fetch():
    os.makedirs(SRC, exist_ok=True)
    for k, u in SOURCES.items():
        fn = os.path.join(SRC, os.path.basename(u))
        if not os.path.exists(fn):
            open(fn, "wb").write(get(u))
    os.makedirs(os.path.join(SRC, "ws"), exist_ok=True); os.makedirs(os.path.join(SRC, "wsr"), exist_ok=True)
    titles = [f"{EPI}/Book {b}/Chapter {c}" for b, n in ((1, 30), (2, 26), (3, 26), (4, 13)) for c in range(1, n + 1)]
    titles += [f"{EPI}/The Encheiridion or Manual"] + [f"{SEN}/Letter {i}" for i in range(1, 125)]
    for t in titles:
        if not os.path.exists(ws_file(t, "wiki")):
            open(ws_file(t, "wiki"), "w").write(get("https://en.wikisource.org/w/index.php?action=raw&title=" + urllib.parse.quote(t)).decode())
        if not os.path.exists(ws_file(t, "html")):
            d = json.loads(get("https://en.wikisource.org/w/api.php?action=parse&format=json&prop=text&formatversion=2&page=" + urllib.parse.quote(t)))
            open(ws_file(t, "html"), "w").write(d["parse"]["text"])
        time.sleep(0.2)

def strip_html(s):
    s = re.sub(r"<(style|script)[^>]*>.*?</\1>", " ", s, flags=re.S)
    s = re.sub(r'<sup[^>]*class="reference"[^>]*>.*?</sup>', " ", s, flags=re.S)
    s = re.sub(r'<div class="reflist.*', " ", s, flags=re.S)
    return html.unescape(" ".join(re.sub(r"<[^>]+>", " ", s).split()))

def words(s):
    return len(re.findall(r"[A-Za-z']+", s))

def balance(units, ndays, weight=lambda u: u["w"], breakable=lambda prev, cur: True, prefer=None, bonus=0.4):
    """Split an ordered list of units into ndays contiguous groups with balanced weight.
    A boundary may only fall where breakable(prev, cur) is True."""
    total = sum(weight(u) for u in units)
    cum, c = [], 0
    for u in units:
        c += weight(u); cum.append(c)
    cuts, start = [], 0
    for k in range(1, ndays):
        target = total * k / ndays
        best = None
        for i in range(start + 1, len(units) - (ndays - k) + 1):
            if not breakable(units[i - 1], units[i]):
                continue
            d = abs(cum[i - 1] - target)
            if prefer is not None and prefer(units[i - 1], units[i]):
                d -= bonus * total / ndays
            if best is None or d < best[0]:
                best = (d, i)
            if cum[i - 1] > target + total / ndays:
                break
        if best is None:
            raise SystemExit(f"cannot place cut {k}")
        cuts.append(best[1]); start = best[1]
    bounds = [0] + cuts + [len(units)]
    return [units[bounds[i]:bounds[i + 1]] for i in range(ndays)]

# ---------------- Stoics ----------------
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]

def marcus_sections():
    lines = open(os.path.join(SRC, "pg15877.txt"), encoding="utf-8").read().splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == "THE THOUGHTS")
    book_lines = [i for i, l in enumerate(lines) if i > start and l.strip() in [r + "." for r in ROMAN]]
    assert len(book_lines) == 12, book_lines
    end = next(i for i, l in enumerate(lines) if i > book_lines[-1] and re.match(r"^[A-Z][A-Z .]{6,}$", l.strip()))
    anchors = set(re.findall(r'id="([ivx]+\._\d+)"', open(os.path.join(SRC, "pg15877-images.html"), encoding="utf-8").read()))
    out = []
    for b in range(12):
        s, e = book_lines[b] + 1, (book_lines[b + 1] if b < 11 else end)
        cur, num = [], 1
        for l in lines[s:e]:
            if l.startswith("    ") or re.match(r"^\s*\[[A-Z]\]", l):  # indented footnotes
                continue
            m = re.match(r"^(\d+)\. ", l)
            if m and int(m.group(1)) == num + 1:
                out.append({"book": b + 1, "sec": num, "w": words(" ".join(cur))}); cur, num = [l], num + 1
            else:
                cur.append(l)
        out.append({"book": b + 1, "sec": num, "w": words(" ".join(cur))})
    return out, anchors

def marcus_days(n):
    secs, anchors = marcus_sections()
    # give each book a share of days proportional to its length, then balance inside each book
    tot = sum(x["w"] for x in secs)
    bw = [sum(x["w"] for x in secs if x["book"] == b) for b in range(1, 13)]
    raw = [n * w / tot for w in bw]
    alloc = [max(1, int(r)) for r in raw]
    while sum(alloc) < n:
        i = max(range(12), key=lambda j: raw[j] - alloc[j]); alloc[i] += 1
    while sum(alloc) > n:
        i = min(range(12), key=lambda j: raw[j] - alloc[j]); alloc[i] -= 1
    groups = []
    for b in range(12):
        groups += balance([x for x in secs if x["book"] == b + 1], alloc[b])
    days = []
    for g in groups:
        b0, b1 = g[0]["book"], g[-1]["book"]
        if b0 == b1:
            ref = f"Book {ROMAN[b0-1]}, sections {g[0]['sec']}-{g[-1]['sec']}" if len(g) > 1 else f"Book {ROMAN[b0-1]}, section {g[0]['sec']}"
        else:
            ref = f"Book {ROMAN[b0-1]}, section {g[0]['sec']} to Book {ROMAN[b1-1]}, section {g[-1]['sec']}"
        anchor = None
        for s in [x for x in secs if x["book"] == b0 and x["sec"] <= g[0]["sec"]][::-1]:
            a = f"{ROMAN[b0-1].lower()}._{s['sec']}"
            if a in anchors:
                anchor = a; break
        link = SOURCES["marcus_html"] + ("#" + anchor if anchor else "#THE_THOUGHTS")
        days.append({"work": "Meditations (The Thoughts)", "author": "Marcus Aurelius", "translator": "George Long",
                     "ref": ref, "full_text_link": link, "words": sum(x["w"] for x in g), "verified": True,
                     "source_notes": f"Section numbers parsed from Project Gutenberg #15877 (Long translation). Link anchor {'#'+anchor if anchor else 'none'}: nearest section anchor at or before the start; scroll to the section number if needed."})
    return days

def ws_meta(title):
    w = open(ws_file(title, "wiki"), encoding="utf-8").read()
    tr = re.search(r"\|\s*translator\s*=\s*([^\n|]+)", w)
    sec = re.search(r"\|\s*section\s*=\s*([^\n]*)", w)
    return (tr.group(1).strip() if tr else ""), (sec.group(1).strip() if sec else "")

PROPER = {"god": "God", "gods": "Gods", "zeus": "Zeus", "socrates": "Socrates", "diogenes": "Diogenes", "epicurus": "Epicurus",
          "epictetus": "Epictetus", "nero": "Nero", "rome": "Rome", "cynic": "Cynic", "cynics": "Cynics", "cynism": "Cynism", "academics": "Academics",
          "pyrrhonists": "Pyrrhonists", "epicureans": "Epicureans", "stoics": "Stoics", "hercules": "Hercules", "achilles": "Achilles",
          "nicopolis": "Nicopolis", "naso": "Naso", "maximus": "Maximus", "heraclitus": "Heraclitus", "lucilius": "Lucilius"}

def nice_title(t):
    t = re.sub(r"\s*\([^)]*[\u0370-\u03ff\u1f00-\u1fff][^)]*\)", "", t)
    t = re.sub(r"[A-Za-z]+", lambda m: PROPER.get(m.group(0).lower(), m.group(0)), t)
    return t[0].upper() + t[1:]

def epictetus_units():
    units = []
    for b, n in ((1, 30), (2, 26), (3, 26), (4, 13)):
        for c in range(1, n + 1):
            t = f"{EPI}/Book {b}/Chapter {c}"
            tr, sec = ws_meta(t)
            body = strip_html(open(ws_file(t, "html"), encoding="utf-8").read())
            body = body.split("Layout 1", 1)[-1]
            m = re.match(r"[\s\u200b]*(?:BOOK [IVX]+\.\s*)?(?:CHAPTER [IVXL]+\.?\s*)?([a-z][^.?!]{3,200}?(?:[.?!]|(?=\s[A-Z])))", body)
            title = nice_title(m.group(1)).rstrip(".") if m else None
            ok = tr == "George Long" and sec.replace(" ", "") == f"Book{b},Chapter{c}" and words(body) > 80
            units.append({"work": "Discourses", "author": "Epictetus", "translator": "George Long",
                          "ref": f"Book {b}, Chapter {c}", "chapter_title": title, "full_text_link": ws_url(t),
                          "w": words(body), "verified": ok,
                          "source_notes": f"Wikisource page (Long, 1877 edition) checked: translator '{tr}', section '{sec}', {words(body)} words."})
    return units

def enchiridion_chapters():
    t = f"{EPI}/The Encheiridion or Manual"
    body = strip_html(open(ws_file(t, "html"), encoding="utf-8").read())
    # chapters are numbered as Roman numerals at the start of paragraphs
    parts = re.split(r"\s(?=(?:[IVXL]+)\.\s+[A-Z])", body)
    nums = []
    expect = 1
    chunks = {}
    def roman(n):
        vals = [(50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
        r = ""
        for v, s in vals:
            while n >= v: r += s; n -= v
        return r
    for p in parts:
        m = re.match(r"([IVXL]+)\.\s", p)
        if m and m.group(1) == roman(expect):
            chunks[expect] = p; expect += 1
        elif expect > 1:
            chunks[expect - 1] += " " + p
    return t, chunks


SPLIT_AT = 3000  # words; longer chapters or letters are split into parts at paragraph breaks

def paragraphs(title):
    h = open(ws_file(title, "html"), encoding="utf-8").read()
    h = re.sub(r'<div class="reflist.*', " ", h, flags=re.S)
    ps = [strip_html(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S)]
    return [p for p in ps if words(p) > 0]

def split_unit(u, title):
    """Return u, or u split into balanced parts at paragraph breaks, each with its opening words."""
    if u["words"] <= SPLIT_AT:
        return [u]
    ps = [{"t": p, "w": words(p)} for p in paragraphs(title)]
    k = -(-u["words"] // SPLIT_AT)
    if len(ps) < k:
        return [u]
    parts = balance(ps, k)
    out = []
    for i, g in enumerate(parts, 1):
        v = dict(u)
        opening = " ".join(g[0]["t"].replace("\u200b", " ").split()[:8]) if i > 1 else "the beginning"
        v["ref"] = f"{u['ref']}, part {i} of {k}"
        v["part_starts_with"] = opening
        v["words"] = sum(x["w"] for x in g)
        v["source_notes"] = u["source_notes"] + f" Split at paragraph breaks into {k} parts; this part starts with: {opening if i == 1 else chr(34) + opening + chr(34)}."
        out.append(v)
    return out

def stoics():
    t, ench = enchiridion_chapters()
    n_ench = len(ench)
    tr, _ = ws_meta(t)
    ench_units = [{"ch": k, "w": words(v)} for k, v in sorted(ench.items())]
    ench_days = []
    for g in balance(ench_units, 18):
        ench_days.append({"work": "Enchiridion (Manual)", "author": "Epictetus", "translator": "George Long",
                          "ref": f"Chapters {g[0]['ch']}-{g[-1]['ch']}" if len(g) > 1 else f"Chapter {g[0]['ch']}",
                          "full_text_link": ws_url(t), "words": sum(x["w"] for x in g),
                          "verified": n_ench >= 50 and tr == "George Long",
                          "source_notes": f"Chapter numbers parsed from the Wikisource Encheiridion page (translator '{tr}'); {n_ench} chapters found."})
    epi = epictetus_units()
    for u in epi:
        u["words"] = u.pop("w")
    epi = [p for u in epi for p in split_unit(u, EPI + "/" + u["ref"].replace(", ", "/"))]
    sen = []
    for i in range(1, 125):
        tt = f"{SEN}/Letter {i}"
        tr2, sec = ws_meta(tt)
        body = strip_html(open(ws_file(tt, "html"), encoding="utf-8").read())
        m = re.match(r"Letter\s+\d+\.\s*(.*)", sec)
        sen.append({"work": "Moral Letters to Lucilius", "author": "Seneca", "translator": "Richard Mott Gummere",
                    "ref": f"Letter {i}", "chapter_title": (m.group(1).strip() if m else None), "full_text_link": ws_url(tt),
                    "words": words(body), "verified": tr2 == "Richard Mott Gummere" and sec.startswith(f"Letter {i}.") and words(body) > 150,
                    "source_notes": f"Wikisource page checked: translator '{tr2}', section '{sec}', {words(body)} words."})
    sen = [p for u in sen for p in split_unit(u, SEN + "/" + u["ref"])]
    n_rest = 365 - len(ench_days)
    n_mar = n_rest - len(epi) - len(sen)
    mar = marcus_days(n_mar)
    # interleave the three queues proportionally so all finish together
    queues = [mar, sen, epi]
    idx = [0, 0, 0]; seq = []
    for d in range(n_rest):
        best = max(range(3), key=lambda q: (len(queues[q]) * (d + 1) / n_rest - idx[q]) if idx[q] < len(queues[q]) else -1e9)
        seq.append(queues[best][idx[best]]); idx[best] += 1
    days = ench_days + seq
    for i, d in enumerate(days, 1):
        d["day"] = i
        d["title"] = f"{d['author']}, {d['work']}: {d['ref']}"
    return {"meta": {"path": "stoics", "title": "Stoics in a Year", "count": len(days), "generated": TODAY,
                     "plan": "Week one: Epictetus' Enchiridion. Then Marcus Aurelius, Seneca and Epictetus' Discourses interleaved so all three finish on day 365.",
                     "sources": [SOURCES["marcus"], ws_url(EPI), ws_url(SEN)]}, "days": days}

# ---------------- Shakespeare ----------------
ORDER = ["THE TRAGEDY OF ROMEO AND JULIET", "A MIDSUMMER NIGHT’S DREAM", "THE TRAGEDY OF JULIUS CAESAR", "MUCH ADO ABOUT NOTHING",
         "THE TRAGEDY OF HAMLET, PRINCE OF DENMARK", "TWELFTH NIGHT; OR, WHAT YOU WILL", "THE TRAGEDY OF MACBETH", "THE MERCHANT OF VENICE",
         "THE TRAGEDY OF OTHELLO, THE MOOR OF VENICE", "AS YOU LIKE IT", "THE TRAGEDY OF KING LEAR", "THE TEMPEST",
         "THE LIFE AND DEATH OF KING JOHN", "THE LIFE AND DEATH OF KING RICHARD THE SECOND", "THE FIRST PART OF KING HENRY THE FOURTH",
         "THE SECOND PART OF KING HENRY THE FOURTH", "THE LIFE OF KING HENRY THE FIFTH", "THE FIRST PART OF HENRY THE SIXTH",
         "THE SECOND PART OF KING HENRY THE SIXTH", "THE THIRD PART OF KING HENRY THE SIXTH", "KING RICHARD THE THIRD", "KING HENRY THE EIGHTH",
         "THE TAMING OF THE SHREW", "THE TRAGEDY OF ANTONY AND CLEOPATRA", "THE COMEDY OF ERRORS", "THE TRAGEDY OF CORIOLANUS",
         "THE WINTER’S TALE", "THE TRAGEDY OF TITUS ANDRONICUS", "THE TWO GENTLEMEN OF VERONA", "TROILUS AND CRESSIDA",
         "LOVE’S LABOUR’S LOST", "THE LIFE OF TIMON OF ATHENS", "MEASURE FOR MEASURE", "CYMBELINE", "THE MERRY WIVES OF WINDSOR",
         "PERICLES, PRINCE OF TYRE", "ALL’S WELL THAT ENDS WELL", "THE TWO NOBLE KINSMEN"]
SHORT_FIX = {"THE TRAGEDY OF ": "", "THE LIFE AND DEATH OF ": "", "THE LIFE OF ": ""}

def short_title(t):
    s = t
    for k, v in SHORT_FIX.items():
        s = s.replace(k, v)
    s = s.split(";")[0].split(",")[0] if ("HAMLET" in s or "OTHELLO" in s or "PERICLES" in s or "TWELFTH" in s) else s
    ws = s.split()
    out = " ".join(w.capitalize() if (i == 0 or w not in ("OF", "THE", "AND", "FOR", "ABOUT", "THAT")) else w.lower() for i, w in enumerate(ws))
    return out.replace("’S", "’s")

def shakespeare():
    s = open(os.path.join(SRC, "pg100-images.html"), encoding="utf-8").read()
    txt = open(os.path.join(SRC, "pg100.txt"), encoding="utf-8").read()
    chaps = [(m.group(1), m.start()) for m in re.finditer(r'<a id="(chap\d+)">', s)]
    plays = {}
    for i, (c, pos) in enumerate(chaps):
        end = chaps[i + 1][1] if i + 1 < len(chaps) else len(s)
        seg = s[pos:end]
        title = html.unescape(" ".join(re.sub(r"<[^>]+>", " ", seg[:600]).split())).split(" Contents")[0].strip()
        n = int(c[4:])
        ids = re.findall(r'id="(scene([A-Z]+)_%d\.(\d+))"' % n, seg)
        if ids:
            plays[title] = {"chap": n, "ids": ids, "seg": seg}
    assert sorted(plays) == sorted(ORDER), set(plays) ^ set(ORDER)
    days, k = [], 0
    for t in ORDER:
        p = plays[t]
        acts = []
        for full, a, sc in p["ids"]:
            a2 = "I" if a == "IN" else a
            if not acts or acts[-1][0] != a2:
                acts.append([a2, full, []])
            if sc != "0" and a != "IN":
                acts[-1][2].append(int(sc))
        # text check: the play's body has an ACT heading for each act
        start = txt.find("\n" + t + "\n", txt.find("*** START")+2000)
        nxt = min([txt.find("\n" + o + "\n", start + 10) for o in ORDER if o != t and txt.find("\n" + o + "\n", start + 10) > 0] + [len(txt)])
        body = txt[start:nxt]
        text_acts = re.findall(r"^ACT ([IV]+)\s*$", body, flags=re.M)
        body_acts = list(dict.fromkeys(text_acts))
        for a, anchor, scenes in acts:
            k += 1
            sc = f"Scenes {min(scenes)}-{max(scenes)}" if len(set(scenes)) > 1 else (f"Scene {scenes[0]}" if scenes else "")
            extra = " (with the Induction)" if (a == "I" and "IN" in [x[1] for x in p["ids"]]) else ""
            name = short_title(t)
            days.append({"day": k, "title": f"{name}, Act {a}", "work": name, "author": "William Shakespeare",
                         "ref": f"Act {a}" + (f", {sc}" if sc else "") + extra, "full_text_link": SOURCES["shakespeare_html"] + "#" + anchor,
                         "verified": a in body_acts and len(acts) == 5,
                         "source_notes": f"Act and scene anchors parsed from Project Gutenberg #100 HTML; act heading confirmed in the plain-text edition ({len(body_acts)} act headings found for this play)."})
    return {"meta": {"path": "shakespeare", "title": "Shakespeare, One Act a Day", "count": len(days), "generated": TODAY,
                     "plan": "38 plays, one act a day. Twelve best-known plays first, then the English histories in story order, then the remaining comedies, tragedies and romances alternating.",
                     "sources": [SOURCES["shakespeare_html"], SOURCES["shakespeare_txt"]]}, "days": days}

# ---------------- Shared helpers for Gutenberg texts ----------------
PG = "https://www.gutenberg.org/cache/epub/{id}/pg{id}.txt"
PGH = "https://www.gutenberg.org/cache/epub/{id}/pg{id}-images.html"
NEW_PG_IDS = [2199, 1727, 1004, 1642, 1656, 1657, 1658, 1600, 1636, 1643, 1672, 1497, 1591, 1726, 1572, 8604, 8714, 31, 14484]
COLERIDGE = "The Plays of Euripides (Coleridge)"
EURIPIDES = [("Alcestis", "Alcestis"), ("Medea", "Medea"), ("Hippolytus", "Hippolytus"), ("The Trojan Women", "The Trojan Women"),
             ("Ion", "Ion"), ("Heracleidae", "The Children of Heracles"), ("The Bacchantes", "The Bacchae")]
# Helen is only partly transcribed on Wikisource (Oct 2026), so The Children of Heracles takes its place.
DAY_WORDS = 3000      # prose: split anything longer into parts of about 2,000-3,000 words
DRAMA_WORDS = 2200    # plays: one episode or scene group, about 2,200 words

def fetch_new():
    for i in NEW_PG_IDS:
        for u in (PG.format(id=i), PGH.format(id=i)):
            fn = os.path.join(SRC, os.path.basename(u))
            if not os.path.exists(fn):
                open(fn, "wb").write(get(u)); time.sleep(0.5)
    for p, _ in EURIPIDES:
        t = f"{COLERIDGE}/{p}"
        if not os.path.exists(ws_file(t, "wiki")):
            open(ws_file(t, "wiki"), "w").write(get("https://en.wikisource.org/w/index.php?action=raw&title=" + urllib.parse.quote(t)).decode())
        if not os.path.exists(ws_file(t, "html")):
            d = json.loads(get("https://en.wikisource.org/w/api.php?action=parse&format=json&prop=text&formatversion=2&page=" + urllib.parse.quote(t)))
            open(ws_file(t, "html"), "w").write(d["parse"]["text"])

def pg_lines(i):
    t = open(os.path.join(SRC, f"pg{i}.txt"), encoding="utf-8").read().replace("\r", "")
    t = t[t.find("*** START"):]
    t = t[:t.find("*** END")] if "*** END" in t else t
    return t.split("\n")

def paras(lines):
    out, cur = [], []
    for l in lines + [""]:
        if l.strip():
            cur.append(l.strip())
        elif cur:
            out.append(" ".join(cur)); cur = []
    return out

BAD_ID = re.compile(r"linknote|noteref|FNanchor|Footnote|^id-|^pg-|^img|_t_\d|_n_\d|^fn|^note")

class HtmlIndex:
    """Maps text positions in a Gutenberg HTML file to the nearest preceding anchor id."""
    def __init__(self, i):
        s = open(os.path.join(SRC, f"pg{i}-images.html"), encoding="utf-8").read()
        st = s.find('id="pg-start-separator"')
        s = s[st if st > 0 else 0:]
        self.norm, self.anchors = [], []
        n = 0
        for m in re.finditer(r"<[^>]+>|[^<]+", s):
            tok = m.group(0)
            if tok.startswith("<"):
                a = re.search(r'\bid="([^"]+)"', tok)
                if a and not BAD_ID.search(a.group(1)):
                    self.anchors.append((n, a.group(1)))
            else:
                letters = re.sub(r"[^a-z]", "", html.unescape(tok).lower())
                self.norm.append(letters); n += len(letters)
        self.norm = "".join(self.norm)
        self.cursor = 0
    def anchor_for(self, snippet):
        key = re.sub(r"[^a-z]", "", snippet.lower())[:60]
        if len(key) < 15:
            return None
        p = self.norm.find(key, self.cursor)
        if p < 0:
            p = self.norm.find(key)
        if p < 0:
            return None
        self.cursor = p
        best = None
        for pos, aid in self.anchors:
            if pos <= p: best = aid
            else: break
        return best

def opening(text, n=8):
    return " ".join(text.replace("\u200b", " ").split()[:n])

def split_parts(ps, target, prefer=None):
    """ps: list of paragraph strings. Returns list of lists, balanced near `target` words each."""
    units = [{"t": p, "w": words(p)} for p in ps if words(p) > 0]
    total = sum(u["w"] for u in units)
    k = max(1, round(total / target)) if target == DRAMA_WORDS else max(1, math.ceil(total / target))
    k = min(k, len(units))
    if k == 1:
        return [[u["t"] for u in units]]
    groups = balance(units, k, prefer=(lambda a, b: prefer(b["t"])) if prefer else None, bonus=0.25)
    return [[u["t"] for u in g] for g in groups]

def make_days(path_items, idx=None, gid=None):
    days = []
    for it in path_items:
        days.append(it)
    for i, d in enumerate(days, 1):
        d["day"] = i
    return days

def part_entries(base, groups, link_base, hidx, sn_note):
    out = []
    k = len(groups)
    for i, g in enumerate(groups, 1):
        e = dict(base)
        op = opening(g[0])
        e["ref"] = base["ref"] + (f", part {i} of {k}" if k > 1 else "")
        e["part_starts_with"] = "the beginning" if i == 1 else op
        e["words"] = sum(words(p) for p in g)
        anc = None
        if hidx:
            ws_ = " ".join(g).split()
            for off in (0, 5, 12, 25, 40, 60):
                anc = hidx.anchor_for(" ".join(ws_[off:off + 14]))
                if anc: break
        e["full_text_link"] = link_base + (f"#{anc}" if anc else "")
        e["verified"] = True if hidx is None else anc is not None  # opening words located in the HTML edition
        e["source_notes"] = sn_note + (f" Part {i} of {k}, split at paragraph breaks; starts with \"{op}\"." if k > 1 else "") + (f" Link anchor #{anc} is the nearest anchor before this part." if anc else " No anchor found; link opens the book page.")
        out.append(e)
    return out

# ---------------- Homer ----------------
def homer():
    days = []
    for i, work in ((2199, "Iliad"), (1727, "Odyssey")):
        lines = pg_lines(i)
        heads = [j for j, l in enumerate(lines) if re.match(r"^BOOK [IVXL]+\.?\s*$", l)]
        assert len(heads) == 24, (work, len(heads))
        end = next((j for j, l in enumerate(lines) if j > heads[-1] and re.match(r"^\s*FOOTNOTES:?\s*$", l)), len(lines))
        hidx = HtmlIndex(i)
        for b, h in enumerate(heads):
            body = paras(lines[h + 1:(heads[b + 1] if b < 23 else end)])
            summary = None
            if work == "Iliad" and body and len(body[0].split()) < 80:
                summary = body[0]; body = body[1:]
            if work == "Odyssey" and body and body[0].isupper():
                summary = body[0].capitalize(); body = body[1:]
            body = [re.sub(r"\[\d+\]", "", p) for p in body]
            base = {"work": work, "author": "Homer", "translator": "Samuel Butler", "ref": f"Book {ROMAN24[b]}",
                    "book_summary": summary}
            hidx.cursor = 0 if b == 0 and work == "Iliad" else hidx.cursor
            days += part_entries(base, split_parts(body, DAY_WORDS), PGH.format(id=i), hidx,
                                 f"Book {b+1} of 24 parsed from Project Gutenberg #{i} (Butler prose translation).")
    for d in days:
        d["title"] = f"Homer, {d['work']}: {d['ref']}"
    days = make_days(days)
    return {"meta": {"path": "homer", "title": "Homer: the Iliad and the Odyssey", "count": len(days), "generated": TODAY,
                     "plan": "The Iliad, then the Odyssey, book by book; each book split at paragraph breaks into parts of about 2,000 to 3,000 words.",
                     "sources": [PG.format(id=2199), PG.format(id=1727)]}, "days": days}

ROMAN24 = ["I","II","III","IV","V","VI","VII","VIII","IX","X","XI","XII","XIII","XIV","XV","XVI","XVII","XVIII","XIX","XX","XXI","XXII","XXIII","XXIV"]

# ---------------- Plato ----------------
PLATO = [(1642, "Euthyphro"), (1656, "Apology"), (1657, "Crito"), (1658, "Phaedo"), (1600, "Symposium"), (1636, "Phaedrus"),
         (1643, "Meno"), (1672, "Gorgias"), (1497, "Republic"), (1591, "Protagoras"), (1726, "Theaetetus"), (1572, "Timaeus")]

def plato():
    days = []
    for i, name in PLATO:
        lines = pg_lines(i)
        if name == "Apology":
            st = max(j for j, l in enumerate(lines) if l.strip() == "APOLOGY")
        else:
            st = [j for j, l in enumerate(lines) if "PERSONS OF THE DIALOGUE" in l][-1]
        end = next((j for j, l in enumerate(lines) if j > st and re.match(r"^\s*FOOTNOTES:?\s*$", l)), len(lines))
        hidx = HtmlIndex(i)
        sn = f"Dialogue text (Jowett's introduction excluded) parsed from Project Gutenberg #{i}."
        if name == "Republic":
            heads = [j for j, l in enumerate(lines) if j > st and re.match(r"^\s*BOOK [IVX]+\.?\s*$", l)]
            assert len(heads) == 10, len(heads)
            for b, h in enumerate(heads):
                body = paras(lines[h + 1:(heads[b + 1] if b < 9 else end)])
                base = {"work": "Republic", "author": "Plato", "translator": "Benjamin Jowett", "ref": f"Book {ROMAN24[b]}"}
                days += part_entries(base, split_parts(body, DAY_WORDS), PGH.format(id=i), hidx, sn + f" Book {b+1} of 10.")
        else:
            body = paras(lines[st + 1:end])
            # drop the persons list and scene line at the top
            while body and words(body[0]) < 12 and ":" not in body[0][:20]:
                body = body[1:]
            base = {"work": name, "author": "Plato", "translator": "Benjamin Jowett", "ref": "Whole dialogue"}
            days += part_entries(base, split_parts(body, DAY_WORDS), PGH.format(id=i), hidx, sn)
    for d in days:
        d["title"] = f"Plato, {d['work']}" + ("" if d["ref"] == "Whole dialogue" else f": {d['ref']}")
        if d["ref"].startswith("Whole dialogue, "):
            d["ref"] = d["ref"].replace("Whole dialogue, ", "").capitalize()
            d["title"] = f"Plato, {d['work']}: {d['ref']}"
    days = make_days(days)
    return {"meta": {"path": "plato", "title": "Plato's Dialogues", "count": len(days), "generated": TODAY,
                     "plan": "The trial and death of Socrates (Euthyphro, Apology, Crito, Phaedo), then Symposium, Phaedrus, Meno, Gorgias, the Republic (10 books), Protagoras, Theaetetus and Timaeus. Parts of about 2,000 to 3,000 words split at paragraph breaks.",
                     "sources": [PG.format(id=i) for i, _ in PLATO]}, "days": days}

# ---------------- Dante ----------------
def dante():
    lines = pg_lines(1004)
    heads = [(j, m.group(1), m.group(2)) for j, l in enumerate(lines) for m in [re.match(r"^(Inferno|Purgatorio|Paradiso): Canto ([IVXL]+)\s*$", l)] if m]
    assert [h[1] for h in heads].count("Inferno") == 34 and len(heads) == 100, len(heads)
    s = open(os.path.join(SRC, "pg1004-images.html"), encoding="utf-8").read()
    ids = set(re.findall(r'id="(Canto[IVX]+\.[IVXL]+)"', s))
    cant = {"Inferno": "I", "Purgatorio": "II", "Paradiso": "III"}
    days = []
    for k, (j, part, num) in enumerate(heads):
        nxt = heads[k + 1][0] if k + 1 < len(heads) else next((x for x in range(j, len(lines)) if re.match(r"^\s*(APPENDIX|Notes|NOTES)\s*$", lines[x])), len(lines))
        body = [l for l in lines[j + 1:nxt] if l.strip()]
        aid = f"Canto{cant[part]}.{num}"
        days.append({"title": f"Dante, {part}: Canto {num}", "work": f"Divine Comedy, {part}", "author": "Dante Alighieri",
                     "translator": "Henry Wadsworth Longfellow", "ref": f"{part}, Canto {num}",
                     "full_text_link": PGH.format(id=1004) + "#" + aid, "lines": len(body), "words": words(" ".join(body)),
                     "verified": aid in ids and len(body) > 100,
                     "source_notes": f"Canto heading found in Project Gutenberg #1004 (Longfellow) plain text ({len(body)} verse lines); HTML anchor #{aid} {'present' if aid in ids else 'missing'}."})
    days = make_days(days)
    return {"meta": {"path": "dante", "title": "Dante, One Canto a Day", "count": len(days), "generated": TODAY,
                     "plan": "Inferno (34 cantos), Purgatorio (33), Paradiso (33): one canto a day.", "sources": [PG.format(id=1004), PGH.format(id=1004)]}, "days": days}

# ---------------- Greek tragedies ----------------
SPEAKER = re.compile(r"^[A-Z][A-Z .,’'Æ-]{1,40}\.?$")
def is_chorus(p):
    return bool(re.match(r"^(\d+\w*\s+)?(CHORUS|LEADER OF (THE )?CH|SEMI-?CHORUS|CH\.|Chorus|Cho\b|Ch\b|Semi-?cho|STROPHE|Strophe)", p.strip()))

# (gutenberg id, title in text, play name, translator, death year, first published)
PLAYS = [
    (8604, "AGAMEMNON", "Agamemnon", "Aeschylus", "E. D. A. Morshead", 1912, "1881"),
    (8604, "THE LIBATION-BEARERS", "The Libation Bearers", "Aeschylus", "E. D. A. Morshead", 1912, "1881"),
    (8604, "THE FURIES", "The Eumenides (The Furies)", "Aeschylus", "E. D. A. Morshead", 1912, "1881"),
    (8714, "PROMETHEUS BOUND", "Prometheus Bound", "Aeschylus", "E. D. A. Morshead", 1912, "1908"),
    (8714, "THE PERSIANS", "The Persians", "Aeschylus", "E. D. A. Morshead", 1912, "1908"),
    (8714, "THE SEVEN AGAINST THEBES", "Seven Against Thebes", "Aeschylus", "E. D. A. Morshead", 1912, "1908"),
    (8714, "THE SUPPLIANT MAIDENS", "The Suppliant Maidens", "Aeschylus", "E. D. A. Morshead", 1912, "1908"),
    (31, "OEDIPUS THE KING", "Oedipus the King", "Sophocles", "Francis Storr", 1919, "1912"),
    (31, "OEDIPUS AT COLONUS", "Oedipus at Colonus", "Sophocles", "Francis Storr", 1919, "1912"),
    (31, "ANTIGONE", "Antigone", "Sophocles", "Francis Storr", 1919, "1912"),
    (14484, "AIAS", "Ajax", "Sophocles", "Lewis Campbell", 1908, "1883"),
    (14484, "ELECTRA", "Electra", "Sophocles", "Lewis Campbell", 1908, "1883"),
    (14484, "THE TRACHINIAN MAIDENS", "The Women of Trachis", "Sophocles", "Lewis Campbell", 1908, "1883"),
    (14484, "PHILOCTETES", "Philoctetes", "Sophocles", "Lewis Campbell", 1908, "1883"),
]

def play_body(i, title):
    lines = pg_lines(i)
    persons = [j for j, l in enumerate(lines) if re.match(r"^\s*(DRAMATIS PERSONAE|THE PERSONS)\s*$", l)]
    # the play starts at the persons list that follows the title heading
    tpos = [j for j, l in enumerate(lines) if l.strip() == title]
    pairs = [(t, p) for t in tpos for p in persons if abs(p - t) < 40]
    t0, p0 = pairs[-1] if title != "AGAMEMNON" else pairs[0]
    st = max(t0, p0)
    later = [p for p in persons if p > st + 5]
    end = later[0] if later else len(lines)
    # cut notes and the next play's argument
    for j in range(st + 1, end):
        if re.match(r"^\s*(FOOTNOTES|NOTES|ARGUMENT)\.?\s*$", lines[j]):
            end = j; break
    ps = paras(lines[st + 1:end])
    titles = {p[1] for p in PLAYS if p[0] == i} | {"KING OEDIPUS", "OEDIPUS AT COLONOS", "ANTIGONE", "AIAS"}
    for n, p in enumerate(ps):
        if n > 20 and p.strip() in titles:
            ps = ps[:n]; break
    while ps and re.match(r"^[*\s]+$", ps[-1]):
        ps.pop()
    ps = [re.sub(r"^([B-HJ-Z]) ([a-z])", r"\1\2", p) for p in ps if not re.match(r"^\[\d+\]", p)]  # drop footnotes; fix drop caps like "L ord"
    sc = [n for n in range(min(40, len(ps))) if ps[n].startswith("SCENE")]
    rt = [n for n in range(min(40, len(ps))) if ps[n].strip() == title]
    if i == 14484 and rt:
        k = rt[0] + 1
    elif i == 14484 and sc:
        k = sc[0] + 1
    elif i == 14484:  # Campbell: skip the prose argument and cast list, start at the first speech
        k = next(n for n in range(len(ps)) if re.match(r"^[A-ZÊÆ][A-ZÊÆ .’'-]{1,40}\.\s+\S", ps[n]) or (SPEAKER.match(ps[n]) and n + 1 < len(ps) and words(ps[n + 1]) > 8 and n > 0 and words(ps[n - 1]) > 0 and not SPEAKER.match(ps[n - 1])))
    else:
        k = next(n for n in range(len(ps)) if words(ps[n]) > 25)
        while k > 0 and SPEAKER.match(ps[k - 1]) and words(ps[k - 1]) <= 6:
            k -= 1
    ps = ps[k:]
    # merge speaker headings into the speech that follows
    merged = []
    for p in ps:
        if merged and SPEAKER.match(merged[-1]) and words(merged[-1]) <= 6:
            merged[-1] = merged[-1] + " " + p
        else:
            merged.append(p)
    return merged, st

def tragedies():
    days = []
    for i, ttl, name, author, tr, died, pub in PLAYS:
        body, st = play_body(i, ttl)
        hidx = HtmlIndex(i)
        sn = f"{name} parsed from Project Gutenberg #{i} ({tr}, d. {died}; first published {pub}): public domain worldwide."
        base = {"work": name, "author": author, "translator": tr, "ref": name}
        days += part_entries(base, split_parts(body, DRAMA_WORDS, prefer=is_chorus), PGH.format(id=i), hidx, sn)
    for p, name in EURIPIDES:
        t = f"{COLERIDGE}/{p}"
        trn, sec = ws_meta(t)
        h = open(ws_file(t, "html"), encoding="utf-8").read()
        h = re.sub(r'<div class="reflist.*', " ", h, flags=re.S)
        ps = [strip_html(x) for x in re.findall(r"<p[^>]*>(.*?)</p>", h, flags=re.S)]
        ps = [x for x in ps if words(x) > 0]
        k = next(n for n in range(len(ps)) if words(ps[n]) > 25)
        ps = ps[k:]
        sn = f"Wikisource page checked: translator '{trn}', section '{sec}' (E. P. Coleridge, d. 1936; published 1891): public domain worldwide."
        groups = split_parts(ps, DRAMA_WORDS, prefer=is_chorus)
        base = {"work": name, "author": "Euripides", "translator": "Edward Philip Coleridge", "ref": name}
        ents = part_entries(base, groups, ws_url(t), None, sn)
        for e in ents:
            e["full_text_link"] = ws_url(t)
            e["verified"] = trn == "Edward Philip Coleridge" and len(ps) > 50
            e["source_notes"] = e["source_notes"].replace(" No anchor found; link opens the book page.", "")
        days += ents
    for d in days:
        d["title"] = f"{d['author']}, {d['ref']}"
    days = make_days(days)
    return {"meta": {"path": "tragedies", "title": "The Greek Tragedies", "count": len(days), "generated": TODAY,
                     "plan": "Seven plays each by Aeschylus, Sophocles and Euripides, one episode or scene group (about 2,200 words) a day, split at speech breaks and preferring breaks before a choral passage.",
                     "sources": sorted(set(PG.format(id=p[0]) for p in PLAYS)) + [ws_url(COLERIDGE)]}, "days": days}


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch(); fetch_new()
    out = {"stoics.json": stoics(), "shakespeare.json": shakespeare(), "homer.json": homer(),
           "plato.json": plato(), "dante.json": dante(), "tragedies.json": tragedies()}
    for fn, data in out.items():
        json.dump(data, open(os.path.join(HERE, "plans", fn), "w"), indent=1, ensure_ascii=False)
        v = sum(1 for d in data["days"] if d["verified"])
        print(f"{fn}: {len(data['days'])} days, {v} verified")
