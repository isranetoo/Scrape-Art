import os
import json
import base64
from io import BytesIO
from PIL import Image
from datetime import datetime
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

    def obter_ip_local(self):
        try:
            resposta = requests.get('https://api.ipify.org')
            return resposta.text
        except Exception as e:
            print(f"Erro ao coletar o IP: {e}")
            return "IP não disponível"

    def obter_user_agent(self):
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"

    def gerar_timestamp(self):
        return datetime.now().isoformat()

    def fazer_requisicao_captcha(self):
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
                self.resolver_captcha(base64_img)
            else:
                print("Nenhum campo de imagem foi encontrado no JSON")
        except Exception as e:
            print(f"Erro ao coletar a imagem JSON: {e}")

    def resolver_captcha(self, base64_string):
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            resposta = solve_captcha_local(base64_string)
            self.resposta_captcha = resposta
            print(f"Resposta do Captcha: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o Captcha: {e}")
            self.resposta_captcha = None

    def enviar_documento(self):
        if not self.token_desafio or not self.resposta_captcha:
            print("Token de desafio ou resposta do captcha ausente.")
            return False

        url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            #"andField": ["arroz"],
            #"assunto": ["Abandono de Emprego [55200]", "Adicional de Horas Extras [55365]" , "Adicional de Horas Extras [13787]"],
            "paginationPosition": 1,
            "paginationSize": 100,
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
            if resposta.status_code == 200:
                documentos = resposta.json()
                self.salvar_documentos(documentos)
                return True
            else:
                print(f"Erro ao realizar POST: {resposta.status_code} - {resposta.text}")
                return False
        except Exception as e:
            print(f"Erro ao enviar o documento: {e}")
            return False

    def salvar_documentos(self, documentos):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_nome = f"documentos_{timestamp}.json"
        pasta = "documentos"
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, arquivo_nome)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(documentos, arquivo, ensure_ascii=False, indent=4)
            print(f"Documentos salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar documentos: {e}")

    def iniciar_sessao(self):
        while True:
            print("Tentando iniciar a sessão...")
            self.fazer_requisicao_captcha()
            if self.token_desafio and self.resposta_captcha:
                sucesso = self.enviar_documento()
                if sucesso:
                    print("Documentos obtidos com sucesso!")
                    break
                else:
                    print("Erro ao obter documentos. Tentando novamente...")
            else:
                print("Erro ao resolver captcha. Tentando novamente...")


if __name__ == "__main__":
    sessao = SessaoJurisprudencia()
    sessao.iniciar_sessao()
