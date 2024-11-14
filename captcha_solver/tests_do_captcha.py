import os
import string
import random
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter
import pytesseract
import numpy as np

# Definir o caminho para o executável do Tesseract, se necessário
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

# Caminhos para salvar as imagens processadas
F_PATH = os.path.dirname(__file__)
IMG_PATH = os.path.join(F_PATH, "..", "temp")
IMG_UNIQUE_ID = "".join(random.choices(string.digits, k=6))
IMG_ORIGINAL_PATH = os.path.join(IMG_PATH, f"original_{IMG_UNIQUE_ID}.png")
IMG_FILTERED_PATH = os.path.join(IMG_PATH, f"filtered_{IMG_UNIQUE_ID}.png")
IMG_FINAL_PATH = os.path.join(IMG_PATH, f"final_{IMG_UNIQUE_ID}.png")

if not os.path.exists(IMG_PATH):
    os.mkdir(IMG_PATH)

def solve_captcha_local(image_path, th1, th2, sig, resize_dim):
    """
    Função para resolver o CAPTCHA, extraindo um código alfanumérico de 6 caracteres.
    Realiza o processamento da imagem e OCR com base nos parâmetros fornecidos.
    """
    original = Image.open(image_path)
    original.save(IMG_ORIGINAL_PATH)
    
    # Converter para escala de cinza
    gray = original.convert("L")

    # Aplicar thresholding
    thresholded = gray.point(lambda p: p > th1 and 255)

    # Aplicar desfoque gaussiano
    blurred = gaussian_filter(np.array(thresholded), sigma=sig)
    blurred = Image.fromarray(blurred)

    # Aplicar outro threshold após o desfoque
    final = blurred.point(lambda p: p > th2 and 255)
    
    # Melhorar bordas e nitidez
    final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final = final.filter(ImageFilter.SHARPEN)
    final.save(IMG_FILTERED_PATH)

    # Redimensionar a imagem
    final_resized = final.resize(resize_dim)
    final_resized = final_resized.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final_resized = final_resized.filter(ImageFilter.SHARPEN)
    final_resized.save(IMG_FINAL_PATH)


    custom_oem_psm_config = r'--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    

    ocr_result = pytesseract.image_to_string(final_resized, config=custom_oem_psm_config)

    number = ocr_result.strip().replace(" ", "").replace("\n", "")


    if len(number) == 6 and all(c.isalnum() for c in number):
        return number
    else:

        number = pytesseract.image_to_string(final, config=custom_oem_psm_config).strip().replace(" ", "").replace("\n", "")
        if len(number) == 6 and all(c.isalnum() for c in number):
            return number

    return None  

def grid_search(image_path):
    """
    Função para realizar uma busca em grid por diferentes combinações de parâmetros
    (thresholding, sigma de desfoque e dimensões de redimensionamento) para otimizar a extração do código.
    """
    thresholds = [(150, 120), (160, 125), (170, 130)]  
    sigmas = [1.5, 2.0, 2.5]  
    resize_dims = [(3000, 900), (2500, 750), (3500, 1050)]  

    best_number = ""
    best_params = None

    for th1, th2 in thresholds:
        for sig in sigmas:
            for resize_dim in resize_dims:
                print(f"Testing with th1={th1}, th2={th2}, sigma={sig}, resize_dim={resize_dim}")
                number = solve_captcha_local(image_path, th1, th2, sig, resize_dim)
                
                if number:
                    print(f"Result: {number}")
                    if len(number) == 6 and all(c.isalnum() for c in number):
                        best_number = number
                        best_params = (th1, th2, sig, resize_dim)

    return best_number, best_params

def save_best_params(best_params, file_path="best_params.txt"):
    """
    Função para salvar os melhores parâmetros em um arquivo de texto.
    """
    if best_params:
        with open(file_path, "w") as file:
            file.write(f"Best Parameters:\n")
            file.write(f"Threshold 1: {best_params[0]}\n")
            file.write(f"Threshold 2: {best_params[1]}\n")
            file.write(f"Sigma: {best_params[2]}\n")
            file.write(f"Resize Dimensions: {best_params[3]}\n")
            print(f"Melhores parâmetros salvos em {file_path}")
    else:
        print("Não há parâmetros para salvar.")

if __name__ == "__main__":

    image_path = "teste.png" 

    best_number, best_params = grid_search(image_path)

    if best_number:
        print(f"Melhor código extraído: {best_number}")
        print(f"Melhores parâmetros: {best_params}")

        save_best_params(best_params)
    else:
        print("Não foi possível extrair um código válido.")
