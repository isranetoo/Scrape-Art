import os
import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
import requests
from captcha_local_solver import solve_captcha_local

# URLs usadas no processo
URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'


class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None

    def obter_ip_local(self):
        """Obtendo o IP Local"""
        try:
            resposta = requests.get('https://api.ipify.org')
            return resposta.text
        except Exception as e:
            print(f"Erro ao coletar o IP: {e}")
            return "IP não disponível"

    def obter_user_agent(self):
        """Obtendo o User-Agent"""
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

    def gerar_timestamp(self):
        """Gerar o timestamp atual"""
        return datetime.now().isoformat()

    def fazer_requisicao_captcha(self):
        """Faz a requisição inicial para obter o captcha"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': self.obter_user_agent(),
        }
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers=headers)
            resposta.raise_for_status()
            conteudo_json = resposta.json()

            if "imagem" in conteudo_json and conteudo_json["imagem"]:
                base64_img = conteudo_json["imagem"]
                self.token_desafio = conteudo_json.get('tokenDesafio')
                print("Imagem Base64 retirada do Json")
                self.converter_base64_para_jpeg(base64_img)
                self.resolver_captcha(base64_img)
            else:
                print("Nenhum campo de imagem foi encontrado no JSON")
        except Exception as e:
            print(f"Erro ao coletar a imagem JSON: {e}")

    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converte uma imagem Base64 para JPEG"""
        try:
            pasta_imagem = "images"
            os.makedirs(pasta_imagem, exist_ok=True)
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))
            caminho_arquivo = os.path.join(pasta_imagem, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva na pasta Images: {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar a imagem: {e}")

    def resolver_captcha(self, base64_string):
        """Resolve o captcha usando a solução local"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            resposta = solve_captcha_local(base64_string)
            self.resposta_captcha = resposta
            print(f"Resposta do Captcha: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o Captcha: {e}")
            self.resposta_captcha = None

    def enviar_documento(self):
        """Realiza o POST para enviar o documento com o token e a resposta do captcha."""
        if not self.token_desafio or not self.resposta_captcha:
            print("Token de desafio ou resposta do captcha ausente.")
            return

        url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
        print(f"URL montada para o POST: {url_post}")
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "paginationPosition": 1,
            "paginationSize": 20,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao"
        }
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': self.obter_user_agent(),
        }
        try:
            resposta = self.sessao.post(url_post, json=payload, headers=headers)
            print(f"Resposta do servidor: {resposta.status_code} - {resposta.text}")
            if resposta.status_code == 200:
                print("POST realizado com sucesso.")
            else:
                print(f"Erro ao realizar POST: {resposta.status_code} - {resposta.text}")
        except Exception as e:
            print(f"Erro ao enviar o documento: {e}")

    def iniciar_sessao(self):
        """Fluxo principal para iniciar a sessão"""
        try:
            print("Iniciando a Sessão")
            self.fazer_requisicao_captcha()
            if self.token_desafio and self.resposta_captcha:
                self.enviar_documento()
            else:
                print("Erro ao encontrar o token de desafio ou a resposta do captcha.")
        except Exception as e:
            print(f"Erro ao iniciar a Sessão: {e}")


if __name__ == "__main__":
    sessao = SessaoJurisprudencia()
    sessao.iniciar_sessao()
