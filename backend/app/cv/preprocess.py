import cv2
import numpy as np

def load_and_preprocess(image_bytes: bytes) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Decodes image bytes, applies median blur to handle paper glare,
    and returns a robust binary mask for handwriting layout detection.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise ValueError("Process couldn't be completed.")

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    
    # Mild Gaussian blur to smooth out shadow noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive thresholding calibrated for pen-on-paper lighting
    binary = cv2.adaptiveThreshold(
        blurred, 
        255, 
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
        cv2.THRESH_BINARY_INV, 
        21, 
        10
    )
    
    return image, gray, binary