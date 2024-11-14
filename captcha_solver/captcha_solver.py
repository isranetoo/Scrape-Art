from datetime import datetime, timezone
from dotenv import load_dotenv
from tqdm import tqdm
from twocaptcha import TwoCaptcha
from twocaptcha.api import NetworkException
from twocaptcha.api import ApiException
import time
import os
import logging
import base64
import json
import numpy as np
import cv2




load_dotenv()

tokenCapchaResposta = "?tokenDesafio=6a356df92482f42786229a90caca36821ee31f5a18c70c12766b94a522b360fba83bfc8219322474237f1a605fac0197e1bf01b8c25016c1f75d2cbc1ba50c2e24e8fa378e0ba06fa0aaf684be3f65527fbbc0044ab74efeb5983b1e599432b1&resposta=YjVtYXdz"
tokenCapcha={}

API_KEY = os.getenv("API_KEY")

solver = TwoCaptcha(API_KEY)

def save_token(token, id_processo, instancia):
    tokenCapcha[str(id_processo)+"-"+str(instancia)] = token
    json_object = json.dumps(tokenCapcha, indent=4)
    with open("./capchaToken.json", "w") as json_token_file:
        json_token_file.write(json_object)

try:
    json_token_file = open("./capchaToken.json", "rb")

    tokenCapcha = json.load(json_token_file)
except:
    save_token('', 'default', 0)

def solve_captcha_api(data_bytes):
    logging.info("Resolvendo capcha via api")
    result = ""

    while result == "":
        try:
            result = solver.normal(data_bytes)['code']
        except NetworkException as e:
            logging.info(f"{e} error2")
            tqdm.write(f"[{datetime.now(timezone.utc)}] 2Captcha api error trying again in {0.5} seconds  {e}")
            time.sleep(0.5)
            continue
        except ApiException as e:
            if "NO_SLOT" in f"{e}":
                
                logging.info(f"{e} error2")
                tqdm.write(f"[{datetime.now(timezone.utc)}] 2Captcha api error [NO_SLOT_AVALIABLE] trying again in {10} seconds  {e}")
                time.sleep(10)
                continue
            else:
                raise e

    return result

def readb64_image_and_show(encoded_data):
   nparr = np.frombuffer(base64.b64decode(encoded_data), np.uint8)
   img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
   cv2.imshow('image',img)
   cv2.waitKey(0)
   cv2.destroyAllWindows()
   return img


def check_solver():
    return solver is not None