import os
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from typing import List

from app.config import UPLOADS_DIR
from app.database import init_db, get_session
from app.models import Script, Region
from app.cv.preprocess import load_and_preprocess
from app.cv.layout import extract_regions
from app.cv.ocr import extract_raw_ocr
from app.cv.gemini_helper import process_region_with_gemini

app = FastAPI(title="HASA Engine")

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded images statically
app.mount("/uploads", StaticFiles(directory=str(UPLOADS_DIR)), name="uploads")

@app.on_event("startup")
def on_startup():
    init_db()

@app.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_script(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """Uploads an answer sheet image and registers it in the database."""
    try:
        file_path = UPLOADS_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())

        script = Script(filename=file.filename, file_path=str(file_path), status="uploaded")
        session.add(script)
        session.commit()
        session.refresh(script)
        return script
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Process couldn't be completed."
        )

@app.post("/analyze/{script_id}")
async def analyze_script(script_id: int, session: Session = Depends(get_session)):
    """Triggers image preprocessing, layout extraction, and OCR refinement."""
    script = session.get(Script, script_id)
    if not script:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Process couldn't be completed."
        )

    try:
        script.status = "processing"
        session.add(script)
        session.commit()

        # Read image binary data
        with open(script.file_path, "rb") as f:
            image_bytes = f.read()

        # Execute CV Pipeline
        orig_img, _, binary_thresh = load_and_preprocess(image_bytes)
        detected_regions = extract_regions(orig_img, binary_thresh)

        # Process each region
        for reg in detected_regions:
            crop = reg["crop"]
            raw_ocr = extract_raw_ocr(crop)
            refined_content = process_region_with_gemini(crop, reg["region_type"], raw_ocr)

            db_region = Region(
                script_id=script.id,
                order_index=reg["order_index"],
                region_type=reg["region_type"],
                bbox_x=reg["bbox"]["x"],
                bbox_y=reg["bbox"]["y"],
                bbox_w=reg["bbox"]["w"],
                bbox_h=reg["bbox"]["h"],
                raw_ocr_text=raw_ocr,
                refined_content=refined_content
            )
            session.add(db_region)

        script.status = "completed"
        session.add(script)
        session.commit()
        session.refresh(script)

        return {"status": "completed", "script_id": script.id, "total_regions": len(detected_regions)}

    except Exception:
        script.status = "error"
        session.add(script)
        session.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Process couldn't be completed."
        )

@app.get("/scripts/{script_id}")
async def get_script_analysis(script_id: int, session: Session = Depends(get_session)):
    """Retrieves script details alongside all detected bounding boxes and parsed content."""
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