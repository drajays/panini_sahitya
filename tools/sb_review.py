#!/usr/bin/env python3
"""Review helper for proofreading: dump verse seams and suspicious tokens."""
import json
import re
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sb = json.load(open(REPO / 'data' / 'shankarbhashya.json'))

ch = sys.argv[1]
mode = sys.argv[2] if len(sys.argv) > 2 else 'seams'

if mode == 'seams':
    for n, t in sorted(sb[ch].items(), key=lambda kv: int(kv[0])):
        t1 = t.replace('\n', ' ')
        head, tail = t1[:150], t1[-150:]
        print(f'--- {ch}.{n} ({len(t)} chars)')
        print('  A:', head)
        print('  Z:', tail)
elif mode == 'tokens':
    # corpus token frequencies
    freq = Counter()
    for vs in sb.values():
        for t in vs.values():
            freq.update(re.findall(r'[ऀ-ॿ]+', t))
    # rare bigrams learned from corpus
    big = Counter()
    for w, c in freq.items():
        for i in range(len(w) - 1):
            big[w[i:i+2]] += c
    text = '\n'.join(t for t in sb[ch].values())
    seen = set()
    for n, t in sorted(sb[ch].items(), key=lambda kv: int(kv[0])):
        for m in re.finditer(r'[ऀ-ॿ]+', t):
            w = m.group(0)
            if w in seen or len(w) < 3 or freq[w] > 2:
                continue
            score = min(big[w[i:i+2]] for i in range(len(w) - 1))
            if score < 25:  # contains a corpus-rare bigram
                seen.add(w)
                c0 = t[max(0, m.start()-30):m.end()+30].replace('\n', ' ')
                print(f'{ch}.{n} [{w}] …{c0}…')
elif mode == 'verse':
    print(sb[ch][sys.argv[3]])
