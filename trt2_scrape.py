import base64
from io import BytesIO
from PIL import Image
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

from urllib.parse import urlparse, parse_qs

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'

class SessaoJurisprudencia:
    def __init__(self):
        self.browser = None
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None

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
                EC.presence_of_element_located((By.TAG_NAME, 'img'))
            )
            img_src = img_element.get_attribute('src=')
            
            if img_src:
                print(f"Imagem encontrada: {img_src}")
                if img_src.startswith('data:image'):
                    self.converter_base64_para_jpeg(img_src)
                else:
                    print("A imagem não é base64.")
                return img_src
            else:
                print("A imagem não possui o atributo 'src'.")
                return None
        except Exception as e:
            print(f"Erro ao obter a imagem: {e}")
            return None

    def converter_base64_para_jpeg(self, base64_string, captcha="imagem_captcha.jpeg"):
        """Converter uma string base64 para um arquivo JPEG"""
        try:
            if base64_string.startswith('data:image'):
                base64_string = base64_string.split(',')[1]

            imagem_binaria = base64.b64decode(base64_string)

            imagem = Image.open(BytesIO(imagem_binaria))

            imagem.save(captcha, "JPEG")
            print(f"Imagem salva como {captcha}")
        except Exception as e:
            print(f"Erro ao converter base64 para JPEG: {e}")

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
                url_final = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
                print(f"\nFazendo requisição com URL: {url_final}")
                resposta = self.fazer_requisicao_com_headers(url_final)
            
                with open("resposta_token.txt", "w") as arquivo:
                    arquivo.write(f"Token: {self.token_desafio}\n")
                    arquivo.write(f"Resposta do Captcha: {self.resposta_captcha}\n")
                    if resposta:
                        arquivo.write(f"Status da Resposta: {resposta.status_code}\n")
                        arquivo.write("Cabeçalhos da Resposta:\n")
                        arquivo.write(f"Link da imagem Captcha: {resposta.obter_imagem_div}\n")
                        arquivo.write(json.dumps(dict(resposta.headers), indent=2) + "\n")
                        arquivo.write("Conteúdo da Resposta:\n")
                        arquivo.write(resposta.text[:500] + "\n")  

            img_src = self.obter_imagem_div()
            if img_src:
                print(f"URL da imagem extraída: {img_src}")
            else:
                print("Imagem não encontrada.")
                
        except Exception as e:
            print(f"\nErro durante a sessão: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            input("\nPressione Enter para fechar o navegador...")
            if self.browser:
                self.browser.quit()

def main():
    sessao = SessaoJurisprudencia()
    sessao.iniciar_sessao()

if __name__ == "__main__":
    main()
