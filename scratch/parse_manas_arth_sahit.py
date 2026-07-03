"""
Parse 'Shri Ramcharitmanas - Gita Press (Hindi)_djvu.txt' into structured JSON.
Creates ONLY: data/manas_arth_sahit.json — does NOT touch any other file.

OCR Sopana headings (garbled by DJVU OCR):
  Line 1:     प्रथम सोपान     → 1 (बालकाण्ड)
  Line 15983: ह्ितीय सोपान   → 2 (अयोध्याकाण्ड)  [OCR error for द्वितीय]
  Line 29406: तृतीय सोपान    → 3 (अरण्यकाण्ड)
  Line 32563: अतुर्थ सोपान   → 4 (किष्किन्धाकाण्ड) [OCR error for चतुर्थ]
  Line 34265: पद्ञम सोपान    → 5 (सुन्दरकाण्ड) [OCR error for पंचम]
  Line 37092: घष्ठ सोपान     → 6 (लंकाकाण्ड) [OCR error for षष्ठ]
  Line 43925: सप्तम सोपान    → 7 (उत्तरकाण्ड)
Strategy: match any short line ending with "सोपान" and increment kaand counter.
"""

import re, json

SRC = '/Users/dr.ajayshukla/Downloads/Shri Ramcharitmanas - Gita Press (Hindi)_djvu.txt'
OUT = '/Users/dr.ajayshukla/Panini_sahitya/data/manas_arth_sahit.json'

KANDA_DISPLAY = {1:'बालकाण्ड', 2:'अयोध्याकाण्ड', 3:'अरण्यकाण्ड',
                 4:'किष्किन्धाकाण्ड', 5:'सुन्दरकाण्ड', 6:'लंकाकाण्ड', 7:'उत्तरकाण्ड'}

# Match a standalone sopana heading line (short line ending in सोपान)
# Avoids false positives like verse lines mentioning सोपाना
SOPANA_HEADING_RE = re.compile(r'^.{2,15}\s+सोपान\s*$', re.UNICODE)
# Lines that are definitely NOT sopana headings (they contain verse content)
SOPANA_EXCLUDE_RE = re.compile(r'[।॥]|करि|सुंदर|रचि|सरु|मनि|निर्मल|सुभग|सलिल', re.UNICODE)

# End markers for sections
SECTION_END_RE = re.compile(r'इति श्रीमद्रामचरितमानसे|यह .+सोपान समाप्त')

# Type markers
DOHA_RE    = re.compile(r'^दो[०0]\s*[-।—–]+\s*')
SORTHA_RE  = re.compile(r'^सो[०0]\s*[-।—–]+\s*')
CHAND_RE   = re.compile(r'^छं[०0]?\s*[-।—–]+\s*')
MANGAL_RE  = re.compile(r'^मं[०0]?\s*[-।—–]+\s*')
SHLOKA_RE  = re.compile(r'^श्लोक\s*$')

# Page noise
NOISE_RE = re.compile(
    r'^\*\s*(रामचरितमानस|.*?काण्ड)\s*\*|'
    r'^\d+\s*\*\s*रामचरितमानस|'
    r'^\(_.*_>|'
    r'^_.*?काण्ड »|'
    r'^<__.*?काण्ड',
    re.UNICODE
)

BARE_DANDA   = re.compile(r'[।॥]+\s*$')
NUMBERED_END = re.compile(r'॥\s*\d+(?:\s*\(\s*[कखगघञ]\s*\))?\s*॥\s*$')

def is_numbered(s): return bool(NUMBERED_END.search(s))
def is_bare(s):
    return bool(BARE_DANDA.search(s.strip())) and not is_numbered(s.strip())


def parse():
    with open(SRC, 'r', encoding='utf-8') as f:
        raw_lines = [l.rstrip('\n') for l in f]

    records = []
    gid = 0
    kanda_num = 1          # Start at 1; will increment on each sopana heading
    kanda_seen = 0         # How many sopana headings we've seen
    vtype = 'chaupai'
    vlines, mlines = [], []
    state = 'verse'
    vctr = {i: 0 for i in range(1, 8)}

    def flush():
        nonlocal gid
        v = '\n'.join(l for l in vlines if l.strip()).strip()
        hs = '\n'.join(l for l in mlines if l.strip()).strip()
        if v and len(v) > 4:
            gid += 1
            vctr[kanda_num] += 1
            records.append({'id': gid, 'c': kanda_num,
                            'kanda': KANDA_DISPLAY[kanda_num],
                            'type': vtype, 'n': vctr[kanda_num],
                            'v': v, 'hs': hs})

    def new_type(t):
        nonlocal vtype, vlines, mlines, state
        flush()
        vlines, mlines = [], []
        state = 'verse'
        vtype = t

    for line in raw_lines:
        stripped = line.strip()

        # ---- 1. Blank lines → skip ----
        if not stripped:
            continue

        # ---- 2. Section end markers → skip ----
        if SECTION_END_RE.search(stripped):
            continue

        # ---- 3. Sopana heading → kaand boundary ----
        if (SOPANA_HEADING_RE.match(stripped)
                and not SOPANA_EXCLUDE_RE.search(stripped)):
            flush()
            vlines, mlines = [], []
            state = 'verse'
            vtype = 'chaupai'
            kanda_seen += 1
            kanda_num = min(kanda_seen, 7)
            continue

        # ---- 4. Page noise → skip ----
        if NOISE_RE.match(stripped):
            continue

        # ---- 5. Type markers ----
        if SHLOKA_RE.match(stripped):
            new_type('shloka'); continue

        def handle_marker(marker_re, t):
            nonlocal state
            new_type(t)
            rest = marker_re.sub('', stripped).strip()
            if rest:
                vlines.append(rest)
                if is_numbered(rest):
                    state = 'meaning'

        if DOHA_RE.match(stripped):   handle_marker(DOHA_RE, 'doha');    continue
        if SORTHA_RE.match(stripped): handle_marker(SORTHA_RE, 'sortha'); continue
        if CHAND_RE.match(stripped):  handle_marker(CHAND_RE, 'chand');   continue
        if MANGAL_RE.match(stripped): handle_marker(MANGAL_RE, 'mangal'); continue

        # ---- 6. Regular content ----
        if state == 'verse':
            if is_bare(stripped):
                vlines.append(stripped)
            elif is_numbered(stripped):
                if vtype in ('doha','sortha','chand','mangal','shloka'):
                    vlines.append(stripped)
                    state = 'meaning'
                else:
                    # Chaupai context: a ॥N॥ line = doha at end of chaupai group
                    if vlines:
                        flush()
                        vlines = [stripped]
                        mlines = []
                        vtype = 'doha'
                        state = 'meaning'
                    else:
                        vlines.append(stripped)
                        state = 'meaning'
            else:
                # No danda → meaning begins (or intro text if no verse yet)
                if vlines:
                    state = 'meaning'
                    mlines.append(stripped)
                else:
                    vlines.append(stripped)

        else:  # state == 'meaning'
            if is_bare(stripped):
                # New chaupai verse starting
                new_type('chaupai')
                vlines.append(stripped)
            else:
                mlines.append(stripped)

    flush()
    return records


def main():
    print("Parsing DJVU → manas_arth_sahit.json ...")
    records = parse()

    print(f"\nTotal entries: {len(records)}")

    kanda_counts, type_counts = {}, {}
    for r in records:
        kanda_counts[r['kanda']] = kanda_counts.get(r['kanda'], 0) + 1
        type_counts[r['type']]   = type_counts.get(r['type'], 0) + 1

    print("\nKaanda breakdown:")
    for k in KANDA_DISPLAY.values():
        print(f"  {k}: {kanda_counts.get(k, 0)}")

    print("\nType breakdown:")
    for t, n in sorted(type_counts.items()):
        print(f"  {t}: {n}")

    with_meaning = sum(1 for r in records if r.get('hs','').strip())
    print(f"\nEntries WITH Hindi arth: {with_meaning} / {len(records)}"
          f"  ({100*with_meaning//len(records) if records else 0}%)")

    out = {"title": "श्रीरामचरितमानस (अर्थ सहित)",
           "subtitle": "गीता प्रेस, गोरखपुर",
           "source": "Gita Press DJVU OCR",
           "total": len(records),
           "data": records}

    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved → {OUT}")

    # Sample from each kaanda
    print("\n=== One sample from each kaanda ===")
    shown = set()
    for r in records:
        k = r['c']
        if k not in shown and r['hs'].strip():
            shown.add(k)
            print(f"\n[{r['kanda']} | {r['type']} #{r['n']}]")
            print(f"  v:  {r['v'][:150]}")
            print(f"  hs: {r['hs'][:150]}")


if __name__ == '__main__':
    main()
