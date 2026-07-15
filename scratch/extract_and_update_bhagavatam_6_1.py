#!/usr/bin/env python3
import json
import re
import os

ROOT = '/Users/dr.ajayshukla/Panini_sahitya'
HTML_PATH = '/Users/dr.ajayshukla/bhagavat_6_1_shabdarth (3).html'
BHAG_JSON = os.path.join(ROOT, 'data/bhagavatam.json')
SKANDHA_6_JSON = os.path.join(ROOT, 'data/bhagavatam-analysis/skandha-6.json')

VIB_MAP = {
    'प्रथमा': '1',
    'द्वितीया': '2',
    'तृतीया': '3',
    'चतुर्थी': '4',
    'पञ्चमी': '5',
    'षष्ठी': '6',
    'सप्तमी': '7',
    'सम्बोधन': '8',
}
VAC_MAP = {'एक.': '1', 'द्वि.': '2', 'बहु.': '3', 'एकवचन': '1', 'द्विवचन': '2', 'बहुवचन': '3'}

def map_cn(vib, vac):
    vib_clean = vib.strip()
    vac_clean = vac.strip()
    if vib_clean in VIB_MAP and vac_clean in VAC_MAP:
        return f"{VIB_MAP[vib_clean]}.{VAC_MAP[vac_clean]}"
    return None

def main():
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html_text = f.read()

    # Extract essay
    essay_match = re.search(r'<div class="essay" id="samagra-vishleshan">(.*?)</div>\s*(?=<div class="card"|$)', html_text, re.DOTALL)
    essay_html = essay_match.group(1).strip() if essay_match else ''

    # Extract all cards
    cards = re.findall(r'<div class="card" id="v(\d+)">(.*?)</div>\s*(?=<div class="card"|<div class="footer"|$)', html_text, re.DOTALL)
    print(f"Extracted {len(cards)} verse cards from HTML.")

    with open(BHAG_JSON, 'r', encoding='utf-8') as f:
        bhag = json.load(f)

    with open(SKANDHA_6_JSON, 'r', encoding='utf-8') as f:
        sk6 = json.load(f)

    # Attach essay to chapter 6.1
    for ch in bhag.get('chapters', []):
        if str(ch.get('number')) == '6.1':
            ch['essay'] = essay_html
            print("Attached essay to chapter 6.1 entry.")

    bhag_data_map = {}
    for entry in bhag.get('data', []):
        if entry.get('c') == '6.1' and entry.get('n') is not None:
            bhag_data_map[str(entry.get('n'))] = entry

    updated_count = 0
    for num_str, ctext in cards:
        # parse anvay/bhavarth
        anv_match = re.search(r'<div class="anv">(.*?)</div>', ctext, re.DOTALL)
        anv_text = re.sub(r'<.*?>', '', anv_match.group(1)).replace('अन्वय-भावार्थ:', '').strip() if anv_match else ''

        # parse table
        rows = []
        tbody_match = re.search(r'<tbody>(.*?)</tbody>', ctext, re.DOTALL)
        if tbody_match:
            trs = re.findall(r'<tr>(.*?)</tr>', tbody_match.group(1), re.DOTALL)
            for tr in trs:
                tds = re.findall(r'<td>(.*?)</td>', tr, re.DOTALL)
                if len(tds) >= 6:
                    clean_tds = [re.sub(r'<.*?>', '', td).strip() for td in tds[:6]]
                    rows.append({
                        'pad': clean_tds[0],
                        'arth': clean_tds[1],
                        'vibhakti': clean_tds[2],
                        'vachan': clean_tds[3],
                        'pratyaya': clean_tds[4],
                        'prakriti': clean_tds[5]
                    })

        if not rows:
            print(f"Warning: No table rows extracted for verse {num_str}")
            continue

        # Build padaccheda string
        anv_str = ' । '.join([r['pad'] for r in rows]) + ' ॥'

        # Build pc array and sk_rows array
        pc_list = []
        sk_rows = []
        for r in rows:
            pad = r['pad']
            arth = r['arth'] if r['arth'] != '—' else ''
            vib = r['vibhakti']
            vac = r['vachan']
            pra = r['pratyaya'] if r['pratyaya'] != '—' else ''
            prak = r['prakriti'] if r['prakriti'] != '—' else ''

            gram = vib
            if vac != '—' and vac != '':
                gram += ' · ' + vac

            cn_code = map_cn(vib, vac)

            # Build part object
            part = {'l': prak if prak else pad}
            if cn_code:
                part['cn'] = cn_code
            if pra:
                part['s'] = [pra]

            pc_item = {
                'w': pad,
                'e': arth,
                'g': gram,
                'm': prak,
                'p': [part]
            }
            if pra:
                pc_item['s'] = [pra]
            if prak:
                pc_item['k'] = prak

            pc_list.append(pc_item)

            sk_row = {
                'w': pad,
                'm': prak,
                'g': gram,
                'e': arth
            }
            if pra:
                sk_row['s'] = pra
            if prak:
                sk_row['k'] = prak
            sk_rows.append(sk_row)

        if num_str in bhag_data_map:
            entry = bhag_data_map[num_str]
            entry['hs'] = anv_text
            entry['anv'] = anv_str
            entry['pc'] = pc_list
            updated_count += 1

        # Update skandha-6.json
        sk6[f"6.1|{num_str}"] = sk_rows

    with open(BHAG_JSON, 'w', encoding='utf-8') as f:
        json.dump(bhag, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Saved {BHAG_JSON} ({updated_count} verses updated with full analysis).")

    with open(SKANDHA_6_JSON, 'w', encoding='utf-8') as f:
        json.dump(sk6, f, ensure_ascii=False, separators=(',', ':'))
    print(f"Saved {SKANDHA_6_JSON}.")

if __name__ == '__main__':
    main()
