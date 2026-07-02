import os
import json

def build_chalisa_json():
    source_dir = "/Users/dr.ajayshukla/Downloads/hanumanchalisha/devnagari_dataset"
    index_path = os.path.join(source_dir, "index.json")
    
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"Index file not found: {index_path}")
        
    with open(index_path, "r", encoding="utf-8") as f:
        index_data = json.load(f)
        
    data_entries = []
    
    for idx, v_info in enumerate(index_data["verses"], 1):
        if idx == 1:
            data_entries.append({"c": "1", "t": "॥ प्रारंभिक दोहे ॥"})
        elif idx == 3:
            data_entries.append({"c": "1", "t": "॥ चौपाई ॥"})
        elif idx == 43:
            data_entries.append({"c": "1", "t": "॥ समापन दोहा ॥"})
            
        file_path = os.path.join(source_dir, "json", f"{v_info['id']}.json")
        with open(file_path, "r", encoding="utf-8") as f:
            v_data = json.load(f)
            
        text = v_data.get("text", "")
        saral_arth = v_data.get("saral_arth", "")
        
        vyakhya_list = v_data.get("vistrit_vyakhya", [])
        vyakhya = "\n\n".join(vyakhya_list) if vyakhya_list else ""
        
        prashnottar = v_data.get("prashnottar", [])
        qa_list = [
            {"q": item.get("prashna", ""), "a": item.get("uttar", "")}
            for item in prashnottar
            if item.get("prashna")
        ]
        
        entry = {
            "c": "1",
            "n": str(idx),
            "i": idx,
            "title": v_data.get("title", ""),
            "v": text,
            "ch": {"n": v_data.get("type", "पद")},
            "hs": saral_arth,
            "sb": vyakhya,
            "qa": qa_list
        }
        data_entries.append(entry)
        
    output_json = {
        "title": "श्री हनुमान चालीसा",
        "terms": {
            "chapterSg": "पाठ",
            "verseSg": "पद",
            "bookSg": "भाग"
        },
        "custom": {
            "hs": {"name": "सरल अर्थ / व्याख्या", "lang": "hi", "order": 1, "showInline": True},
            "sb": {"name": "विस्तृत आध्यात्मिक एवं वैज्ञानिक व्याख्या", "lang": "hi", "order": 2, "showInline": True},
            "qa": {"name": "प्रश्नोत्तर", "lang": "hi", "order": 3, "showInline": True}
        },
        "chapters": [
            {
                "number": "1",
                "name": "श्री हनुमान चालीसा",
                "subtitle": "गोस्वामी तुलसीदास कृत श्री हनुमान चालीसा (४३ दोहे एवं चौपाइयाँ)",
                "es": "Shri Hanuman Chalisa composed by Goswami Tulsidas."
            }
        ],
        "data": data_entries
    }
    
    output_path = "/Users/dr.ajayshukla/Panini_sahitya/data/chalisa.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_json, f, ensure_ascii=False, indent=2)
        
    print(f"Successfully generated {output_path} with {len(data_entries)} data items ({len(index_data['verses'])} verses).")

if __name__ == "__main__":
    build_chalisa_json()
