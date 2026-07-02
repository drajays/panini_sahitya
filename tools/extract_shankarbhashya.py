#!/usr/bin/env python3
"""Extract per-verse Hindi Shankara-bhashya from the Gita Press OCR dataset.

Source: ~/gita_shankarbhashya_dataset/json/NN_*.json (two-column OCR text,
Sanskrit bhashya left, Hindi translation right, interleaved in strips).

Output: per-verse Hindi bhashya keyed by chapter/verse, written to
data/shankarbhashya.json and optionally merged into data/gita.json as "sb".
"""
import json
import re
import sys
from pathlib import Path

DATASET = Path.home() / 'gita_shankarbhashya_dataset' / 'json'
REPO = Path(__file__).resolve().parent.parent

HDR = re.compile(r'^\*.{0,40}(गीता|गवद|भाष्य|अध्याय)')
PAGENUM = re.compile(r'^[०-९0-9]+\s*[»>]?\s*$')
MARKER = re.compile(r'॥\s*([०-९]+)\s*॥')
TOKEN = re.compile(r'[क़-ॡअ-हऀ-ॄॅ-्ॐ]+')

HI_STRONG = set(
    'है हैं था थे थी हो हूँ हुआ हुए हुई नहीं करता करते करती कहते कहता कहा जाता जाते जाती '
    'होता होते होती चाहिये चाहिए सकता सकते सकती वाला वाले वाली गया गये गयी और भी तो यह ये '
    'क्योंकि किंतु परंतु इसलिये इसलिए उनके उनका उनकी उसके उसका उसकी इसके इसका इसकी अपने अपना अपनी '
    'मेरे तेरे द्वारा तरह लिये लिए रहेंगे करूँगा जायँगे दीखती देखा जब तब कोई'.split())
SA_STRONG = set(
    'इति एव हि तु स्यात् भवति उच्यते यत् तत् यस्मात् तस्मात् किम् अत्र आह चेत् अपि च वा '
    'ते सः अयं इदं एतत् तस्य यस्य तेषां श्रुतेः स्मृतेः'.split())
HI_END = ('के', 'की', 'को', 'में', 'से', 'ने', 'पर', 'वाले', 'वाली', 'ोंके', 'ोंकी', 'ोंको', 'ोंमें', 'ोंसे')

ASCII_DIGITS = str.maketrans('0123456789', '०१२३४५६७८९')


def hindi_sanskrit_score(line):
    h = sa = 0
    for w in TOKEN.findall(line):
        if w in HI_STRONG:
            h += 2
        elif w in SA_STRONG:
            sa += 1
        elif w.endswith('ः') or (w + ':') in line or w.endswith('म्'):
            sa += 1
        elif len(w) > 3 and w.endswith(HI_END):
            h += 1
    return h, sa


def split_mixed(line):
    """Split a merged two-column line into (sanskrit_left, hindi_right)."""
    if '|' in line:
        left, _, right = line.partition('|')
        return left.strip(), right.strip()
    # find first strong-Hindi token; everything from there is the Hindi column
    for m in TOKEN.finditer(line):
        w = m.group(0)
        if w in HI_STRONG or (len(w) > 3 and w.endswith(HI_END)):
            return line[:m.start()].strip(), line[m.start():].strip()
    return line.strip(), ''


def extract_hindi_stream(text):
    """Return list of (kind, value): kind 'txt' Hindi text piece or 'par' break."""
    text = text.replace('‌', '').replace('‍', '')
    lines = [l.rstrip() for l in text.split('\n')]
    stream = []          # Hindi pieces in order
    pending_gap = False  # blank gap since last Hindi piece
    prev_class = 'S'
    for raw in lines:
        s = raw.strip()
        if not s:
            pending_gap = True
            continue
        if HDR.search(s) or PAGENUM.match(s):
            continue
        h, sa = hindi_sanskrit_score(s)
        if '|' in s or (h >= 2 and sa >= 2):
            cls = 'M'
        elif h > sa:
            cls = 'H'
        elif sa > h:
            cls = 'S'
        else:
            toks = TOKEN.findall(s)
            if toks and max(len(w) for w in toks) >= 11:
                cls = 'S'  # long sandhi compound: Sanskrit column
            else:
                cls = prev_class  # ambiguous: continue current column strip
        if cls == 'M':
            _, right = split_mixed(s)
            if right:
                stream.append((pending_gap, right))
            cls = 'H'  # merged line means we are inside a Hindi strip region
        elif cls == 'H':
            stream.append((pending_gap, s))
        prev_class = cls
        pending_gap = False
    return stream


def assemble(stream):
    """Join Hindi pieces; paragraph break when a gap follows sentence end."""
    out = ''
    for gap, piece in stream:
        if not out:
            out = piece
            continue
        if gap and out.rstrip().endswith(('।', '॥', '?', '!')):
            out = out.rstrip() + '\n' + piece
        elif out.endswith('-'):
            out = out[:-1] + piece
        else:
            out += ' ' + piece
    return out


DEV_NUM = dict(zip('०१२३४५६७८९', range(10)))


def dev_to_int(s):
    n = 0
    for ch in s:
        n = n * 10 + DEV_NUM[ch]
    return n


def segment_by_verse(text, max_verse):
    """Split assembled Hindi text on ॥n॥ markers into {verse: text}."""
    segs = {}
    pos = 0
    prev = 0
    for m in MARKER.finditer(text):
        n = dev_to_int(m.group(1))
        if prev < n <= prev + 4 and n <= max_verse:
            seg = text[pos:m.end()].strip()
            if seg:
                segs[n] = (segs.get(n, '') + '\n' + seg).strip()
            pos = m.end()
            prev = n
        # else: stray number (quote reference etc.) - ignore, keep accumulating
    tail = text[pos:].strip()
    if tail and prev + 1 <= max_verse:
        segs[prev + 1] = tail
    return segs


FIXES = [
    ('--', '—'),
    (' ।', '।'),
    ('। ॥', '॥'),
    ('।।', '॥'),
    ('॑', ''),
    ('ऊ', 'ऊ'),
    # curated OCR corrections (verified against Gita Press readings)
    ('द्ठारा', 'द्वारा'),
    ('द्ठाा', 'द्वारा'),
    ('द्वाए ', 'द्वारा '),
    ('श्रेष्ठठटर', 'श्रेष्ठतर'),
    ('श्रेष्ठटर', 'श्रेष्ठतर'),
    ('आतमज्ञ', 'आत्मज्ञ'),
    ('प्रवत्त', 'प्रवृत्त'),
    ('आशछ्डा', 'आशङ्का'),
    ('आशड्डा', 'आशङ्का'),
    ('आशड्ढा', 'आशङ्का'),
    ('शड्डा', 'शङ्का'),
    ('सड़्ग्राम', 'सङ्ग्राम'),
    ('सड़ग्राम', 'सङ्ग्राम'),
    ('सड्ग्राम', 'सङ्ग्राम'),
    ('सड़्ख्य', 'सङ्ख्य'),
    ('सड्ख्य', 'सङ्ख्य'),
    ('सुहृदू', 'सुहृद्'),
    ('श्लोकद्ठारा', 'श्लोकद्वारा'),
    ('ऊ्', '्'),
    ('ू् ', '् '),
    ('पू०-:', 'पू०—'),
    ('इत्यादिना', 'इत्यादिना'),
]

RE_FIXES = [
    (re.compile(r'अग्रि(?!म)'), 'अग्नि'),
    (re.compile(r'(?<=[क-ह])ृ्'), '्'),
]


def clean(text):
    text = text.translate(ASCII_DIGITS)
    # ASCII colon straight after a Devanagari letter is a visarga
    text = re.sub(r'(?<=[अ-ह़ािीुूृेैोौंँॅ])\s?:', 'ः', text)
    text = re.sub(r'[A-Za-z]+', '', text)
    text = re.sub(r'[*_»«=~^<>+|#&%"/\\{}]+', '', text)
    text = re.sub(r'(?<=[ऀ-ॿ]):', 'ः', text)
    text = text.replace(':', '')
    for a, b in FIXES:
        text = text.replace(a, b)
    for rx, b in RE_FIXES:
        text = rx.sub(b, text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r' +\n', '\n', text)
    text = re.sub(r'\n{2,}', '\n', text)
    return text.strip()


def main():
    gita = json.load(open(REPO / 'data' / 'gita.json'))
    verses_per_ch = {}
    for v in gita['data']:
        if not str(v.get('n', '')).isdigit():
            continue
        c = int(v['c'])
        verses_per_ch[c] = max(verses_per_ch.get(c, 0), int(v['n']))

    result = {}
    for f in sorted(DATASET.glob('*.json')):
        d = json.load(open(f))
        ch = d['chapter_number']
        if ch < 2:  # ch0 = upodghata, ch1 = shloka+arth only (no bhashya)
            continue
        stream = extract_hindi_stream(d['text'])
        text = assemble(stream)
        segs = segment_by_verse(text, verses_per_ch[ch])
        result[str(ch)] = {str(n): clean(t) for n, t in sorted(segs.items())}
        exp = verses_per_ch[ch]
        got = len(segs)
        chars = sum(len(t) for t in segs.values())
        print(f'ch{ch:2d}: {got}/{exp} verses, {chars} chars')

    out = REPO / 'data' / 'shankarbhashya.json'
    json.dump(result, open(out, 'w'), ensure_ascii=False, indent=1)
    print('wrote', out)


if __name__ == '__main__':
    main()
