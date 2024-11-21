import base64
import time
import json
import csv
from io import BytesIO
from PIL import Image
import requests
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

    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converter base64 para JPEG e salvar com nome baseado no captcha"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))
            captcha_nome = f"{self.resposta_captcha}.jpeg" if self.resposta_captcha else captcha_nome
            imagem.save(captcha_nome, "JPEG")
            print(f"Imagem salva como {captcha_nome}")
        except Exception as e:
            print(f"Erro ao converter base64 para JPEG: {e}")

    def coletar_dados_xpaths(self):
        """Coletar dados dos XPaths"""
        dados = []
        i = 1  
        try:
            while True:  
                xpath_base = f"/html/body/app-root/app-documentos-busca/div[2]/mat-list/mat-list-item[{i}]/div/div[2]"
                try:
                    dados.append([
                        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.XPATH, f"{xpath_base}//div[1]/a"))).get_attribute("href"),  # Inteiro Teor Link
                        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.XPATH, f"{xpath_base}/div[1]/h4/a"))).text,  # Processo
                        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.XPATH, f"{xpath_base}/p[1]"))).text,  # Estágio
                        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.XPATH, f"{xpath_base}/p[2]"))).text,  # Órgão
                        WebDriverWait(self.browser, 15).until(EC.visibility_of_element_located((By.XPATH, f"{xpath_base}/p[4]"))).text,  # Amostras
                    ])
                except Exception as e:
                    print(f"Erro ao processar item {i}: {e}")
                
                i += 1  
                if i > 100:  
                    i = 1  
                    print("Reiniciando coleta...")
                    
                if len(dados) >= 100:  
                    break
        except Exception as e:
            print(f"Erro ao coletar dados: {e}")
        return dados

    def salvar_dados_em_csv(self, nome_arquivo="dados_jurisprudencia_PJE.csv"):
        """Salvar dados em CSV sem sobrescrever"""
        try:
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as file:  
                writer = csv.writer(file, delimiter=';')
                if file.tell() == 0: 
                    writer.writerow(['Inteiro Teor','Título', 'Estágio', 'Órgão', 'Amostras'])
                writer.writerows(self.dados_coletados)
            print(f"Dados salvos em {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar dados em CSV: {e}")

    def fazer_requisicao_com_headers(self, url):
        """Fazer requisição com cabeçalhos"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
            'Referer': URL_BASE,
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            resposta = self.sessao.get(url, headers=headers)
            print(f"Status: {resposta.status_code}\nResposta: {resposta.text[:500]}")
            return resposta
        except Exception as e:
            print(f"Erro na requisição: {e}")

    def aguardar_token_na_pagina(self, timeout=30):
        """Aguardar e extrair token e processar resposta do captcha"""
        inicio = time.time()
        while time.time() - inicio < timeout:
            try:
                fonte_pagina = self.browser.page_source
                if 'tokenDesafio' in fonte_pagina:
                    print("Token encontrado na página.")
                url_token = self.obter_requisicoes_rede()
                if url_token:
                    parametros = parse_qs(urlparse(url_token).query)
                    token = parametros.get('tokenDesafio', [None])[0]
                    if token:
                        self.token_desafio = token
                        self.resposta_captcha = url_token[-6:]
                        print(f"Token coletado: {token}")
                        print(f"Resposta do captcha (últimos 6 dígitos): {self.resposta_captcha}")
                        return token
                    else:
                        print("TokenDesafio não encontrado nos parâmetros da URL.")
                time.sleep(1)
            except Exception as e:
                print(f"Erro ao aguardar token: {e}")
        print("Tempo esgotado aguardando token")
        return None
    
    def obter_requisicoes_rede(self):
        """Obter requisições contendo 'tokenDesafio'"""
        try:
            logs = self.browser.get_log('performance')
            for entrada in logs:
                url = json.loads(entrada.get('message', {})).get('message', {}).get('params', {}).get('request', {}).get('url', '')
                if 'tokenDesafio' in url:
                    print(f"URL de token: {url}")
                    return url
        except Exception as e:
            print(f"Erro ao obter requisições: {e}")
        return None
    
    def clicar_botao(self):
        """Botão a ser clicado primeiro"""
        try:
            botao_primeiro_xpath = "/html/body/app-root/app-documentos-busca/div[2]/div/mat-paginator/div/div/div[1]/mat-form-field/div/div[1]/div/mat-select/div/div[2]"
            botao_primeiro = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, botao_primeiro_xpath))
            )
            botao_primeiro.click()
            print(f"Botão clicado.")
        except Exception as e: 
            print(f"Erro ao clicar no Botão:")

    def esperar_e_clicar_botao(self):
        """Esperar pelo clique do botão depois de capturar a resposta do captcha"""
        try:  
            botao_xpath = "/html/body/div[3]/div[2]/div/div/div/mat-option[4]/span"
            botao = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable((By.XPATH, botao_xpath))
            )
            botao.click()
            print("Botão 100 clicado.")
        except Exception as e:
            print(f"Erro ao clicar no botão 100: {e}")

    def clicar_botao_seguinte(self):
        """Esperar o botão Seguinte ser clicado várias vezes"""
        botao_seguinte_xpath = "/html/body/app-root/app-documentos-busca/div[2]/div/mat-paginator/div/div/div[2]/button[2]"
        
        for tentativa in range(5):  
            try:
                botao_seguinte = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable((By.XPATH, botao_seguinte_xpath))
                )
                botao_seguinte.click()
                print(f"Clicando no botão 'Seguinte' tentativa {tentativa+1}")
                break
            except Exception as e:
                print(f"Erro ao clicar no botão 'Seguinte' tentativa {tentativa+1}: {e}")
        
    def iniciar_sessao(self):
        """Iniciar a sessão no navegador"""
        try:
            print("Iniciando sessão...")
            self.configurar_browser()
            self.browser.get(URL_BASE)
            time.sleep(5)
            cookies = self.browser.get_cookies()
            for cookie in cookies:
                self.sessao.cookies.set(cookie['name'], cookie['value'])
            
            self.obter_imagem_div()
            self.token_desafio = self.aguardar_token_na_pagina()
            
            if self.token_desafio:
                
                if self.img_src:
                    self.converter_base64_para_jpeg(self.img_src)
                    self.clicar_botao()    
                
                self.esperar_e_clicar_botao()

                for _ in range(2):  
                    dados = self.coletar_dados_xpaths()
                    self.dados_coletados.extend(dados)  
                    self.clicar_botao_seguinte()  
                    time.sleep(2)  
                
               
                self.salvar_dados_em_csv() 
        
        except Exception as e:
            print(f"Erro ao iniciar a sessão: {e}")

sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
