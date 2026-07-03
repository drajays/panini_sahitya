"""
Post-process manas_arth_sahit.json to clean up noise entries and re-sequence IDs.
Also removes entries where 'v' is clearly noise (breadcrumbs, very short, OCR junk).
"""
import json, re

IN = OUT = '/Users/dr.ajayshukla/Panini_sahitya/data/manas_arth_sahit.json'

NOISE_V_RE = re.compile(
    r'^\(_|'          # breadcrumb
    r'^_.*?»|'        # breadcrumb
    r'^<__|'          # breadcrumb
    r'^\*\s*.*?\*',   # page header
    re.UNICODE
)

def is_noise_entry(r):
    v = r['v'].strip()
    # Too short to be a verse
    if len(v) < 10:
        return True
    # Clearly a breadcrumb/noise line
    if NOISE_V_RE.match(v):
        return True
    return False

with open(IN, 'r', encoding='utf-8') as f:
    book = json.load(f)

original = len(book['data'])
clean = [r for r in book['data'] if not is_noise_entry(r)]

# Re-number IDs and verse counter per kaand
vctr = {}
for i, r in enumerate(clean):
    r['id'] = i + 1
    c = r['c']
    vctr[c] = vctr.get(c, 0) + 1
    r['n'] = vctr[c]

book['data'] = clean
book['total'] = len(clean)

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(book, f, ensure_ascii=False, indent=2)

print(f"Original: {original}  →  After cleanup: {len(clean)}")
print(f"Removed: {original - len(clean)} noise entries")

from collections import defaultdict
km = defaultdict(int)
for r in clean:
    km[r['kanda']] += 1
print("\nFinal kaanda counts:")
for k, n in km.items():
    print(f"  {k}: {n}")
