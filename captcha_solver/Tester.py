import os
import base64
from io import BytesIO
import pandas as pd
import numpy as np
import pytesseract
from PIL import Image
from PIL import ImageFilter
from scipy.ndimage import gaussian_filter

# Verifica se está executando em um computador Windows e, em caso afirmativo, adiciona o caminho do pytesseract
if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = 'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

def solve_captcha_local(th1, th2, sig1, sig2, bytes_data):
    # Abre a imagem a partir dos dados base64
    original = Image.open(BytesIO(base64.b64decode(bytes_data)))

    # Converte para preto e branco
    black_and_white = original.convert("L")
    first_threshold = black_and_white.point(lambda p: p > th1 and 255)

    # Aplica o filtro gaussiano
    blur = np.array(first_threshold)
    blurred = gaussian_filter(blur, sigma=sig1)
    blurred = Image.fromarray(blurred)
    final = blurred.point(lambda p: p > th2 and 255)
    final = final.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final = final.filter(ImageFilter.SHARPEN)

    # Aplica novamente o filtro gaussiano
    blur2 = np.array(final)
    blurred2 = gaussian_filter(blur2, sigma=sig2)
    blurred2 = Image.fromarray(blurred2)
    final2 = blurred2.point(lambda p: p > th2 and 255)
    final2 = final2.filter(ImageFilter.EDGE_ENHANCE_MORE)
    final2 = final2.filter(ImageFilter.SHARPEN)

    # Configuração do OCR
    ocr_config = '--psm 11 --oem 3 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvxwyz'
    number = pytesseract.image_to_string(final2, config=ocr_config)
    number = number.strip().lstrip().rstrip().replace(chr(32), "").replace("\n", "")

    return number

# Caminho para a pasta de imagens
files = 'C:/Users/techc/OneDrive/Desktop/Artemis/Scrape-Art/captcha_solver/images/'  # Altere para o caminho correto da sua pasta

# Dicionário para armazenar os resultados
res = {}

# Loop para testar diferentes combinações de parâmetros
for p1 in range(100, 200, 5):
    for p2 in range(100, 200, 5):
        for p3 in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]:
            for p4 in [0.7, 0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7]:

                score = {}
                # Verifica todos os arquivos na pasta de imagens
                for img in os.listdir(files):
                    img_path = os.path.join(files, img)

                    # Verifica se o arquivo existe
                    if not os.path.exists(img_path):
                        print(f"Arquivo não encontrado: {img_path}")
                        continue  # Ignora esse arquivo e continua com o próximo

                    # Lê a imagem e tenta resolver o captcha
                    with open(img_path, "rb") as bytes_data:
                        this_pred = solve_captcha_local(p1, p2, p3, p4, base64.b64encode(bytes_data.read()))

                    # Verifica se o resultado do OCR corresponde ao nome do arquivo (sem a extensão)
                    if this_pred == img.split(".")[0]:
                        score[img.split(".")[0]] = 1
                    else:
                        score[img.split(".")[0]] = 0

                # Armazena os resultados para os parâmetros atuais
                res[(p1, p2, p3, p4)] = score
                print(p1, p2, p3, p4, sum(list(score.values())))

# Salva os resultados em um arquivo CSV
pd.DataFrame.from_dict(res, orient="index").to_csv("./results.csv")
print(res)
