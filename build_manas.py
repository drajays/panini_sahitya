import os
import json

def build_manas():
    src_dir = '/Users/dr.ajayshukla/Downloads/sanskrit_text_gitasupersite-master/ramcharitmanas'
    
    kandas = [
        ('1', 'baal_kaanda', 'बालकाण्ड', 'श्री राम जन्मोत्सव, विश्वामित्र यज्ञ रक्षा एवं सीता स्वयंवर (३६२ दोहे)'),
        ('2', 'ayodhya_kaanda', 'अयोध्याकाण्ड', 'श्री राम राज्याभिषेक तैयारी, वनवास एवं भरत मिलाप (३२७ दोहे)'),
        ('3', 'aranya_kaanda', 'अरण्यकाण्ड', 'पंचवटी निवास, शूर्पणखा प्रसंग, सीता हरण एवं शबरी अनुग्रह (४७ दोहे)'),
        ('4', 'kishkindha_kaanda', 'किष्किन्धाकाण्ड', 'हनुमान मिलन, सुग्रीव मैत्री, बालि वध एवं सीता खोज (३१ दोहे)'),
        ('5', 'sundara_kaanda', 'सुन्दरकाण्ड', 'हनुमान जी की लंका यात्रा, सीता आश्वासन, लंका दहन एवं विभीषण शरणागति (६१ दोहे)'),
        ('6', 'lanka_kaanda', 'लंकाकाण्ड', 'राम-रावण युद्ध, कुम्भकर्ण व मेघनाद वध एवं रावण संहार (१२२ दोहे)'),
        ('7', 'uttara_kaanda', 'उत्तरकाण्ड', 'श्री राम राज्याभिषेक, राम राज्य, काकभुशुण्डि-गरुड़ संवाद एवं रामगीता (१३१ दोहे)')
    ]
    
    chapters = []
    data = []
    
    for num, folder, name, subtitle in kandas:
        chapters.append({
            "number": num,
            "name": name,
            "subtitle": subtitle
        })
        
        c_path = os.path.join(src_dir, folder, 'chopayi.txt')
        d_path = os.path.join(src_dir, folder, 'doha.txt')
        
        c_list = open(c_path, encoding='utf-8').read().split('--x--') if os.path.exists(c_path) else []
        d_list = open(d_path, encoding='utf-8').read().split('--x--') if os.path.exists(d_path) else []
        
        n_blocks = max(len(c_list), len(d_list))
        for i in range(n_blocks):
            chop = c_list[i].strip() if i < len(c_list) else ""
            doh = d_list[i].strip() if i < len(d_list) else ""
            if not chop and not doh:
                continue
            comb = f"{chop}\n\n{doh}" if chop and doh else (chop or doh)
            data.append({
                "c": num,
                "n": str(i + 1),
                "v": comb
            })
            
    manas_json = {
        "title": "श्री रामचरितमानस",
        "terms": {
            "chapterSg": "काण्ड",
            "verseSg": "दोहा/चौपाई",
            "bookSg": "भाग"
        },
        "custom": {
            "hs": {"name": "सरल अर्थ / भावार्थ", "lang": "hi", "order": 1, "showInline": True},
            "sb": {"name": "विस्तृत आध्यात्मिक एवं दार्शनिक व्याख्या", "lang": "hi", "order": 2, "showInline": True},
            "qa": {"name": "प्रश्नोत्तर", "lang": "hi", "order": 3, "showInline": True}
        },
        "chapters": chapters,
        "data": data
    }
    
    out_path = '/Users/dr.ajayshukla/Panini_sahitya/data/manas.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manas_json, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {out_path} with {len(chapters)} kandas and {len(data)} total sections.")

if __name__ == '__main__':
    build_manas()
