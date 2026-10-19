import cv2
import numpy as np
from typing import List, Dict, Any

def _is_table(crop_binary: np.ndarray, w: int, h: int) -> bool:
    """
    Detects if a region is likely a table by searching for orthogonal
    horizontal and vertical grid lines.
    """
    if h < 60 or w < 100:
        return False

    h_len = max(25, w // 4)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_len, 1))
    h_lines = cv2.morphologyEx(crop_binary, cv2.MORPH_OPEN, h_kernel)
    has_h = np.count_nonzero(h_lines) > (w * 0.5)

    v_len = max(25, h // 4)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_len))
    v_lines = cv2.morphologyEx(crop_binary, cv2.MORPH_OPEN, v_kernel)
    has_v = np.count_nonzero(v_lines) > (h * 0.5)

    return bool(has_h and has_v)

def extract_regions(orig_image: np.ndarray, binary_thresh: np.ndarray) -> List[Dict[str, Any]]:
    """
    Extracts clean, cohesive sections (headers, questions, answers, diagrams).
    Eliminates photo edge shadow frames and filters desk/keyboard noise.
    """
    h, w = binary_thresh.shape[:2]

    # Zero out outer 2.5% image borders to eliminate dark desk/shadow frame contours
    border_y = int(h * 0.025)
    border_x = int(w * 0.025)
    clean_thresh = binary_thresh.copy()
    clean_thresh[:border_y, :] = 0
    clean_thresh[-border_y:, :] = 0
    clean_thresh[:, :border_x] = 0
    clean_thresh[:, -border_x:] = 0

    # Horizontal dilation to connect words across the same line
    line_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (25, 4))
    dilated = cv2.dilate(clean_thresh, line_kernel, iterations=2)

    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    min_area = (w * h) * 0.003
    initial_boxes = []

    for cnt in contours:
        x, y, box_w, box_h = cv2.boundingRect(cnt)
        area = box_w * box_h

        # Ignore tiny specks or full-frame contours
        if area < min_area or (box_w > int(w * 0.98) and box_h > int(h * 0.98)):
            continue
        # Filter margin edge strips and right-side desk/keyboard
        if x > int(w * 0.88):
            continue

        initial_boxes.append((x, y, box_w, box_h))

    # Sort top to bottom
    initial_boxes = sorted(initial_boxes, key=lambda b: (b[1], b[0]))

    # Merge consecutive lines that belong to the SAME question/answer section
    max_section_height = int(h * 0.32)
    paragraphs = []

    for b in initial_boxes:
        x, y, bw, bh = b
        if not paragraphs:
            paragraphs.append([x, y, bw, bh])
            continue

        px, py, pbw, pbh = paragraphs[-1]
        py2 = py + pbh
        gap = y - py2

        # Check horizontal overlap
        px2 = px + pbw
        bx2 = x + bw
        h_overlap = max(0, min(px2, bx2) - max(px, x))
        has_overlap = (h_overlap / min(pbw, bw)) > 0.20 if min(pbw, bw) > 0 else False

        # Merge if within 30px vertically and section height stays reasonable
        if 0 <= gap <= 30 and has_overlap and (y + bh - py) <= max_section_height:
            nx = min(px, x)
            ny = py
            nx2 = max(px2, bx2)
            ny2 = y + bh
            paragraphs[-1] = [nx, ny, nx2 - nx, ny2 - ny]
        else:
            paragraphs.append([x, y, bw, bh])

    raw_boxes = []
    for x, y, box_w, box_h in paragraphs:
        pad = 8
        crop_x1 = max(0, x - pad)
        crop_y1 = max(0, y - pad)
        crop_x2 = min(w, x + box_w + pad)
        crop_y2 = min(h, y + box_h + pad)

        crop = orig_image[crop_y1:crop_y2, crop_x1:crop_x2]
        crop_bin = clean_thresh[crop_y1:crop_y2, crop_x1:crop_x2]
        area = box_w * box_h
        aspect_ratio = box_w / float(box_h)

        if _is_table(crop_bin, box_w, box_h):
            region_type = "markdown_table"
        elif aspect_ratio < 2.2 and box_h > 100 and area > (w * h * 0.05):
            region_type = "diagram"
        else:
            region_type = "text"

        raw_boxes.append({
            "bbox": {"x": int(crop_x1), "y": int(crop_y1), "w": int(crop_x2 - crop_x1), "h": int(crop_y2 - crop_y1)},
            "region_type": region_type,
            "crop": crop
        })

    # Sort in natural reading order
    sorted_boxes = sorted(raw_boxes, key=lambda b: (b["bbox"]["y"] // 40, b["bbox"]["x"]))

    for index, region in enumerate(sorted_boxes):
        region["order_index"] = index

    return sorted_boxes

