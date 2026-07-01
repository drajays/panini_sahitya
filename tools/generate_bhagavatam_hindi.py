#!/usr/bin/env python3
"""Extract Hindi verse meanings from the Gita Press Srimad Bhagavat Mahapuran
(Sanskrit-Hindi) OCR text and merge them into data/bhagavatam.json as the
'hs' field (same convention as data/gita.json), so the app's existing
Hindi-meaning tab picks them up with no front-end changes.

Source: two djvu-OCR .txt volumes (Sanskrit shlokas + Hindi prose meaning,
in Gita Press book order). The OCR is noisy (stray watermark lines, garbled
characters), so this is a best-effort heuristic extractor, not a precise
parser. Expect partial coverage; verses that don't confidently match get no
'hs' field rather than a wrong one.

Method:
  1. Split each volume into paragraphs (blank-line separated), dropping
     paragraphs that are mostly OCR watermark junk (not Devanagari).
  2. Track (skandha, chapter) by scanning colophon lines
     ("इति श्रीमद्भागवते महापुराणे ... संहितायां <skandha>स्कन्धे ...
     <ordinal>ऽध्यायः ।।N।।"): the skandha number comes from matching the
     (sandhi'd, sometimes misspelled) skandha-name word immediately before
     "स्कन्धे", and the chapter number from the trailing "।।N।।" marker. A
     colophon paragraph marks the END of a chapter, so the paragraphs
     buffered since the previous colophon are that chapter's own content
     and get flushed under the newly-parsed (skandha, chapter) - not the
     one from before this colophon.
  3. Within each chapter's running text, split on verse-end markers
     ("।।N।।", "।।N-M।।", ASCII-digit variants) and score the text segment
     before each marker for "Hindi-ness" (function-word density). Sanskrit
     shloka segments score near 0 and are discarded; Hindi meaning segments
     score higher and are kept as the meaning for that verse number
     (verse ranges like 70-71 get the same combined text). Known junk that
     leaks into chapter-opening segments (page footnotes, "अथ Nऽध्यायः"
     heading banners) is stripped.
  4. Merge into data/bhagavatam.json 'data' entries by "skandha.chapter"
     ("c") + verse number ("n").
"""
import json
import os
import re
import sys

ROOT = os.path.join(os.path.dirname(__file__), '..')
SRC_DIR = os.path.expanduser(
    '~/srimad-bhagavat-mahapuran-2-volume-set-sanskrit-hindi')
VOLUMES = [
    'Srimad Bhagavat Mahapuran Volume 1 Sanskrit Hindi_djvu.txt',
    'Srimad Bhagavat Mahapuran Volume 2 Sanskrit Hindi_djvu.txt',
]
BHAG_JSON = os.path.join(ROOT, 'data', 'bhagavatam.json')

DEVANAGARI_RE = re.compile(r'[ऀ-ॿ]')
JUNK_RE = re.compile(r'एशॉश|शायय|शाय।|शाय।द|शा।गह')

# Colophon skandha names, as they actually appear after sandhi with the
# preceding "संहितायाम्" (e.g. "संहितायामष्टमस्कन्धे" swallows the leading
# vowel of "अष्टम"/"एकादश"), plus common OCR misspellings of "पञ्चम".
# Longest/most specific alternatives first so e.g. "द्वादश" wins over "दश".
SKANDHA_WORDS = [
    ('द्वादश', 12), ('कादश', 11), ('एकादश', 11), ('दशम', 10), ('नवम', 9),
    ('ष्टम', 8), ('अष्टम', 8), ('सप्तम', 7), ('षष्ठ', 6),
    ('पञ्चम', 5), ('पजञ्चम', 5), ('पजचम', 5), ('पठचम', 5), ('पडचम', 5),
    ('पञजचम', 5), ('पचम', 5),
    ('चतुर्थ', 4), ('तृतीय', 3), ('द्वितीय', 2), ('प्रथम', 1),
]
COLOPHON_RE = re.compile(r'इति\s+श्रीमद्.{0,4}ागवते\s+महापुराणे')
DEV_DIGITS = str.maketrans('०१२३४५६७८९', '0123456789')
MARK_RE = re.compile(
    r'[।॥]{1,3}\s*([0-9०-९]{1,3})(?:\s*[-–]\s*([0-9०-९]{1,3}))?\s*[।॥]{0,3}')

HINDI_WORDS = set('''है हैं था थे थी हुआ हुई हुए गया गयी गये कहा लिये तथा और
यह वह वे कि जो ने को से में का की के पर हो कर करते करता रहे रहा रही अपने
उनके इसके उसके किया गयी'''.split())

HINDI_SCORE_THRESHOLD = 0.08
MIN_SEGMENT_WORDS = 3


def to_int(devnum):
    return int(devnum.translate(DEV_DIGITS))


def load_clean_paragraphs(path):
    """Return list of paragraphs (blank-line separated), junk lines dropped."""
    text = open(path, encoding='utf-8').read()
    paras, cur = [], []
    for line in text.split('\n'):
        s = line.strip()
        if not s:
            if cur:
                paras.append(' '.join(cur))
                cur = []
            continue
        if JUNK_RE.search(s):
            continue
        devanagari_chars = len(DEVANAGARI_RE.findall(s))
        if len(s) > 5 and devanagari_chars / len(s) < 0.3:
            continue  # mostly non-Devanagari OCR noise
        cur.append(s)
    if cur:
        paras.append(' '.join(cur))
    return paras


def hindi_score(segment):
    words = segment.split()
    if not words:
        return 0.0
    hits = sum(1 for w in words if w.strip('।॥,.-–—‌') in HINDI_WORDS)
    return hits / len(words)


# Page-footnote asides ("प्रा० पा०--variant reading..." closed by a smart
# quote) and "अथ ...अध्यायः" chapter-heading banners (followed by the
# chapter's title, its Sanskrit speaker tag, and its shloka-1 text) sometimes
# get swept into the meaning of a chapter's first verse, ahead of where its
# real Hindi meaning ("...जी कहते हैं--...") actually starts.
FOOTNOTE_PREFIX_RE = re.compile(r'^\s*[.,]?\s*प्रा०\s*पा०.*?[”"]\s*')
CHAPTER_HEADING_RE = re.compile(r'अथ\s*\S{0,20}ध्याय[:ःA-Za-z\'‌]*')
HINDI_DIALOGUE_RE = re.compile(
    r'\S*जी(?:ने)?\s*(?:कहते\s*हैं|बोले|कहने\s*लगे|कहा)\s*--')


def clean_segment(text):
    text = FOOTNOTE_PREFIX_RE.sub('', text)
    heading = CHAPTER_HEADING_RE.search(text)
    if heading:
        dialogue = HINDI_DIALOGUE_RE.search(text, heading.end())
        text = text[dialogue.start():] if dialogue else text[:heading.start()]
    return text.strip()


def parse_colophon(paragraph, match_end):
    """Given a colophon match's end offset in `paragraph`, find the skandha
    number (from the sandhi'd skandha name) and chapter number (from the
    trailing '।।N।।' marker), both within the same paragraph."""
    window = paragraph[match_end:match_end + 400]
    # The skandha name sits immediately before "स्कन्धे"; matching anywhere
    # in the window would also catch the chapter's ordinal word later on
    # (e.g. "...प्रथमस्कन्धे...तृतीयोऽध्यायः" both contain "तृतीय"-like
    # tokens), so only look at the slice right before "स्कन्धे".
    skandha = None
    idx = window.find('स्कन्धे')
    if idx != -1:
        prefix = window[max(0, idx - 20):idx]
        for word, num in SKANDHA_WORDS:
            if prefix.endswith(word):
                skandha = num
                break
        if skandha is None:
            for word, num in SKANDHA_WORDS:
                if word in prefix:
                    skandha = num
                    break
    mark = MARK_RE.search(window)
    chapter = to_int(mark.group(1)) if mark else None
    return skandha, chapter


def extract_hindi_map(paragraphs):
    """Walk paragraphs, tracking skandha/chapter via colophons, and pull
    Hindi-meaning segments keyed by 'skandha.chapter|versenum'."""
    hindi_map = {}
    skandha, chapter = 1, 0
    buffer = []
    seen_first_colophon = False

    def flush(buf_paragraphs, sk, ch):
        if not buf_paragraphs or ch == 0 or sk is None:
            return
        chapter_text = ' '.join(buf_paragraphs)
        parts = MARK_RE.split(chapter_text)
        # parts = [text0, num1, num1b, text1, num2, num2b, ..., textN]
        i = 0
        while i + 2 < len(parts):
            segment, num1, num1b = parts[i], parts[i + 1], parts[i + 2]
            if segment and hindi_score(segment) >= HINDI_SCORE_THRESHOLD \
                    and len(segment.split()) >= MIN_SEGMENT_WORDS:
                lo = to_int(num1)
                hi = to_int(num1b) if num1b else lo
                text = clean_segment(segment)
                if not text:
                    i += 3
                    continue
                for n in range(lo, hi + 1):
                    key = f'{sk}.{ch}|{n}'
                    if key in hindi_map:
                        hindi_map[key] += ' ' + text
                    else:
                        hindi_map[key] = text
            i += 3

    for p in paragraphs:
        m = COLOPHON_RE.search(p)
        if m:
            buffer.append(p)
            # A colophon paragraph announces "chapter X just ended", and the
            # buffer accumulated since the *previous* colophon is exactly
            # chapter X's own content - so it must be flushed under the
            # newly-parsed (skandha, chapter), not the still-old one.
            new_skandha, new_chapter = parse_colophon(p, m.end())
            if new_skandha is not None:
                if new_chapter is None:
                    # marker digits weren't found (OCR gap): assume the
                    # chapter count just advanced by one within the skandha
                    new_chapter = chapter + 1 if new_skandha == skandha else 1
                # The buffer preceding the very first colophon in a volume
                # is front matter (publisher's preface, dedication, etc.),
                # not chapter content - discard it rather than mislabel it
                # as the first chapter's meaning.
                if seen_first_colophon:
                    flush(buffer, new_skandha, new_chapter)
                seen_first_colophon = True
                skandha, chapter = new_skandha, new_chapter
            elif seen_first_colophon:
                flush(buffer, skandha, chapter)
            buffer = []
        else:
            buffer.append(p)
    flush(buffer, skandha, chapter)
    return hindi_map


def main():
    hindi_map = {}
    for vol in VOLUMES:
        path = os.path.join(SRC_DIR, vol)
        if not os.path.exists(path):
            print(f'WARNING: missing {path}', file=sys.stderr)
            continue
        print(f'Reading {vol}...')
        paragraphs = load_clean_paragraphs(path)
        vol_map = extract_hindi_map(paragraphs)
        print(f'  {len(vol_map)} verse meanings extracted')
        hindi_map.update(vol_map)

    print(f'Total Hindi meanings extracted: {len(hindi_map)}')

    bhag = json.load(open(BHAG_JSON, encoding='utf-8'))
    matched = 0
    total_verses = 0
    for entry in bhag['data']:
        if entry.get('n') is None or not entry.get('v'):
            continue
        total_verses += 1
        key = f"{entry['c']}|{entry['n']}"
        hs = hindi_map.get(key)
        if hs:
            entry['hs'] = hs
            matched += 1

    print(f'Matched {matched}/{total_verses} verses '
          f'({100 * matched / total_verses:.1f}%)')

    out_path = os.path.join(ROOT, 'data', 'bhagavatam.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(bhag, f, ensure_ascii=False, separators=(',', ':'))
    print(f'Wrote {out_path}')


if __name__ == '__main__':
    main()
