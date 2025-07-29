"""
Utility functions for image conversion and processing
"""

import cv2
import numpy as np
from PIL import Image
from typing import Optional, Tuple, Union
import io
import logging

logger = logging.getLogger(__name__)


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """
    Convert PIL Image to OpenCV format (BGR).
    
    Args:
        pil_image: PIL Image object
        
    Returns:
        OpenCV image as numpy array in BGR format
        
    Raises:
        ValueError: If image format is not supported
    """
    try:
        # Convert to RGB if necessary
        if pil_image.mode != 'RGB':
            if pil_image.mode == 'RGBA':
                # Convert RGBA to RGB with white background
                rgb_image = Image.new('RGB', pil_image.size, (255, 255, 255))
                rgb_image.paste(pil_image, mask=pil_image.split()[3])
                pil_image = rgb_image
            else:
                pil_image = pil_image.convert('RGB')
        
        # Convert to numpy array
        numpy_image = np.array(pil_image)
        
        # Convert RGB to BGR for OpenCV
        bgr_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
        
        return bgr_image
        
    except Exception as e:
        logger.error(f"Failed to convert PIL image to OpenCV format: {e}")
        raise ValueError(f"Unsupported image format or conversion error: {e}")


def cv2_to_pil(cv2_image: np.ndarray) -> Image.Image:
    """
    Convert OpenCV image to PIL format.
    
    Args:
        cv2_image: OpenCV image as numpy array (BGR or grayscale)
        
    Returns:
        PIL Image object
        
    Raises:
        ValueError: If image format is not supported
    """
    try:
        if len(cv2_image.shape) == 2:
            # Grayscale image
            return Image.fromarray(cv2_image)
        elif len(cv2_image.shape) == 3:
            # Color image - convert BGR to RGB
            rgb_image = cv2.cvtColor(cv2_image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb_image)
        else:
            raise ValueError(f"Unsupported image shape: {cv2_image.shape}")
            
    except Exception as e:
        logger.error(f"Failed to convert OpenCV image to PIL format: {e}")
        raise ValueError(f"Conversion error: {e}")


def bytes_to_cv2(image_bytes: bytes) -> np.ndarray:
    """
    Convert image bytes to OpenCV format.
    
    Args:
        image_bytes: Image data as bytes
        
    Returns:
        OpenCV image as numpy array
        
    Raises:
        ValueError: If bytes cannot be decoded as image
    """
    try:
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        
        # Decode image
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            raise ValueError("Failed to decode image from bytes")
        
        return image
        
    except Exception as e:
        logger.error(f"Failed to convert bytes to OpenCV image: {e}")
        raise ValueError(f"Invalid image data: {e}")


def cv2_to_bytes(cv2_image: np.ndarray, format: str = '.png') -> bytes:
    """
    Convert OpenCV image to bytes.
    
    Args:
        cv2_image: OpenCV image as numpy array
        format: Output format (e.g., '.png', '.jpg')
        
    Returns:
        Image data as bytes
        
    Raises:
        ValueError: If encoding fails
    """
    try:
        # Encode image
        success, encoded = cv2.imencode(format, cv2_image)
        
        if not success:
            raise ValueError(f"Failed to encode image to {format}")
        
        return encoded.tobytes()
        
    except Exception as e:
        logger.error(f"Failed to convert OpenCV image to bytes: {e}")
        raise ValueError(f"Encoding error: {e}")


def validate_image(image: Union[np.ndarray, Image.Image], 
                  max_dimension: int = 4096,
                  min_dimension: int = 50) -> bool:
    """
    Validate image dimensions and format.
    
    Args:
        image: Image to validate (OpenCV or PIL format)
        max_dimension: Maximum allowed dimension
        min_dimension: Minimum allowed dimension
        
    Returns:
        True if image is valid, False otherwise
    """
    try:
        if isinstance(image, Image.Image):
            width, height = image.size
        elif isinstance(image, np.ndarray):
            height, width = image.shape[:2]
        else:
            logger.error(f"Invalid image type: {type(image)}")
            return False
        
        # Check dimensions
        if width < min_dimension or height < min_dimension:
            logger.warning(f"Image too small: {width}x{height}")
            return False
        
        if width > max_dimension or height > max_dimension:
            logger.warning(f"Image too large: {width}x{height}")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating image: {e}")
        return False


def resize_image_if_needed(image: np.ndarray, 
                          max_dimension: int = 4096) -> Tuple[np.ndarray, float]:
    """
    Resize image if it exceeds maximum dimension while maintaining aspect ratio.
    
    Args:
        image: OpenCV image
        max_dimension: Maximum allowed dimension
        
    Returns:
        Tuple of (resized_image, scale_factor)
    """
    height, width = image.shape[:2]
    
    if width <= max_dimension and height <= max_dimension:
        return image, 1.0
    
    # Calculate scale factor
    scale = max_dimension / max(width, height)
    
    # Calculate new dimensions
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Resize image
    resized = cv2.resize(image, (new_width, new_height), 
                        interpolation=cv2.INTER_AREA)
    
    logger.info(f"Resized image from {width}x{height} to {new_width}x{new_height}")
    
    return resized, scale


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image values to improve detection.
    
    Args:
        image: OpenCV image
        
    Returns:
        Normalized image
    """
    # Apply histogram equalization to improve contrast
    if len(image.shape) == 2:
        # Grayscale
        return cv2.equalizeHist(image)
    else:
        # Color - equalize each channel
        channels = cv2.split(image)
        eq_channels = [cv2.equalizeHist(ch) for ch in channels]
        return cv2.merge(eq_channels)


def apply_clahe(image: np.ndarray, clip_limit: float = 2.0, 
                tile_grid_size: Tuple[int, int] = (8, 8)) -> np.ndarray:
    """
    Apply Contrast Limited Adaptive Histogram Equalization (CLAHE).
    
    Args:
        image: OpenCV image (grayscale or color)
        clip_limit: Threshold for contrast limiting
        tile_grid_size: Size of grid for histogram equalization
        
    Returns:
        CLAHE enhanced image
    """
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    
    if len(image.shape) == 2:
        # Grayscale
        return clahe.apply(image)
    else:
        # Color - convert to LAB and apply CLAHE to L channel
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = clahe.apply(l)
        enhanced_lab = cv2.merge([l, a, b])
        return cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)


def safe_image_read(image_path: str) -> Optional[np.ndarray]:
    """
    Safely read an image file with error handling.
    
    Args:
        image_path: Path to image file
        
    Returns:
        OpenCV image or None if read fails
    """
    try:
        image = cv2.imread(image_path)
        if image is None:
            logger.error(f"Failed to read image: {image_path}")
            return None
        return image
    except Exception as e:
        logger.error(f"Error reading image {image_path}: {e}")
        return None