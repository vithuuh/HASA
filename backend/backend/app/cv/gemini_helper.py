import cv2
import numpy as np
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# Initialize engine client silently
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def process_region_with_gemini(crop_bgr: np.ndarray, region_type: str, raw_ocr: str = "") -> str:
    """
    Refines raw extracted content, formats table markdowns, or generates diagram descriptions.
    Fails gracefully to raw extraction without exposing internal errors or provider names.
    """
    if not client:
        return raw_ocr or "Process couldn't be completed."

    if crop_bgr is None or crop_bgr.size == 0:
        return ""

    # Encode BGR image to JPEG bytes for vision processing
    success, encoded_img = cv2.imencode(".jpg", crop_bgr)
    if not success:
        return raw_ocr or "Process couldn't be completed."

    image_bytes = encoded_img.tobytes()

    # Formulate layout prompts
    if region_type == "markdown_table":
        prompt = (
            "Analyze this cropped image of a table from an examination script. "
            "Convert the entire table accurately into a clean, standard Markdown table format. "
            "Do not add conversational fluff or introductory text."
        )
    elif region_type == "diagram":
        prompt = (
            "Analyze this cropped image from an answer sheet containing a diagram, figure, or chart. "
            "Provide a concise Markdown description outlining what is depicted along with any visible labels."
        )
    else:
        prompt = (
            f"The primary text extraction yielded: '{raw_ocr}'. "
            "Examine the image region and transcribe the handwriting with high precision. "
            "Fix spelling misreadings while preserving the student's exact intended text."
        )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ]
        )
        return response.text.strip() if response.text else (raw_ocr or "Process couldn't be completed.")
    except Exception:
        # Fallback silently without printing stack traces or provider error messages
        return raw_ocr or "Process couldn't be completed."