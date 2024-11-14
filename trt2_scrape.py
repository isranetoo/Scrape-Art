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

        src="data:image/png;base64, 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"
        
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
                        arquivo.write(json.dumps(dict(resposta.headers), indent=2) + "\n")
                        arquivo.write("Conteúdo da Resposta:\n")
                        arquivo.write(resposta.text[:500] + "\n")  
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
