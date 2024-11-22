import base64
import os
import time
import json
import csv
from io import BytesIO
from PIL import Image
import requests
from captcha_local_solver import solve_captcha_local
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.browser = None
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.img_src = None
        self.dados_coletados = []  

    def configurar_browser(self):
        """Configurar o navegador Chrome"""
        opcoes = webdriver.ChromeOptions()
        opcoes.add_argument('--start-maximized')
        opcoes.add_argument('--ignore-certificate-errors')
        opcoes.add_argument('--ignore-ssl-errors')
        opcoes.set_capability("goog:loggingPrefs", {"browser": "ALL", "performance": "ALL"})
        self.browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opcoes)

    def obter_imagem_div(self):
        """Obter link da imagem do Captcha"""
        try:
            form = WebDriverWait(self.browser, 30).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="imagemCaptcha"]'))
            )
            img_element = WebDriverWait(form, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-documentos-busca/app-captcha/div/div/div/div/form/img'))
            )
            self.img_src = img_element.get_attribute('src') or None
            print(f"Imagem encontrada: {self.img_src}" if self.img_src else "A imagem não possui 'src'.")
        except Exception as e:
            print(f"Erro ao obter a imagem: {e}")

    def rodar_captcha(self, base64_string):
        """Executa o script do Captcha e preenche o campo de input com a resposta"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do captcha obtida: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao rodar captcha: {e}")

    def input_captcha(self):
        """Insere a resposta do Captcha no campo de input"""
        try:
            input_captcha_element = WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-documentos-busca/app-captcha/div/div/div/div/form/mat-form-field/div/div[1]/div/input'))
            )
            input_captcha_element.clear() 
            input_captcha_element.send_keys(self.resposta_captcha)  
            print(f"Resposta do captcha inserida: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao preencher o campo do captcha: {e}")

    def clique_enviar_captcha(self):
        """Clicando para enviar o captcha"""
        try:
            clique_enviar_xpath = "/html/body/app-root/app-documentos-busca/app-captcha/div/div/div/div/form/button[2]"
            clique_enviar = WebDriverWait(self.browser, 15).until(
                EC.element_to_be_clickable((By.XPATH, clique_enviar_xpath))
            )
            clique_enviar.click()
            print(f"Clique do Captcha")
            return True
        except Exception as e:
            print(f"Erro ao clicar em enviar o captcha: {e}")
            return False

    def resolver_captcha(self):
        """Loop para tentar resolver o captcha até obter sucesso."""
        sucesso = False
        while not sucesso:
            try:

                self.obter_imagem_div()
                if not self.img_src:
                    print("Aguardando imagem do Captcha...")
                    time.sleep(2)
                    continue

                self.rodar_captcha(self.img_src)
                if not self.resposta_captcha:
                    print("Aguardando resposta do Captcha...")
                    time.sleep(2)
                    continue


                self.input_captcha()

                sucesso = self.clique_enviar_captcha()

                if sucesso:
                    print("Captcha resolvido com sucesso.")
                else:
                    print("Captcha não resolvido. Tentando novamente...")
                    time.sleep(2)

            except Exception as e:
                print(f"Erro no processo de resolver Captcha: {e}")
                time.sleep(2)

    def iniciar_sessao(self):
        """Iniciar a sessão no navegador"""
        try:
            print("Iniciando sessão...")
            self.configurar_browser()
            self.browser.get(URL_BASE)
            time.sleep(5)

            self.resolver_captcha()

            self.token_desafio = self.aguardar_token_na_pagina()
            if self.token_desafio:
                print(f"Token desafio obtido: {self.token_desafio}")
            else:
                print("Não foi possível obter o token desafio.")

        except Exception as e:
            print(f"Erro ao iniciar a sessão: {e}")

sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
