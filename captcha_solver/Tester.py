
import os
import base64
from io import BytesIO

import pandas as pd
import numpy as np

import pytesseract
from PIL import Image
from PIL import ImageFilter
from scipy.ndimage import gaussian_filter


# Check if running on windows computer and if so, adds pytesseract to path
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'


def solve_captcha_local(th1, th2, sig1, sig2, bytes_data):
    original = Image.open(BytesIO(base64.b64decode(bytes_data)))

    black_and_white = original.convert("L")  # converting to black and white
    first_threshold = black_and_white.point(lambda p: p > th1 and 255)

    blur = np.array(first_threshold)  # create an image array
    blurred = gaussian_filter(blur, sigma=sig1)
    blurred = Image.fromarray(blurred)
    final = blurred.point(lambda p: p > th2 and 255)
    final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final = final.filter(ImageFilter.SHARPEN)

    blur2 = np.array(final)  # create an image array
    blurred2 = gaussian_filter(blur2, sigma=sig2)
    blurred2 = Image.fromarray(blurred2)
    final2 = blurred2.point(lambda p: p > th2 and 255)
    final2 = final2.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final2 = final2.filter(ImageFilter.SHARPEN)

    ocr_config = '--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvxwyz'
    number = pytesseract.image_to_string(final2, config=ocr_config)
    number = number.strip().lstrip().rstrip().replace(chr(32), "").replace("\n", "")

    return number


files = './images/'

res = {}
for p1 in range(100, 200, 5):
    for p2 in range(100, 200, 5):
        for p3 in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]:
             for p4 in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]:

                score = {}
                for img in os.listdir(files):
                    with open(f"{files}{img}", "rb") as bytes_data:
                        this_pred = solve_captcha_local(p1, p2, p3, p4, base64.b64encode(bytes_data.read()))

                    if this_pred == img.split(".")[0]:
                        score[img.split(".")[0]] = 1
                    else:
                        score[img.split(".")[0]] = 0

                res[(p1, p2, p3, p4)] = score
                print(p1, p2, p3, p4, sum(list(score.values())))


pd.DataFrame.from_dict(res, orient="index").to_csv("./results.csv")
print(res)