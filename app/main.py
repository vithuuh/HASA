import io
import os
import uuid
import asyncio
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from app.config import UPLOADS_DIR
from app.database import init_db, get_session
from app.models import Script, Region
from app.cv.preprocess import load_and_preprocess
from app.cv.layout import extract_regions
from app.cv.ocr import extract_raw_ocr
from app.cv.gemini_helper import process_region_with_gemini, extract_full_page_with_ai


logger = logging.getLogger("hasa.main")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(title="HASA Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directory exists before mounting static route
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_script(file: UploadFile = File(...), session: Session = Depends(get_session)):
    try:
        UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Sanitize filename and prepend unique UUID to prevent file collisions
        original_name = Path(file.filename).name
        unique_filename = f"{uuid.uuid4().hex[:10]}_{original_name}"
        file_path = UPLOADS_DIR / unique_filename

        contents = await file.read()

        # Reject unsupported file types early
        ext = Path(file.filename).suffix.lower()
        if ext not in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".pdf"):
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type '{ext}'. Accepted: images or PDF."
            )

        with open(file_path, "wb") as f:
            f.write(contents)

        # Convert path to POSIX string format (uses forward slashing '/')
        normalized_path = file_path.as_posix()

        script = Script(filename=unique_filename, file_path=normalized_path, status="uploaded")
        session.add(script)
        session.commit()
        session.refresh(script)
        logger.info(f"Script uploaded successfully: ID={script.id}, file={unique_filename}")
        return script
    except Exception as e:
        logger.error(f"UPLOAD ERROR: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Upload failed: {str(e)}"
        )

def _extract_cv_regions(image_bytes: bytes):
    """Worker function to run CPU-bound OpenCV tasks in threadpool."""
    orig_img, _, binary_thresh = load_and_preprocess(image_bytes)
    return extract_regions(orig_img, binary_thresh)

def _process_single_region(reg: dict) -> dict:
    """Worker function to run OCR and Gemini for a single region."""
    crop = reg["crop"]
    raw_ocr = extract_raw_ocr(crop)
    refined_content = process_region_with_gemini(crop, reg["region_type"], raw_ocr)
    return {
        "order_index": reg["order_index"],
        "region_type": reg["region_type"],
        "bbox": reg["bbox"],
        "raw_ocr_text": raw_ocr,
        "refined_content": refined_content,
    }

@app.post("/analyze/{script_id}")
async def analyze_script(script_id: int, session: Session = Depends(get_session)):
    script = session.get(Script, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Script with ID {script_id} not found."
        )

    try:
        script.status = "processing"
        session.add(script)
        session.commit()

        # Clean up any existing regions in case this script is being re-analyzed
        existing_regions = session.exec(select(Region).where(Region.script_id == script_id)).all()
        for er in existing_regions:
            session.delete(er)
        session.commit()

        with open(script.file_path, "rb") as f:
            file_bytes = f.read()

        # ── PDF support: convert each page to a JPEG and process independently ──
        file_ext = Path(script.file_path).suffix.lower()
        if file_ext == ".pdf":
            all_sections = []
            order_offset = 0
            try:
                import fitz  # PyMuPDF
                pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
                logger.info(f"PDF detected: {pdf_doc.page_count} pages for script {script_id}.")
                for page_num in range(pdf_doc.page_count):
                    page = pdf_doc[page_num]
                    # Render at 2x resolution for better OCR quality
                    mat = fitz.Matrix(2.0, 2.0)
                    pix = page.get_pixmap(matrix=mat, alpha=False)
                    page_img_bytes = pix.tobytes("jpeg")

                    page_sections = await asyncio.to_thread(
                        extract_full_page_with_ai, page_img_bytes, pix.width, pix.height
                    )
                    for sec in page_sections:
                        sec["order_index"] = int(sec.get("order_index", 0)) + order_offset
                        sec["title"] = f"[P{page_num + 1}] {sec.get('title', '')}"
                    all_sections.extend(page_sections)
                    order_offset += len(page_sections)
                pdf_doc.close()
            except ImportError:
                logger.error("PyMuPDF (fitz) is not installed. Cannot process PDF.")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="PDF support requires PyMuPDF. Run: pip install pymupdf"
                )

            if all_sections:
                all_sections = sorted(all_sections, key=lambda s: int(s.get("order_index", 0)))
                for idx, item in enumerate(all_sections):
                    db_region = Region(
                        script_id=script.id,
                        order_index=int(item.get("order_index", idx)),
                        region_type=item.get("region_type", "text"),
                        bbox_x=0, bbox_y=0, bbox_w=100, bbox_h=30,
                        raw_ocr_text="",
                        refined_content=item.get("content", ""),
                    )
                    session.add(db_region)
                script.status = "completed"
                session.add(script)
                session.commit()
                session.refresh(script)
                logger.info(f"PDF analysis completed for script {script_id} ({len(all_sections)} sections across all pages).")
                return {"status": "completed", "script_id": script.id, "total_regions": len(all_sections)}
            else:
                raise HTTPException(status_code=500, detail="No content could be extracted from the PDF.")

        # ── Image path (existing logic) ──
        image_bytes = file_bytes

        import cv2
        import numpy as np
        np_arr = np.frombuffer(image_bytes, np.uint8)
        img_mat = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        img_h, img_w = img_mat.shape[:2] if img_mat is not None else (1280, 960)

        # 1. Primary Path: Full-page high-precision AI extraction (prevents fragmentation and rate limits)
        ai_sections = await asyncio.to_thread(extract_full_page_with_ai, image_bytes, img_w, img_h)

        if ai_sections:
            # Sort sections by reading order
            ai_sections = sorted(ai_sections, key=lambda s: int(s.get("order_index", 0)))

            for idx, item in enumerate(ai_sections):
                box_2d = item.get("box_2d")
                if box_2d and len(box_2d) == 4:
                    ymin, xmin, ymax, xmax = [float(v) for v in box_2d]
                    if ymax <= 1.0 and xmax <= 1.0:
                        ymin, xmin, ymax, xmax = [v * 1000 for v in [ymin, xmin, ymax, xmax]]

                    # If this is a question or multi-line text block, ensure ymax encompasses all lines before next section
                    if idx < len(ai_sections) - 1:
                        next_box = ai_sections[idx + 1].get("box_2d")
                        if next_box and len(next_box) == 4:
                            next_ymin = float(next_box[0]) * (1000 if float(next_box[0]) <= 1.0 else 1)
                            if next_ymin > ymax and (next_ymin - ymax) < 450:
                                ymax = max(ymax, next_ymin - 20)

                    px = max(0, int(xmin * img_w / 1000))
                    py = max(0, int(ymin * img_h / 1000))
                    pw = min(img_w - px, int((xmax - xmin) * img_w / 1000))
                    ph = min(img_h - py, int((ymax - ymin) * img_h / 1000))
                else:
                    bbox = item.get("bbox", {})
                    px = int(bbox.get("x", 40))
                    py = int(bbox.get("y", 40))
                    pw = int(bbox.get("w", img_w - 80))
                    ph = int(bbox.get("h", 120))

                db_region = Region(
                    script_id=script.id,
                    order_index=int(item.get("order_index", idx)),
                    region_type=item.get("region_type", "text"),
                    bbox_x=px,
                    bbox_y=py,
                    bbox_w=max(50, pw),
                    bbox_h=max(30, ph),
                    raw_ocr_text="",
                    refined_content=item.get("content", ""),
                )
                session.add(db_region)

            script.status = "completed"
            session.add(script)
            session.commit()
            session.refresh(script)

            logger.info(f"Full-page AI extraction completed for script {script_id} ({len(ai_sections)} sections).")
            return {"status": "completed", "script_id": script.id, "total_regions": len(ai_sections)}


        # 2. Fallback Path: OpenCV + Individual Crop AI
        detected_regions = await asyncio.to_thread(_extract_cv_regions, image_bytes)
        logger.info(f"Fallback to CV: detected {len(detected_regions)} regions for script {script_id}.")

        tasks = [asyncio.to_thread(_process_single_region, reg) for reg in detected_regions]
        processed_regions = await asyncio.gather(*tasks)

        for item in processed_regions:
            db_region = Region(
                script_id=script.id,
                order_index=item["order_index"],
                region_type=item["region_type"],
                bbox_x=item["bbox"]["x"],
                bbox_y=item["bbox"]["y"],
                bbox_w=item["bbox"]["w"],
                bbox_h=item["bbox"]["h"],
                raw_ocr_text=item["raw_ocr_text"],
                refined_content=item["refined_content"],
            )
            session.add(db_region)

        script.status = "completed"
        session.add(script)
        session.commit()
        session.refresh(script)

        logger.info(f"Analysis completed successfully for script {script_id}.")
        return {"status": "completed", "script_id": script.id, "total_regions": len(detected_regions)}


    except Exception as e:
        logger.error(f"Analysis error for script {script_id}: {e}", exc_info=True)
        script.status = "error"
        session.add(script)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Analysis failed: {str(e)}"
        )

@app.get("/scripts/{script_id}")
async def get_script_analysis(script_id: int, session: Session = Depends(get_session)):
    script = session.get(Script, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Process couldn't be completed."
        )

    statement = select(Region).where(Region.script_id == script_id).order_by(Region.order_index)
    regions = session.exec(statement).all()

    return {
        "script": script,
        "regions": regions
    }