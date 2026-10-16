import cv2
import numpy as np
from typing import List, Dict, Any

def extract_regions(orig_image: np.ndarray, binary_thresh: np.ndarray) -> List[Dict[str, Any]]:
    """
    Performs morphological dilation to connect adjacent handwriting strokes into line blocks,
    detects external contours, filters out noise, and sorts boxes top-to-bottom.
    
    Returns list of dicts containing bbox coordinates, type heuristic, and cropped image array.
    """
    h, w = binary_thresh.shape[:2]

    # Create rectangular kernel to fuse characters horizontally into lines/paragraphs
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 9))
    dilated = cv2.dilate(binary_thresh, kernel, iterations=2)

    # Find external contours
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    raw_boxes = []
    min_area = (w * h) * 0.0005  # Ignore small noise blobs (paper artifacts/dots)

    for cnt in contours:
        x, y, box_w, box_h = cv2.boundingRect(cnt)
        area = box_w * box_h

        if area < min_area:
            continue

        # Basic aspect-ratio heuristic classification
        aspect_ratio = box_w / float(box_h)
        if aspect_ratio > 3.5 and box_h > 40:
            region_type = "markdown_table"
        elif aspect_ratio < 1.3 and area > (w * h * 0.08):
            region_type = "diagram"
        else:
            region_type = "text"

        crop = orig_image[y : y + box_h, x : x + box_w]

        raw_boxes.append({
            "bbox": {"x": int(x), "y": int(y), "w": int(box_w), "h": int(box_h)},
            "region_type": region_type,
            "crop": crop
        })

    # Sort boxes top-to-bottom (grouped by bands of 30px to handle slight slants)
    sorted_boxes = sorted(raw_boxes, key=lambda b: (b["bbox"]["y"] // 30, b["bbox"]["x"]))

    # Attach order index
    for index, region in enumerate(sorted_boxes):
        region["order_index"] = index

    return sorted_boxes