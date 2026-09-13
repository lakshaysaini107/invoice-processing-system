import io
from typing import Optional
from PIL import Image
import numpy as np


def load_image(file_source) -> Optional[np.ndarray]:
    try:
        if isinstance(file_source, str):
            image = Image.open(file_source).convert("RGB")
        elif isinstance(file_source, bytes):
            image = Image.open(io.BytesIO(file_source)).convert("RGB")
        elif isinstance(file_source, Image.Image):
            image = file_source.convert("RGB")
        else:
            return None
        return np.array(image)
    except Exception:
        return None


def resize_image_max(img_np: np.ndarray, max_dim: int = 2048) -> np.ndarray:
    h, w = img_np.shape[:2]
    if max(h, w) <= max_dim:
        return img_np
    scale = max_dim / float(max(h, w))
    new_w = int(w * scale)
    new_h = int(h * scale)
    pil_img = Image.fromarray(img_np)
    resized_pil = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
    return np.array(resized_pil)
