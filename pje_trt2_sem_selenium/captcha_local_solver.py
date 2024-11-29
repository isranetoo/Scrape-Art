import os
import string
import random
import base64
from io import BytesIO
 
import numpy as np
import pytesseract
from PIL import Image
from PIL import ImageFilter
from scipy.ndimage import gaussian_filter
 
 
# Check if running on windows computer and if so, adds pytesseract to path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'
 
 
def solve_captcha_local(bytes_data, th0: int = 185, th1: int = 105, sig1: int = 1.1, th2: int = 105, sig2: int = 1.0) -> str:
    """ Attempts to solve captcha with pytesseract
 
    Args:
        bytes_data: image encoded as base64
        th0: erasing threshold 0, Defautls to 185
        sig1:  blurring sigma 1, Defautls to 1.1
        th1: erasing threshold 1, Defautls to 105
        sig2: blurring sigma 2, Defautls to 1.0
        th2: erasing threshold 2, Defautls to 105
 
    Returns:
        Captcha response
    """
    original = Image.open(BytesIO(base64.b64decode(bytes_data)))
 
    # converting to black and white
    black_and_white = original.convert("L")
    img_threshold_0 = black_and_white.point(lambda p: p > th0 and 255)
 
    # Blurs image and aplies new threshold 1
    img_blurred_1 = Image.fromarray(gaussian_filter(np.array(img_threshold_0), sigma=sig1))
    img_threshold_1 = img_blurred_1.point(lambda p: p > th1 and 255)
    img_ee_1 = img_threshold_1.filter(ImageFilter.EDGE_ENHANCE_MORE)
    img_shp_1 = img_ee_1.filter(ImageFilter.SHARPEN)
 
    # Blurs image and aplies new threshold 2
    blurred2 = Image.fromarray(gaussian_filter(np.array(img_shp_1), sigma=sig2))
    img_threshold_2 = blurred2.point(lambda p: p > th2 and 255)
    img_ee_2 = img_threshold_2.filter(ImageFilter.EDGE_ENHANCE_MORE)
    img_shp_2 = img_ee_2.filter(ImageFilter.SHARPEN)
 
    ocr_config = '--psm 11 --oem 3 -c tessedit_char_whitelist=123456789abcdefghijklmnpqrstuvxwyz'
    result = pytesseract.image_to_string(img_shp_2, config=ocr_config)
    result = result.strip().replace(chr(32), "").replace("\n", "")
 
    if len(result) != 6:
        result = pytesseract.image_to_string(img_shp_1, config=ocr_config)
        return result.strip().replace(chr(32), "").replace("\n", "")
    return result
 
if __name__ == "__main__":
    with open("../temp/original_804231.png", "rb") as bytes_data:
        print(solve_captcha_local(base64.b64encode(bytes_data.read())))