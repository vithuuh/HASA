import cv2
import numpy as np
import pytesseract
import os

# Explicitly set Tesseract executable path for Windows
tesseract_cmd_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if os.path.exists(tesseract_cmd_path):
    pytesseract.pytesseract.tesseract_cmd = tesseract_cmd_path

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