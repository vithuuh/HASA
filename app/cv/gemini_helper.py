import logging
import base64
import json
import cv2
import httpx
import numpy as np
from google import genai
from google.genai import types
from app.config import GEMINI_API_KEY, GROQ_API_KEY

logger = logging.getLogger("hasa.cv.ai")

def extract_full_page_with_ai(image_bytes: bytes, img_w: int, img_h: int) -> list:
    """
    Analyzes the entire answer sheet in a single AI pass.
    Identifies sections, questions, answers, and diagrams with high precision,
    preventing rate-limit errors and transcription fragmentation.
    """
    if not GROQ_API_KEY:
        return []

    prompt = """
You are an expert academic answer script visual analyzer and OCR model.
Examine this handwritten student exam sheet image.
Identify every distinct semantic section on the page:
1. Headers / Branding / Metadata (e.g. "apsara Date:", Module, Tutorial)
2. Questions (all lines from question number down to the last word before the answer)
3. Answers / Written explanations
4. Diagrams / Schematics (reconstruct as ASCII art using dashes, pipes, slashes, plus signs and arrows. Include all labels, inputs, outputs, and equations inside or beside the ASCII art)

For each section, you MUST provide its normalized 2D bounding box on a 0 to 1000 scale:
- "box_2d": [ymin, xmin, ymax, xmax]
  * ymin: top boundary (0 to 1000)
  * xmin: left boundary (0 to 1000)
  * ymax: bottom boundary (0 to 1000). CRITICAL: ymax MUST extend down past the lowest line of text in that section so no lines are cut off!
  * xmax: right boundary (0 to 1000)
- "order_index": reading sequence (0, 1, 2, ...)
- "region_type": one of ["header", "question", "text", "diagram", "markdown_table"]
- "title": descriptive name (e.g. "Apsara Header", "Question 1", "Answer Body")
- "content": verbatim transcription of handwriting in clean Markdown (use LaTeX for math, format tables or diagram bullets)

Respond ONLY with a valid JSON array of objects. No markdown code blocks, no preamble.
"""

    try:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }
            ],
            "max_tokens": 2500,
            "temperature": 0.1
        }
        with httpx.Client(timeout=35.0) as client_http:
            resp = client_http.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                if raw_text.startswith("```json"):
                    raw_text = raw_text[7:]
                if raw_text.startswith("```"):
                    raw_text = raw_text[3:]
                if raw_text.endswith("```"):
                    raw_text = raw_text[:-3]
                raw_text = raw_text.strip()
                parsed = json.loads(raw_text)
                if isinstance(parsed, list) and len(parsed) > 0:
                    logger.info(f"Full-page AI extraction succeeded with {len(parsed)} sections.")
                    return parsed
            else:
                logger.error(f"Groq full-page API error {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Full-page AI extraction failed: {e}", exc_info=True)
    return []


# Initialize vision client
gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

def _call_groq_vision(image_bytes: bytes, prompt: str) -> str:
    """Invokes Groq Vision (qwen/qwen3.8-27b) for rapid, accurate multimodal parsing."""
    if not GROQ_API_KEY:
        return ""
    try:
        b64_img = base64.b64encode(image_bytes).decode("utf-8")
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}}
                    ]
                }
            ],
            "max_tokens": 800,
            "temperature": 0.1
        }
        with httpx.Client(timeout=25.0) as client_http:
            resp = client_http.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                content = data["choices"][0]["message"]["content"]
                return content.strip() if content else ""
            else:
                logger.error(f"Groq API returned error {resp.status_code}: {resp.text}")
                return ""
    except Exception as e:
        logger.error(f"Groq Vision call failed: {e}", exc_info=True)
        return ""

def _call_gemini_vision(image_bytes: bytes, prompt: str) -> str:
    """Invokes Google Gemini Vision fallback if configured."""
    if not gemini_client:
        return ""
    for model_name in ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-1.5-flash"]:
        try:
            response = gemini_client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                    prompt
                ]
            )
            if response and response.text:
                return response.text.strip()
        except Exception:
            continue
    return ""

def process_region_with_gemini(crop_bgr: np.ndarray, region_type: str, raw_ocr: str = "") -> str:
    """
    Sends cropped image regions to the vision engine for precise transcription,
    table markdown rendering, or diagram explanations.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return ""

    success, encoded_img = cv2.imencode(".jpg", crop_bgr)
    if not success:
        return raw_ocr or ""

    image_bytes = encoded_img.tobytes()

    # Formulate domain-specific prompts for answer script processing
    if region_type == "markdown_table":
        prompt = (
            "You are an academic script evaluator. Analyze this cropped image of a table. "
            "Convert all handwritten or printed text inside it into a clean, well-formatted Markdown table. "
            "Output ONLY the Markdown table. Do not include introductory conversational words."
        )
    elif region_type == "diagram":
        prompt = (
            "You are analyzing an academic answer script diagram or schematic. "
            "Reconstruct the diagram as ASCII art using only plain text characters: dashes (-), pipes (|), plus signs (+), slashes (/ \\), and arrows (-> <-). "
            "Include all labels, box titles, input/output labels, and equations positioned near their relevant parts. "
            "Do NOT describe the diagram in prose. Do NOT use markdown code fences. "
            "Output ONLY the raw ASCII diagram, exactly as it would appear in a monospace terminal."
        )
    else:
        prompt = (
            "Transcribe all handwritten words, question numbers, equations, and sentences in this cropped answer script image verbatim into Markdown. "
            "Fix obvious minor pen slips while preserving technical terminology exactly. "
            "Output ONLY the transcribed text without conversational chat."
        )

    # 1. Primary engine: Groq Vision (Ultra-fast & accurate)
    result = _call_groq_vision(image_bytes, prompt)
    if result:
        return result

    # 2. Secondary engine: Gemini Vision
    result = _call_gemini_vision(image_bytes, prompt)
    if result:
        return result

    # 3. Fallback: Raw OCR
    return raw_ocr or ""


