from pathlib import Path
from PIL import Image
import numpy as np
import cv2

def get_path_to(package) -> Path:
    """Get path to directory holding a package's __init__.py file"""
    return Path(package.__path__[0])

def get_image_from(image_path: str) -> Image.Image:
    """Load image from a file. Close the file without losing the image"""
    with Image.open(image_path) as image:
        image.load()
    return image

def convert_bgr_ndarray_to_rgb_image(bgr_array: np.ndarray) -> Image.Image:
    """Convert a BGR ndarray (eg generated from `cv2.imread()`) to RGB PIL Image"""
    rgb_array = cv2.cvtColor(bgr_array, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb_array)
