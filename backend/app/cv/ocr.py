import cv2
import numpy as np
import pytesseract
import os

# Check configurable Tesseract path from env or common Windows locations
tesseract_env = os.getenv("TESSERACT_CMD")
common_paths = [
    tesseract_env,
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe")
]

for p in common_paths:
    if p and os.path.exists(p):
        pytesseract.pytesseract.tesseract_cmd = p
        break


def extract_raw_ocr(crop_bgr: np.ndarray) -> str:
    """
    Performs primary OCR extraction on cropped image regions using Tesseract.
    Returns cleaned raw string output.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return ""

    try:
        # Convert crop to grayscale for Tesseract
        gray = cv2.cvtColor(crop_bgr, cv2.COLOR_BGR2GRAY)

        # Simple contrast enhancement
        gray = cv2.equalizeHist(gray)

        # Run Tesseract with Page Segmentation Mode 6 (Assume a single uniform block of text)
        config = r"--oem 3 --psm 6"
        raw_text = pytesseract.image_to_string(gray, config=config)

        return raw_text.strip()
    except Exception:
        return ""