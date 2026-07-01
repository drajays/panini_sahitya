#!/usr/bin/env python3
"""Generate best-effort grammar analysis for Srimad Bhagavatam verses using
vidyut.kosha (surface-word dictionary lookup). Output: one JSON per skandha,
keyed by "c|n" -> list of rows. Rows are minimal (empty fields omitted)."""
import json, re, os, time, sys
from vidyut.kosha import Kosha
from vidyut.lipi import transliterate, Scheme

D, S = Scheme.Devanagari, Scheme.Slp1
DATA = os.path.join(os.path.dirname(__file__), '..')
ROOT = '/Users/dr.ajayshukla/Panini_sahitya'
k = Kosha(os.path.join(ROOT, '.venv/vidyut-data/kosha'))

def dv(x): return transliterate(x or '', S, D)
def slp(x): return transliterate(x, D, S)

VIB = {'praTamA':('प्रथमा','कर्ता'),'dvitIyA':('द्वितीया','कर्म'),'tftIyA':('तृतीया','करण'),
       'caturTI':('चतुर्थी','सम्प्रदान'),'paYcamI':('पञ्चमी','अपादान'),'zazWI':('षष्ठी','सम्बन्ध'),
       'saptamI':('सप्तमी','अधिकरण'),'samboDanam':('सम्बोधन','सम्बोधन')}
VAC = {'eka':'एकवचन','dvi':'द्विवचन','bahu':'बहुवचन'}
LIN = {'puM':'पुंल्लिङ्ग','strI':'स्त्रीलिङ्ग','napuMsaka':'नपुंसकलिङ्ग','napuMsakam':'नपुंसकलिङ्ग'}
PUR = {'praTama':'प्रथम','maDyama':'मध्यम','uttama':'उत्तम'}
LAK = {'la~w':'लट्','li~w':'लिट्','lu~w':'लुट्','lf~w':'लृट्','le~w':'लेट्','lo~w':'लोट्',
       'la~N':'लङ्','ASIrli~N':'आशीर्लिङ्','viDili~N':'विधिलिङ्','lu~N':'लुङ्','lf~N':'लृङ्'}

def is_sub(t): return type(t).__name__.endswith('Subanta')
def is_tin(t): return type(t).__name__.endswith('Tinanta')

def lookup(w):
    key = slp(w)
    cands = [key]
    if key.endswith('H'): cands += [key[:-1]+'s', key[:-1]+'r', key[:-1]]
    if key.endswith('M'): cands += [key[:-1]+'m']
    seen = set()
    for cd in cands:
        if cd in seen: continue
        seen.add(cd)
        try: entries = k.get(cd)
        except Exception: entries = []
        if not entries: continue
        # deprioritise spurious sambodhana readings
        non_sam = [e for e in entries if not (is_sub(e) and str(e.vibhakti) == 'samboDanam')]
        return (non_sam or entries)[0]
    return None

def row_for(w):
    t = lookup(w)
    r = {'w': w}
    if t is None: return r
    try:
        if t.is_avyaya:
            r['g'] = 'अव्यय'; r['m'] = dv(t.lemma)
        elif is_tin(t):
            r['m'] = dv(t.lemma)
            lak = LAK.get(str(t.lakara), dv(str(t.lakara)))
            pur = PUR.get(str(t.purusha), '')
            vac = VAC.get(str(t.vacana), '')
            r['g'] = ' · '.join(x for x in [lak, pur+' पुरुष' if pur else '', vac] if x)
            try:
                pref = list(t.dhatu_entry.dhatu.prefixes)
                if pref: r['u'] = ' + '.join(dv(p) for p in pref)
            except Exception: pass
        elif is_sub(t):
            r['m'] = dv(t.lemma)
            vib, kar = VIB.get(str(t.vibhakti), (dv(str(t.vibhakti)), ''))
            vac = VAC.get(str(t.vacana), '')
            r['g'] = ' · '.join(x for x in [vib, vac] if x)
            if kar: r['k'] = kar
            lin = LIN.get(str(t.linga), '')
            if lin: r['l'] = lin
    except Exception:
        pass
    return r

def main():
    bhag = json.load(open(os.path.join(ROOT, 'data/bhagavatam.json')))
    outdir = os.path.join(ROOT, 'data/bhagavatam-analysis')
    os.makedirs(outdir, exist_ok=True)
    by_sk = {}
    t0 = time.time(); n = 0; resolved = 0; total = 0
    for e in bhag['data']:
        if not (e.get('v') and e.get('n') is not None): continue
        c = e['c']; sk = str(c).split('.')[0]
        words = [w for w in re.sub(r'[।॥]', ' ', e['v']).split() if w.strip()]
        rows = [row_for(w) for w in words]
        for r in rows:
            total += 1
            if len(r) > 1: resolved += 1
        by_sk.setdefault(sk, {})[f"{c}|{e['n']}"] = rows
        n += 1
        if n % 1000 == 0:
            print(f'  {n} verses… ({time.time()-t0:.0f}s)', flush=True)
    for sk, obj in by_sk.items():
        with open(os.path.join(outdir, f'skandha-{sk}.json'), 'w', encoding='utf-8') as f:
            json.dump(obj, f, ensure_ascii=False, separators=(',', ':'))
    print(f'DONE: {n} verses, {len(by_sk)} skandhas in {time.time()-t0:.0f}s')
    print(f'Resolution: {resolved}/{total} = {100*resolved/total:.0f}% words got grammar')

if __name__ == '__main__':
    main()
