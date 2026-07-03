import re
import os

djvu_path = '/Users/dr.ajayshukla/Downloads/Shri Ramcharitmanas - Gita Press (Hindi)_djvu.txt'
out_dir = '/Users/dr.ajayshukla/Panini_sahitya/data/raw_kandas'
os.makedirs(out_dir, exist_ok=True)

with open(djvu_path, 'r', encoding='utf-8') as f:
    text = f.read()

kanda_names = [
    'बालकाण्ड', 'अयोध्याकाण्ड', 'अरण्यकाण्ड', 'किष्किन्धाकाण्ड',
    'सुन्दरकाण्ड', 'लड्ढाकाण्ड', 'उत्तरकाण्ड'
]
actual_names = [
    'बालकाण्ड', 'अयोध्याकाण्ड', 'अरण्यकाण्ड', 'किष्किन्धाकाण्ड',
    'सुन्दरकाण्ड', 'लंकाकाण्ड', 'उत्तरकाण्ड'
]

positions = []
for i, name_pattern in enumerate(kanda_names):
    matches = list(re.finditer(name_pattern, text))
    best_pos = -1
    for m in matches:
        start = max(0, m.start() - 50)
        end = m.end() + 50
        context = text[start:end]
        if 'सोपान' in context or '_' in context or '>' in context:
            best_pos = m.start()
            break
    if best_pos == -1 and matches:
        best_pos = matches[0].start()
        
    positions.append((actual_names[i], best_pos))

positions.sort(key=lambda x: x[1])

for i in range(len(positions)):
    name, start = positions[i]
    end = positions[i+1][1] if i + 1 < len(positions) else len(text)
    
    kand_text = text[start:end]
    
    out_file = os.path.join(out_dir, f"{i+1}_{name}.txt")
    with open(out_file, 'w', encoding='utf-8') as f:
        f.write(kand_text)
        
    print(f"Saved {name} to {out_file} ({len(kand_text)} chars)")
