import os
import json
import base64
from io import BytesIO
from PIL import Image
import requests
from captcha_local_solver import solve_captcha_local

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None

    def fazer_requisicao_com_headers(self, url):
        """Faz uma requisição com cabeçalhos e trata Base64 de imagens."""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
            'Referer': URL_CAPTCHA,
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            resposta = self.sessao.get(url, headers=headers)
            resposta.raise_for_status()
            try:
                conteudo_json = resposta.json()
                if "imagem" in conteudo_json and conteudo_json["imagem"]:
                    base64_img = conteudo_json["imagem"]
                    self.token_desafio = conteudo_json.get("tokenDesafio")
                    print("Imagem Base64 extraida como JSON.")
                    self.converter_base64_para_jpeg(base64_img)
                    self.resolver_captcha(base64_img)
                else:
                    print("Nenhum campo de Imagem foi encontrado em JSON.")
            except json.JSONDecodeError:
                print(f"Resposta NÃO é em Json: {resposta.text[:500]}")
        except Exception as e:
                print(f"Erro na requisição: {e}")

    def obter_cookies(self, url):
        """Coletando o Cookie da página"""
        try:
            resposta = self.sessao.get(url)
            resposta.raise_for_status()

            cookies = resposta.cookies.get_dict()
            print(f"Cookies coletados: {cookies}")
            return cookies
        except Exception as e:
            print(f"Erro ao coletar o cookies: {e}") 
        

    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converte Base64 para JPEG e salva na pasta 'images'."""
        try:
            pasta_images = "images"
            os.makedirs(pasta_images, exist_ok=True)

            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string

            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))

            caminho_arquivo = os.path.join(pasta_images, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva como {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao converter Base64 para JPEG: {e}")

    def resolver_captcha(self, base64_string):
        """Resolve o captcha localmente."""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do captcha: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o captcha: {e}")

    def enviar_resposta_captcha(self):
        """Envia a resposta do captcha ao servidor."""
        try:
            if not self.resposta_captcha or not self.token_desafio:
                print("Captcha ou Token de desafio ausente")
                return
            
            payload = {"resposta": self.resposta_captcha, "tokenDesafio": self.token_desafio}
            resposta = self.sessao.post(URL_CAPTCHA, json=payload)
            print(f"Resposta do servidor: {resposta.status_code} - {resposta.text}")
        except Exception as e:
            print(f"Erro ao  enviar a resposta do Captcha: {e}")

    def iniciar_sessao(self):
        """Fluxo principal para iniciar a sessão e coletar dados."""
        try:
            print("Iniciando a Sessão")

            cookies = self.obter_cookies(URL_BASE)
            if cookies:
                print(f"Cookies capturados: {cookies}")
            else:
                print("Não foi possível capturar os cookies.")

            self.fazer_requisicao_com_headers(URL_CAPTCHA)

            if self.token_desafio:
                print(f"Token de desafio obtido: {self.token_desafio}")
            else:
                print("Token de desafio não encontrado!")

            self.enviar_resposta_captcha()

            html_final = self.sessao.get(URL_BASE).text
            if html_final:
                print("Sessão inicializada com sucesso.")
            else:
                print("Falha ao carregar a página final.")
        except Exception as e:
            print(f"Erro ao Iniciar a Sessão: {e}")

sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
