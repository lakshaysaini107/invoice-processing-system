import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image

def validate_image_format(file_path: str) -> bool:
    """Validate if file is a supported image format"""
    supported = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.pdf'}
    return Path(file_path).suffix.lower() in supported

def get_image_dimensions(file_path: str) -> Optional[Tuple[int, int]]:
    """Get image width and height"""
    try:
        image = cv2.imread(file_path)
        if image is not None:
            return image.shape[1], image.shape[0]  # width, height
    except:
        pass
    return None

def is_image_quality_sufficient(file_path: str, min_width: int = 800, min_height: int = 600) -> bool:
    """Check if image meets minimum quality standards"""
    try:
        dimensions = get_image_dimensions(file_path)
        if dimensions:
            width, height = dimensions
            return width >= min_width and height >= min_height
    except:
        pass
    return False

def convert_image_to_rgb(file_path: str) -> Optional[np.ndarray]:
    """Convert image to RGB format"""
    try:
        image = cv2.imread(file_path)
        if image is not None:
            return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    except:
        pass
    return None

def resize_image(image: np.ndarray, max_width: int = 2000, max_height: int = 2800) -> np.ndarray:
    """Resize image if it exceeds max dimensions"""
    height, width = image.shape[:2]
    
    if width <= max_width and height <= max_height:
        return image
    
    scale = min(max_width / width, max_height / height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)

def rotate_image(image: np.ndarray, angle: float) -> np.ndarray:
    """Rotate image by given angle"""
    h, w = image.shape[:2]
    center = (w // 2, h // 2)
    
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
    rotated = cv2.warpAffine(image, rotation_matrix, (w, h))
    
    return rotated

def get_image_brightness(image: np.ndarray) -> float:
    """Calculate average brightness"""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return np.mean(gray)

def is_image_dark(image: np.ndarray, threshold: float = 50.0) -> bool:
    """Check if image is too dark"""
    brightness = get_image_brightness(image)
    return brightness < threshold
