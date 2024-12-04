import os
import base64
from io import BytesIO
import pandas as pd
import numpy as np
import pytesseract
from PIL import Image, ImageFilter
from scipy.ndimage import gaussian_filter

# Configura o caminho do Tesseract no Windows
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image, th1, th2, sigma1, sigma2):
    """Processa a imagem para otimização do OCR."""
    # Converte para preto e branco
    gray_image = image.convert("L")
    first_threshold = gray_image.point(lambda p: p > th1 and 255)

    # Primeiro filtro Gaussiano
    blurred = gaussian_filter(np.array(first_threshold), sigma=sigma1)
    blurred_image = Image.fromarray(blurred).point(lambda p: p > th2 and 255)
    processed = blurred_image.filter(ImageFilter.EDGE_ENHANCE_MORE).filter(ImageFilter.SHARPEN)

    # Segundo filtro Gaussiano
    final_blurred = gaussian_filter(np.array(processed), sigma=sigma2)
    final_image = Image.fromarray(final_blurred).point(lambda p: p > th2 and 255)
    return final_image.filter(ImageFilter.EDGE_ENHANCE_MORE).filter(ImageFilter.SHARPEN)

def extract_text_from_image(image, ocr_config):
    """Extrai texto da imagem usando Tesseract OCR."""
    text = pytesseract.image_to_string(image, config=ocr_config)
    return text.strip().replace(" ", "").replace("\n", "")

def solve_captcha_local(th1, th2, sigma1, sigma2, image_data_base64):
    """Resolve o CAPTCHA aplicando preprocessamento e OCR."""
    try:
        # Decodifica a imagem base64
        original_image = Image.open(BytesIO(base64.b64decode(image_data_base64)))
        processed_image = preprocess_image(original_image, th1, th2, sigma1, sigma2)

        # Configuração do OCR
        ocr_config = '--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyz'
        return extract_text_from_image(processed_image, ocr_config)
    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return None

def grid_search_on_images(image_folder, param_ranges):
    """Executa uma busca em grade para encontrar os melhores parâmetros."""
    results = {}

    # Itera por todas as combinações de parâmetros
    for th1 in param_ranges["th1"]:
        for th2 in param_ranges["th2"]:
            for sigma1 in param_ranges["sigma1"]:
                for sigma2 in param_ranges["sigma2"]:
                    scores = {}
                    
                    for img_file in os.listdir(image_folder):
                        img_path = os.path.join(image_folder, img_file)
                        
                        if not os.path.isfile(img_path):
                            print(f"Arquivo ignorado (não é um arquivo): {img_path}")
                            continue

                        # Lê o conteúdo do arquivo como base64
                        with open(img_path, "rb") as f:
                            img_base64 = base64.b64encode(f.read())

                        prediction = solve_captcha_local(th1, th2, sigma1, sigma2, img_base64)
                        expected = os.path.splitext(img_file)[0]  # Nome do arquivo sem extensão
                        
                        # Avalia se o OCR acertou
                        scores[expected] = 1 if prediction == expected else 0

                    # Armazena os resultados
                    results[(th1, th2, sigma1, sigma2)] = scores
                    accuracy = sum(scores.values())
                    if accuracy >= 51:
                        print(f"Parâmetros: {th1}, {th2}, {sigma1}, {sigma2} - Acertos: \033[1;32m{accuracy}\033[0m")
                    else:
                        print(f"Parâmetros: {th1}, {th2}, {sigma1}, {sigma2} - Acertos: \033[1;31m{accuracy}\033[0m")
                    
    
    return results

# Configurações e execução
if __name__ == "__main__":
    image_folder = r'C:/Users/IsraelAntunes/Desktop/Scrape-Art/Grid Search/images'  # Ajuste para o caminho correto
    param_ranges = {
        "th1": range(185, 190, 5),
        "th2": range(145, 160, 5),
        "sigma1": [1.0, 1.1, 1.2, 1.3],
        "sigma2": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5],
    }

    # Executa a busca em grade
    results = grid_search_on_images(image_folder, param_ranges)

    # Salva os resultados em CSV
    pd.DataFrame.from_dict(results, orient="index").to_csv("./results.csv")
    print("Resultados salvos em './results.csv'")
