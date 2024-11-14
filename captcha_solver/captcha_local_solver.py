import os
import string
import random
import numpy
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter
import pytesseract
import numpy as np

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

F_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(F_PATH, "..", "temp")
IMG_UNIQUE_ID = "".join(random.choices(string.digits, k=6))
IMG_ORIGINAL_PATH = os.path.join(IMG_PATH, f"original_{IMG_UNIQUE_ID}.png")
IMG_FILTERED_PATH = os.path.join(IMG_PATH, f"filtered_{IMG_UNIQUE_ID}.png")
IMG_FINAL_PATH = os.path.join(IMG_PATH, f"final_{IMG_UNIQUE_ID}.png")
if not os.path.exists(IMG_PATH):
    os.mkdir(IMG_PATH)


def solve_captcha_local(image_path, th1: int = 185, th2: int = 110, sig1: float = 1.0, sig2: float = 1.2) -> str:
    """ Solves captcha

    Args:
        image_path: path to the captcha to solve
        th1: Theshold to erase before blur
        th2: Theshold to erase after blur
        sig1: blurring power
        sig2: blurring power 2
    
    Returns:
        captcha response
    """
    original = Image.open(image_path)  
    original.save(IMG_ORIGINAL_PATH)  

    black_and_white = original.convert("L")  # converting to black and white
    first_threshold = black_and_white.point(lambda p: p > th1 and 255)
    blur = numpy.array(first_threshold)  # create an image array
    blurred = gaussian_filter(blur, sigma=sig1)
    blurred = Image.fromarray(blurred)
    final = blurred.point(lambda p: p > th2 and 255)
    final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final = final.filter(ImageFilter.SHARPEN)
    final.save(IMG_FILTERED_PATH)

    blur2 = numpy.array(final)  # create an image array
    blurred2 = gaussian_filter(blur2, sigma=sig2)
    blurred2 = Image.fromarray(blurred2)
    final2 = blurred2.point(lambda p: p > th2 and 255)
    final2 = final2.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final2 = final2.filter(ImageFilter.SHARPEN)
    final2.save(IMG_FINAL_PATH)

    ocr_config = '--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvxwyz'
    number = pytesseract.image_to_string(Image.open(IMG_FINAL_PATH), config=ocr_config)
    number = number.strip().lstrip().rstrip().replace(chr(32), "").replace("\n", "")

    if len(number) != 6:
        number = pytesseract.image_to_string(Image.open(IMG_FILTERED_PATH), config=ocr_config)
        number = number.strip().lstrip().rstrip().replace(chr(32), "").replace("\n", "")

    return number


def grid_search(image_path):
    thresholds = [(180, 135), (160, 125), (170, 130),(150, 120)]
    sigmas = [1.0, 2.5,3.0,3.5]
    resize_dims = [(2500, 750), (3500, 1050), (1500, 720),(4000,1250),(2000,920)]

    best_number = ""
    best_params = None
    best_confidence = 0  
    best_accuracy = 0  

    for th1, th2 in thresholds:
        for sig in sigmas:
            for resize_dim in resize_dims:
                print(f"testing with th1={th1}, th2={th2}, sigma={sig}, resize_dim={resize_dim}")
                number, confidence = solve_captcha_local(image_path, th1, th2, sig, resize_dim)
                print(f"result: {number} with confidence {confidence}")

                if len(number) == 6 and confidence > best_confidence:
                    best_confidence = confidence
                    best_number = number
                    best_params = (th1, th2, sig, resize_dim)

                if len(number) == 6 and len(number) > best_accuracy:
                    best_accuracy = len(number)
                    best_number = number
                    best_params = (th1, th2, sig, resize_dim)

    return best_number, best_params, best_confidence, best_accuracy


def save_best_params_to_file(best_number, best_params, best_confidence, best_accuracy):
    best_params_file = os.path.join(F_PATH, "best_params.txt")
    
    with open(best_params_file, "w") as file:
        file.write(f"best recognized number: {best_number}\n")
        file.write(f"best parameters:\n")
        file.write(f"  threshold 1: {best_params[0]}\n")
        file.write(f"  threshold 2: {best_params[1]}\n")
        file.write(f"  sigma: {best_params[2]}\n")
        file.write(f"  resize Dimensions: {best_params[3]}\n")
        file.write(f"best confidence: {best_confidence}\n")
        file.write(f"best accuracy (Number Length): {best_accuracy}\n")

    print(f"Best parameters and result saved to {best_params_file}")


if __name__ == "__main__":
    image_path = "captcha_solver/teste.png"
    best_number, best_params, best_confidence, best_accuracy = grid_search(image_path)
    print(f"Best result: {best_number} with parameters {best_params}")
    print(f"Best confidence: {best_confidence}")
    print(f"Best accuracy (number length): {best_accuracy}")

    save_best_params_to_file(best_number, best_params, best_confidence, best_accuracy)
