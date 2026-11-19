"""
Image processing utilities
"""

import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from typing import Optional


def preprocess_image(image_bytes: bytes) -> Optional[np.ndarray]:
    """
    Convert uploaded image bytes to OpenCV format
    
    Args:
        image_bytes: Raw image bytes
        
    Returns:
        OpenCV image (BGR) or None if conversion fails
    """
    try:
        # Convert bytes to PIL Image
        pil_image = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if needed
        if pil_image.mode != 'RGB':
            pil_image = pil_image.convert('RGB')
        
        # Convert PIL to numpy array
        image_array = np.array(pil_image)
        
        # Convert RGB to BGR for OpenCV
        bgr_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        
        return bgr_image
        
    except Exception as e:
        print(f"Error preprocessing image: {e}")
        return None


def resize_image(image: np.ndarray, max_dimension: int = 1024) -> np.ndarray:
    """
    Resize image while maintaining aspect ratio
    
    Args:
        image: OpenCV image
        max_dimension: Maximum width or height
        
    Returns:
        Resized image
    """
    height, width = image.shape[:2]
    
    if max(height, width) <= max_dimension:
        return image
    
    if height > width:
        new_height = max_dimension
        new_width = int(width * (max_dimension / height))
    else:
        new_width = max_dimension
        new_height = int(height * (max_dimension / width))
    
    resized = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    return resized


def enhance_image(image: np.ndarray) -> np.ndarray:
    """
    Apply basic enhancement to improve skin tone detection
    
    Args:
        image: OpenCV image
        
    Returns:
        Enhanced image
    """
    # Convert to LAB for luminance adjustment
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    
    # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    
    # Merge channels
    enhanced_lab = cv2.merge([l, a, b])
    
    # Convert back to BGR
    enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
    
    return enhanced


def hex_to_lab(hex_color: str) -> np.ndarray:
    """Convert sRGB hex to true CIELAB (L* 0..100, signed a*/b*)."""
    color = hex_color.lstrip("#")
    if len(color) != 6:
        raise ValueError("Expected a six-digit hex color")
    r, g, b = [int(color[i:i + 2], 16) for i in (0, 2, 4)]
    bgr = np.array([[[b, g, r]]], dtype=np.float32) / 255.0
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)[0, 0].astype(float)


def lab_to_hex(lab: np.ndarray) -> str:
    """Convert true CIELAB back to a displayable sRGB hex swatch."""
    lab_img = np.asarray(lab, dtype=np.float32).reshape(1, 1, 3)
    bgr = cv2.cvtColor(lab_img, cv2.COLOR_LAB2BGR)[0, 0]
    b, g, r = np.rint(np.clip(bgr, 0, 1) * 255).astype(np.uint8)
    return f"#{r:02x}{g:02x}{b:02x}"
