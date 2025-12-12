import cv2
import numpy as np
from pdf2image import convert_from_path
import easyocr
from rapidfuzz import fuzz
import re


def structured_parsing(text, header_list):
    # 1. Normalize text
    clean_text = text.replace('~', ' ').replace('\n', ' ')
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()

    found_matches = []

    # 2. Iterate through specific header list
    for header in header_list:
        parts = header.split()
        num = parts[0].replace('.', '')
        first_word = parts[1] if len(parts) > 1 else "" 
        
        # Fuzzy Regex: Match Number + First 3-4 chars of the title
        fuzzy_word = first_word[:4] 
        pattern = fr"({num})[\.\s\-\)]+({fuzzy_word}.*?)(?=\s)"
        
        match = re.search(pattern, clean_text, re.IGNORECASE)
        
        if match:
            found_matches.append({
                "original_header": header,
                "found_title": match.group(0),
                "start": match.start(),
                "end": match.end()
            })

    found_matches.sort(key=lambda x: x['start'])

    sections = []

    # Introduction
    if found_matches and found_matches[0]['start'] > 0:
        sections.append({
            "header": "GİRİŞ / ÖN BİLGİ",
            "content": clean_text[:found_matches[0]['start']].strip()
        })

    # Content Extraction
    for i, item in enumerate(found_matches):
        start_content = item['end']
        end_content = found_matches[i+1]['start'] if i + 1 < len(found_matches) else len(clean_text)
        content = clean_text[start_content:end_content].strip()
        
        sections.append({
            "header": item['original_header'],
            "content": content
        })

    return sections

def special_logic(header, content):
    content = content.strip()
    # Remove leading punctuation often found in OCR (e.g. ": 5 Atasehir")
    clean_content = content.lstrip(" :.,;-")
    
    # Get the section number (e.g., "8" from "8. Temsil")
    section_num = header.split('.')[0]

    # --- CONDITION 1: AMAÇ (Uppercase Only) ---
    if "amaç" in header.lower():
        # Find all Uppercase words (len > 2)
        caps = re.findall(r'\b[A-ZÇĞİÖŞÜ]{3,}\b', content)
        # Filter stop words
        excludes = ["VE", "VEYA", "ILE", "ANCAK", "SİRKET", "YAPMAK", "ETMEK", "SATMAK"]
        filtered = [w for w in caps if w not in excludes]
        # Unique values preserving order
        seen = set()
        unique = [x for x in filtered if not (x in seen or seen.add(x))]
        return ", ".join(unique)

    # --- CONDITION 2: 8, 9, 10, 14 (First Sentence Only) ---
    elif section_num in ["8", "9", "10", "14"]:
        # Split by dot and take the first part
        first_sentence = clean_content.split('.')[0]
        return first_sentence + "."

    # --- CONDITION 3: ELSE (Whole Content) ---
    else:
        return clean_content


class TOBBOCR:
    def __init__(self, dpi=200, gpu=True):
        self.dpi = dpi
        self.reader = easyocr.Reader(['tr', 'en'], gpu=gpu)

    def tr_upper(self, text):
        return text.replace('i', 'İ').upper()

    def find_red_titles(self, img_col):
        """Finds red boxes to identify company headers."""
        hsv = cv2.cvtColor(img_col, cv2.COLOR_BGR2HSV)
        mask1 = cv2.inRange(hsv, np.array([0, 70, 50]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 70, 50]), np.array([180, 255, 255]))
        mask = cv2.bitwise_or(mask1, mask2)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (20, 3))
        mask = cv2.dilate(mask, kernel, iterations=1)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        boxes = []
        for c in contours:
            if cv2.contourArea(c) > 300:
                x, y, w, h = cv2.boundingRect(c)
                boxes.append((x, y, w, h))
        return sorted(boxes, key=lambda b: b[1])



    def summarize_kurulus(self, text):
        # --- EXECUTION ---

        possible_headers = [
            "1. Kuruluş", "2. Şirket Unvanı", "3. Amaç ve Konu", "4. Şirketin Merkezi",
            "5. Süre", "6. Sermaye", "7. Şirketin İdaresi", "8. Temsil", "9. Genel Kurul",
            "10. İlan", "11. Hesap Dönemi", "12. Karın Tespiti ve Dağıtımı", "13. Yedek Akçe", "14. Kanuni Hükümler"
        ]

        parsed_data = structured_parsing(text, possible_headers)

        summarized = []
        for section in parsed_data:
            final_text = special_logic(section['header'], section['content'])
            summarized.append({
                "header": section['header'],
                "content": final_text
            })

        return summarized
    # ---------------------------------------------------------
    # NEW: CONTINUOUS DOCUMENT STREAM PROCESSING
    # ---------------------------------------------------------
    def run(self, pdf_path, section_type, target_company):
        print(f"--- Scanning Document Stream: {pdf_path} ---")
        pages = convert_from_path(pdf_path, dpi=self.dpi)
        
        # Flatten columns
        column_stream = []
        for idx, page in enumerate(pages):
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            h, w, _ = img.shape
            column_stream.append((img[:, 0:w//2], idx+1, "LEFT"))
            column_stream.append((img[:, w//2:], idx+1, "RIGHT"))

        is_collecting = False
        buffer_text = []
        STOP_PHRASES = ["TİCARET SİCİLİ MÜDÜRLÜĞÜ", "İLAN SIRA NO"]
        found_results = []

        for col_img, page_num, col_name in column_stream:
            # Always scan the whole column
            raw_lines = self.reader.readtext(col_img, detail=0)
            
            for line in raw_lines:
                line_up = self.tr_upper(line)
                
                # --- PHASE 1: SEARCH FOR TITLE ---
                if not is_collecting:
                    if fuzz.partial_ratio(self.tr_upper(target_company), line_up) > 85:
                        print(f"Match Found on Page {page_num} ({col_name}): {line}")
                        is_collecting = True  # Start collecting from here
                
                # --- PHASE 2: COLLECT TEXT ---
                if is_collecting:
                    # Check for stop phrases
                    if any(stop in line_up for stop in STOP_PHRASES) and len(line) < 100:
                        print(f"   -> End detected: {line}")
                        is_collecting = False
                        
                        # Process collected text
                        full_text = " ".join(buffer_text)
                        extracted = self.extract_and_summarize(full_text, section_type)
                        if extracted:
                            found_results.append(extracted)
                        
                        buffer_text = []  # Reset buffer
                        continue
                    
                    # Add line to buffer
                    buffer_text.append(line)

        # --- End of document check ---
        if is_collecting and buffer_text:
            print("   -> End of Document reached.")
            full_text = " ".join(buffer_text)
            extracted = self.extract_and_summarize(full_text, section_type)
            if extracted:
                found_results.append(extracted)

        return found_results



    def extract_and_summarize(self, full_text, section_type):

        text_up = self.tr_upper(full_text)
        
        if section_type == "KURULUS":
            return self.summarize_kurulus(full_text)
        else:
            return full_text
        




# --- EXECUTION ---
if __name__ == "__main__":
    ocr = TOBBOCR(dpi=200)

    # Example: Sermaye
    results = ocr.run("TOBBPDF/k.pdf", "KURULUS", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS ===")
    for r in results:
        print(r)
        print("-" * 30)

    results = ocr.run("TOBBPDF/r2.pdf", "SERMAYE", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS ===")
    for r in results:
        print(r)
        print("-" * 30)
    results = ocr.run("TOBBPDF/p.pdf", "PAY", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS ===")
    for r in results:
        print(r)
        print("-" * 30)