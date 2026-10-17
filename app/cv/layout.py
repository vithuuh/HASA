import cv2
import numpy as np
from typing import List, Dict, Any

def extract_regions(orig_image: np.ndarray, binary_thresh: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extracts line blocks, filters page margin shadows, and sorts boxes top-to-bottom.
    """
    h, w = binary_thresh.shape[:2]

    # Smaller horizontal kernel to fuse words into lines without lumping the whole page
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 5))
    dilated = cv2.dilate(binary_thresh, kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    # Ignore tiny noise blobs and margin edge shadows
    min_area = (w * h) * 0.001

    for cnt in contours:
        x, y, box_w, box_h = cv2.boundingRect(cnt)
        area = box_w * box_h

        # Filter out tiny noise and extreme margin shadow strips
        if area < min_area:
            continue
        if x < int(w * 0.03) and box_w < int(w * 0.1):  # Ignore left margin binder/shadow strips
            continue

        # Add 5px padding around crops
        pad = 5
        crop_x1 = max(0, x - pad)
        crop_y1 = max(0, y - pad)
        crop_x2 = min(w, x + box_w + pad)
        crop_y2 = min(h, y + box_h + pad)

        crop = orig_image[crop_y1:crop_y2, crop_x1:crop_x2]

        aspect_ratio = box_w / float(box_h)

        # Better classification rules
        if aspect_ratio > 3.0 and box_h > 35:
            region_type = "markdown_table"
        elif aspect_ratio < 1.3 and area > (w * h * 0.10):
            region_type = "diagram"
        else:
            region_type = "text"

        raw_boxes.append({
            "bbox": {"x": int(x), "y": int(y), "w": int(box_w), "h": int(box_h)},
            "region_type": region_type,
            "crop": crop
        })

    # Sort boxes top-to-bottom logically
    sorted_boxes = sorted(raw_boxes, key=lambda b: (b["bbox"]["y"] // 30, b["bbox"]["x"]))

    for index, region in enumerate(sorted_boxes):
        region["order_index"] = index

    return sorted_boxes