import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import cv2
import numpy as np
from pdf2image import convert_from_path
from doctr.models import ocr_predictor
import torch
from rapidfuzz import fuzz
import re
import json




# ---------------------------------------------------------
# TOBBOCR CLASS USING DOCTR
# ---------------------------------------------------------
class TOBBOCR:
    def __init__(self, dpi=200, gpu=True):
        self.dpi = dpi
        self.device = "cuda" if gpu and torch.cuda.is_available() else "cpu"
        print(f"🧠 Initializing Doctr OCR on {self.device.upper()}...")
        self.reader = ocr_predictor(pretrained=True, detect_language=True).to(self.device)

    def tr_upper(self, text):
        return text.replace('i', 'İ').upper()

    def find_red_titles(self, img_col):
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

    def ocr_column(self, img_col):
        img_rgb = cv2.cvtColor(img_col, cv2.COLOR_BGR2RGB)
        result = self.reader([img_rgb])
        json_output = result.export()
        all_text = []
        
        for page in json_output["pages"]:
            for block in page["blocks"]:
                for line in block["lines"]:
                    line_text = " ".join([w["value"].replace(" ", "") for w in line["words"]])
                    all_text.append(line_text)
        plain_text = "\n".join(all_text)
        print(plain_text)
        return re.sub(r'\s{2,}', ' ', plain_text).strip()



    def run(self, pdf_path, section_type, target_company):
        print(f"--- Scanning Document Stream: {pdf_path} ---")
        pages = convert_from_path(pdf_path, dpi=self.dpi)
        column_stream = []
        for idx, page in enumerate(pages):
            img = cv2.cvtColor(np.array(page), cv2.COLOR_RGB2BGR)
            h, w, _ = img.shape
            column_stream.append((img[:, 0:w//2], idx+1, "LEFT"))
            column_stream.append((img[:, w//2:], idx+1, "RIGHT"))

        is_collecting = False
        buffer_text = []
        STOP_PATTERN = re.compile(r'\(\d{8}\)|İLAN SIRA NO', re.IGNORECASE)

        found_results = []

        for col_img, page_num, col_name in column_stream:
            raw_text = self.ocr_column(col_img)
            # Split OCR text into lines for more accurate stopping
            lines = [line.strip() for line in raw_text.split("\n") if line.strip()]

            for line in lines:
                line_up = self.tr_upper(line)

                if not is_collecting:
                    # Start collecting when target company is found
                    if fuzz.partial_ratio(self.tr_upper(target_company), line_up) > 85:
                        print(f"Match Found on Page {page_num} ({col_name}): {line}")
                        is_collecting = True

                if is_collecting:
                    match = STOP_PATTERN.search(line)
                    if match:
                        # Stop detected
                        buffer_text.append(line[:match.start()].strip())
                        full_text = " ".join(buffer_text).strip()
                        if full_text:
                            found_results.append(full_text)
                            print(f"   -> End detected at stop phrase: {line[:match.start()]}")
                        buffer_text = []
                        is_collecting = False
                        continue
                    buffer_text.append(line)



        return found_results



# ---------------------------------------------------------
# EXECUTION EXAMPLE
# ---------------------------------------------------------
if __name__ == "__main__":
    ocr = TOBBOCR(dpi=200, gpu=True)

    # Example runs
    results = ocr.run("TOBBPDF/k.pdf", "KURULUS", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS KURULUS ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    results = ocr.run("TOBBPDF/r2.pdf", "SERMAYE", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS SERMAYE ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))

    results = ocr.run("TOBBPDF/p.pdf", "PAY", "GENÇ ALDEM")
    print("\n=== FINAL RESULTS PAY ===")
    print(json.dumps(results, ensure_ascii=False, indent=2))
