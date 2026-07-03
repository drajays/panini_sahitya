import re

djvu_path = '/Users/dr.ajayshukla/Downloads/Shri Ramcharitmanas - Gita Press (Hindi)_djvu.txt'
with open(djvu_path, 'r', encoding='utf-8') as f:
    text = f.read()

kanda_names = [
    'बालकाण्ड', 'अयोध्याकाण्ड', 'अरण्यकाण्ड', 'किष्किन्धाकाण्ड',
    'सुन्दरकाण्ड', 'लंकाकाण्ड', 'उत्तरकाण्ड'
]

# Let's search for "प्रथम सोपान", "द्वितीय सोपान", etc.
for match in re.finditer(r'(प्रथम|द्वितीय|तृतीय|चतुर्थ|पंचम|षष्ठ|सप्तम)\s+सोपान', text):
    start = match.start()
    print(f"Found {match.group(0)} at {start}")
    print(text[start:start+100])
