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

# URLs base
URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'

class SessaoJurisprudencia:
    def __init__(self):
        self.browser = None
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.img_src = None

    def configurar_browser(self):
        """Configurar o navegador Chrome com as opções apropriadas"""
        opcoes = webdriver.ChromeOptions()
        opcoes.add_argument('--start-maximized')
        opcoes.add_argument('--ignore-certificate-errors')
        opcoes.add_argument('--ignore-ssl-errors')
        opcoes.set_capability(
            "goog:loggingPrefs",
            {
                "browser": "ALL",
                "performance": "ALL",
            }
        )
        
        servico = Service(ChromeDriverManager().install())
        
        try:
            self.browser = webdriver.Chrome(
                service=servico,
                options=opcoes
            )
            print("Configuração do navegador bem-sucedida")
        except Exception as e:
            print(f"Erro ao configurar o navegador: {e}")
            raise

    def obter_imagem_div(self):
        """Coletar o link da imagem do Captcha"""
        try:
            form_element = WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located((By.XPATH, '//*[@id="imagemCaptcha"]'))
            )
            img_element = WebDriverWait(form_element, 10).until(
                EC.presence_of_element_located((By.XPATH, '/html/body/app-root/app-documentos-busca/app-captcha/div/div/div/div/form/img'))
            )

            img_src = img_element.get_attribute('src')

            if img_src:
                print(f"Imagem encontrada: {img_src}")
                self.img_src = img_src  
            else:
                print("A imagem não possui o atributo 'src'.")
                self.img_src = None
        except Exception as e:
            print(f"Erro ao obter a imagem: {e}")
            self.img_src = None

    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converter uma string base64 para um arquivo JPEG"""
        try:
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]

            imagem_binaria = base64.b64decode(base64_string)

            imagem = Image.open(BytesIO(imagem_binaria))
            if self.resposta_captcha:
                captcha_nome = f"{self.resposta_captcha}.jpeg"
            imagem.save(captcha_nome, "JPEG")
            print(f"Imagem salva como {captcha_nome}")
        except Exception as e:
            print(f"Erro ao converter base64 para JPEG: {e}")

    def coletar_dados_xpaths(self):
        """Coletar os dados dos XPaths e retorná-los em um formato estruturado"""
        dados = []

        try:
            for i in range(1, 99): 
                titulo_xpath = f"/html/body/app-root/app-documentos-busca/div[2]/mat-list/mat-list-item[{i}]/div/div[2]/div[1]/h4/a"
                estagio_xpath = f"/html/body/app-root/app-documentos-busca/div[2]/mat-list/mat-list-item[{i}]/div/div[2]/p[1]"
                orgao_xpath = f"/html/body/app-root/app-documentos-busca/div[2]/mat-list/mat-list-item[{i}]/div/div[2]/p[2]"
                amostras_xpath = f"/html/body/app-root/app-documentos-busca/div[2]/mat-list/mat-list-item[{i}]/div/div[2]/p[4]"
                      
                titulo = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.XPATH, titulo_xpath))
                ).text
                estagio = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.XPATH, estagio_xpath))
                ).text
                orgao = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.XPATH, orgao_xpath))
                ).text
                
                amostras = WebDriverWait(self.browser, 15).until(
                    EC.visibility_of_element_located((By.XPATH, amostras_xpath))
                ).text

                dados.append([titulo, estagio, orgao, amostras])
        except Exception as e:
            print(f"Erro ao coletar os dados dos XPaths: {e}")

        return dados

    def salvar_dados_em_csv(self, dados, nome_arquivo="dados_jurisprudencia.csv"):
        """Salvar os dados coletados em um arquivo CSV"""
        try:
            with open(nome_arquivo, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow(['Título', 'Estágio do Processo', 'Órgão Julgador', 'Ementa', 'Amostras do Inteiro Teor'])
                for linha in dados:
                    writer.writerow(linha)
            print(f"Dados salvos em {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar os dados em CSV: {e}")

    def fazer_requisicao_com_headers(self, url):
        """Fazer uma requisição com os cabeçalhos adequados"""
        cabecalhos = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
            'Referer': URL_BASE,
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            resposta = self.sessao.get(url, headers=cabecalhos)
            print(f"\nURL de Requisição: {url}")
            print(f"Status da Resposta: {resposta.status_code}")
            print(f"Cabeçalhos da Resposta: {dict(resposta.headers)}")
            print(f"Conteúdo da Resposta: {resposta.text[:500]}")
            return resposta
        except Exception as e:
            print(f"Erro ao fazer a requisição: {e}")
            return None

    def aguardar_token_na_pagina(self, timeout=30):
        """Aguardar e extrair o token da página ou das requisições de rede"""
        inicio = time.time()
        while time.time() - inicio < timeout:
            try:
                fonte_pagina = self.browser.page_source
                if 'tokenDesafio' in fonte_pagina:
                    print("Token encontrado na fonte da página")
                
                url_token = self.obter_requisicoes_rede()
                if url_token:
                    analisado = urlparse(url_token)
                    parametros = parse_qs(analisado.query)
                    if 'tokenDesafio' in parametros:
                        return parametros['tokenDesafio'][0]
                
                time.sleep(1)
            except Exception as e:
                print(f"Erro ao aguardar pelo token: {e}")
        
        print("Tempo esgotado aguardando pelo token")
        return None

    def obter_requisicoes_rede(self):
        """Obter todas as requisições de rede contendo 'tokenDesafio'"""
        try:
            logs = self.browser.get_log('performance')
            for entrada in logs:
                dados_log = json.loads(entrada.get('message', {}))
                mensagem = dados_log.get('message', {})
                if mensagem.get('method') == 'Network.requestWillBeSent':
                    requisicao = mensagem.get('params', {}).get('request', {})
                    url = requisicao.get('url', '')
                    if 'tokenDesafio' in url:
                        print(f"URL de token encontrado: {url}")
                        return url
        except Exception as e:
            print(f"Erro ao obter requisições de rede: {e}")
        return None

    def iniciar_sessao(self):
        """Iniciar a sessão no navegador e lidar com o processo de token/captcha"""
        try:
            print("Iniciando nova sessão...")
            self.configurar_browser()
            
            print("Carregando a página...")
            self.browser.get(URL_BASE)
            time.sleep(5)
            
            print("\nExtraindo cookies...")
            cookies = self.browser.get_cookies()
            for cookie in cookies:
                print(f"Cookie: {cookie['name']} = {cookie['value']}")
                self.sessao.cookies.set(cookie['name'], cookie['value'])
            
            print("\nColetando a imagem do CAPTCHA...")
            self.obter_imagem_div()
            if self.img_src:
                print(f"Imagem do CAPTCHA coletada: {self.img_src}")
            else:
                print("Falha ao coletar a imagem do CAPTCHA.")
            
            print("\nAguardando o token aparecer...")
            self.token_desafio = self.aguardar_token_na_pagina()
            if self.token_desafio:
                print(f"\nToken extraído: {self.token_desafio}")
            else:
                print("\nFalha ao extrair o token")
                return
            print("\nPor favor, insira a solução do captcha que você vê no navegador.")
            print("O formato deve ser algo como 'k8fe6w' (6 caracteres)")
            self.resposta_captcha = input("Insira a solução do captcha: ").strip()
            
            if self.token_desafio and self.resposta_captcha:
                if self.img_src:
                    self.converter_base64_para_jpeg(self.img_src)
                
                url_final = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
                print(f"\nFazendo requisição com URL: {url_final}")
                resposta = self.fazer_requisicao_com_headers(url_final)
                
                dados = self.coletar_dados_xpaths()
                self.salvar_dados_em_csv(dados)
            
        except Exception as e:
            print(f"Erro ao iniciar a sessão: {e}")


sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
