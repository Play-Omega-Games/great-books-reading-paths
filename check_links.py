#!/usr/bin/env python3
"""Check that every unique page URL in the datasets resolves (HTTP 200)."""
import os, json, urllib.request, concurrent.futures as cf
FILES = ("stoics.json", "shakespeare.json", "homer.json", "plato.json", "dante.json", "tragedies.json")
urls = sorted({d["full_text_link"].split("#")[0] for fn in FILES for d in json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plans", fn)))["days"]})
def check(u):
    try:
        return u, urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).status
    except Exception as e:
        return u, str(e)
with cf.ThreadPoolExecutor(6) as ex:
    res = list(ex.map(check, urls))
bad = [r for r in res if r[1] != 200]
print(f"checked {len(res)} URLs, {len(bad)} failed")
for b in bad: print(b)
