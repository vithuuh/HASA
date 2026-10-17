import cv2
import numpy as np
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY

# Initialize vision client
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def process_region_with_gemini(crop_bgr: np.ndarray, region_type: str, raw_ocr: str = "") -> str:
    """
    Sends cropped image regions to the vision engine for precise transcription,
    table markdown rendering, or diagram explanations.
    """
    if not client:
        return raw_ocr or "Process couldn't be completed."

    if crop_bgr is None or crop_bgr.size == 0:
        return ""

    # Encode crop to JPEG bytes
    success, encoded_img = cv2.imencode(".jpg", crop_bgr)
    if not success:
        return raw_ocr or "Process couldn't be completed."

    image_bytes = encoded_img.tobytes()

    # Formulate domain-specific prompts for answer script processing
    if region_type == "markdown_table":
        prompt = (
            "You are an academic script evaluator. Analyze this cropped image of a table. "
            "Convert all handwritten or printed text inside it into a clean, well-formatted Markdown table. "
            "Output ONLY the Markdown table. Do not include markdown code block formatting or introductory words."
        )
    elif region_type == "diagram":
        prompt = (
            "You are analyzing a handwritten answer script region containing a diagram, chart, or architecture sketch. "
            "Provide a clear, structured summary describing what the diagram illustrates, including all visible labels, "
            "arrows, inputs, outputs, and equations. Keep it concise and professional."
        )
    else:
        prompt = (
            "You are transcribing a student's handwritten answer script. "
            "Accurately transcribe all words, math notations, bullet points, and equations from this cropped image. "
            "Do not skip words, and fix obvious minor spelling glitches while preserving exact technical terms. "
            "Output ONLY the transcribed text without any conversational preamble."
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
        return raw_ocr or "Process couldn't be completed."