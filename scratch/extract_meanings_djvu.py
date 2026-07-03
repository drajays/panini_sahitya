import json
import re
import html
import os

def clean_text(text):
    text = html.unescape(text)
    text = re.sub(r'^\d+\s*\*\s*रामचरितमानस\s*\*\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\*\s*.*?\s*\*\s*\d+\s*$', '', text, flags=re.MULTILINE)
    return text

def normalize(text):
    text = re.sub(r'[^\w\s]', '', text)
    return text.split()

def find_best_match(query, text_window):
    query_lines = [l.strip() for l in query.split('\n') if len(l.strip()) > 5]
    if not query_lines:
        return -1
        
    first_line = query_lines[0]
    query_words = normalize(first_line)
    text_words = normalize(text_window)
    
    if len(query_words) < 3:
        return -1
        
    target_len = min(6, len(query_words))
    target_words = query_words[:target_len]
    target_set = set(target_words)
    
    best_score = 0
    best_idx = -1
    
    for i in range(len(text_words) - target_len + 1):
        window_words = text_words[i:i+target_len]
        window_set = set(window_words)
        score = len(target_set & window_set)
        if score > best_score:
            best_score = score
            best_idx = i
            
    if best_score >= target_len * 0.5:
        word_iter = re.finditer(r'\b\w+\b', text_window)
        for i, m in enumerate(word_iter):
            if i == best_idx:
                return m.start()
                
    return -1

def extract():
    json_path = '/Users/dr.ajayshukla/Panini_sahitya/data/manas.json'
    raw_dir = '/Users/dr.ajayshukla/Panini_sahitya/data/raw_kandas'
    
    with open(json_path, 'r', encoding='utf-8') as f:
        manas = json.load(f)
        
    kaand_files = {
        '1': '1_बालकाण्ड.txt',
        '2': '2_अयोध्याकाण्ड.txt',
        '3': '3_अरण्यकाण्ड.txt',
        '4': '4_किष्किन्धाकाण्ड.txt',
        '5': '5_सुन्दरकाण्ड.txt',
        '6': '6_लंकाकाण्ड.txt',
        '7': '7_उत्तरकाण्ड.txt'
    }
    
    kaand_texts = {}
    for num, fname in kaand_files.items():
        with open(os.path.join(raw_dir, fname), 'r', encoding='utf-8') as f:
            kaand_texts[num] = clean_text(f.read())
            
    # Group verses by kaand
    verses_by_kaand = {str(i): [] for i in range(1, 8)}
    for i, item in enumerate(manas['data']):
        verses_by_kaand[str(item['c'])].append((i, item))
        
    extracted_count = 0
    
    for c_num, verses in verses_by_kaand.items():
        ocr_text = kaand_texts[c_num]
        current_idx = 0
        verse_positions = []
        
        print(f"Locating blocks in Kaanda {c_num}...")
        for i, item in verses:
            verse_text = item['v']
            verse_text_clean = re.sub(r'^\[.*?\]\n', '', verse_text)
            
            window = ocr_text[current_idx:current_idx + 30000]
            start = find_best_match(verse_text_clean, window)
            
            if start != -1:
                abs_start = current_idx + start
                verse_positions.append((i, abs_start))
                current_idx = abs_start + 10 
            else:
                current_idx += 50
                
        print(f"Total blocks found for Kaanda {c_num}: {len(verse_positions)} / {len(verses)}")
        
        for k in range(len(verse_positions) - 1):
            idx, pos = verse_positions[k]
            next_idx, next_pos = verse_positions[k+1]
            
            raw_meaning = ocr_text[pos:next_pos].strip()
            
            vtext = manas['data'][idx]['v']
            vlines = [l.strip() for l in vtext.split('\n') if len(l.strip()) > 3]
            
            meaning_lines = raw_meaning.split('\n')
            final_lines = []
            for mline in meaning_lines:
                mline_clean = mline.strip()
                is_verse = False
                mline_norm = normalize(mline_clean)
                if len(mline_norm) > 2:
                    for vline in vlines:
                        vnorm = normalize(vline)
                        if len(set(mline_norm) & set(vnorm)) >= len(mline_norm) * 0.8:
                            is_verse = True
                            break
                if not is_verse and mline_clean:
                    final_lines.append(mline_clean)
                    
            meaning_clean = '\n'.join(final_lines)
            if len(meaning_clean) > 10:
                manas['data'][idx]['hs'] = meaning_clean
                extracted_count += 1
                
    out_path = '/Users/dr.ajayshukla/Panini_sahitya/data/manas_with_arth.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manas, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully extracted meanings for {extracted_count} verses.")

if __name__ == '__main__':
    extract()
