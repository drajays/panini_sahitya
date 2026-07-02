import os
import json

def build_manas():
    src_dir = '/Users/dr.ajayshukla/Downloads/DharmicData-main/Ramcharitmanas'
    
    kandas = [
        ('1', '1_बाल_काण्ड_data.json', 'बालकाण्ड', 'श्री राम जन्मोत्सव, विश्वामित्र यज्ञ रक्षा एवं सीता स्वयंवर (३६२ दोहे)'),
        ('2', '2_अयोध्या_काण्ड_data.json', 'अयोध्याकाण्ड', 'श्री राम राज्याभिषेक तैयारी, वनवास एवं भरत मिलाप (३२७ दोहे)'),
        ('3', '3_अरण्य_काण्ड_data.json', 'अरण्यकाण्ड', 'पंचवटी निवास, शूर्पणखा प्रसंग, सीता हरण एवं शबरी अनुग्रह (४७ दोहे)'),
        ('4', '4_किष्किन्धा_काण्ड_data.json', 'किष्किन्धाकाण्ड', 'हनुमान मिलन, सुग्रीव मैत्री, बालि वध एवं सीता खोज (३१ दोहे)'),
        ('5', '5_सुंदर_काण्ड_data.json', 'सुन्दरकाण्ड', 'हनुमान जी की लंका यात्रा, सीता आश्वासन, लंका दहन एवं विभीषण शरणागति (६१ दोहे)'),
        ('6', '6_लंका_काण्ड_data.json', 'लंकाकाण्ड', 'राम-रावण युद्ध, कुम्भकर्ण व मेघनाद वध एवं रावण संहार (१२२ दोहे)'),
        ('7', '7_उत्तर_काण्ड_data.json', 'उत्तरकाण्ड', 'श्री राम राज्याभिषेक, राम राज्य, काकभुशुण्डि-गरुड़ संवाद एवं रामगीता (१३१ दोहे)')
    ]
    
    chapters = []
    data = []
    
    for num, filename, name, subtitle in kandas:
        chapters.append({
            "number": num,
            "name": name,
            "subtitle": subtitle
        })
        
        file_path = os.path.join(src_dir, filename)
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                kand_data = json.load(f)
                
            for i, item in enumerate(kand_data):
                v_type = item.get("type", "")
                content = item.get("content", "").strip()
                if not content:
                    continue
                
                comb = f"[{v_type}]\n{content}" if v_type else content
                
                data.append({
                    "c": num,
                    "n": str(i + 1),
                    "v": comb
                })
        else:
            print(f"Warning: {file_path} not found.")
            
    manas_json = {
        "title": "श्री रामचरितमानस",
        "terms": {
            "chapterSg": "काण्ड",
            "verseSg": "छंद/दोहा/चौपाई",
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
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(manas_json, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {out_path} with {len(chapters)} kandas and {len(data)} total sections.")

if __name__ == '__main__':
    build_manas()
