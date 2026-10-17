import cv2
import numpy as np

def load_and_preprocess(image_bytes: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Decodes image bytes, creates grayscale image, applies Gaussian blur,
    and returns adaptive threshold binary mask.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Process couldn't be completed.")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Gaussian blur to reduce high-frequency noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive thresholding to convert image to binary
    binary = cv2.adaptiveThreshold(
        blurred, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        15, 
        4
    )
    
    return image, gray, binary