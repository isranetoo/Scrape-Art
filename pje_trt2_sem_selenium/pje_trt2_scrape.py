import json
import os
from datetime import datetime
import requests
from captcha_local_solver import solve_captcha_local

URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.assunto_de_interesse = input("==== Digite o assunto de interesse: ")
        self.numero_de_pagina = input("==== Digite o número de processos por página: ")
        self.url_post = None
        self.cookies = {}

    def gerar_timestamp(self):
        return datetime.now().strftime("%d-%m-%Y_%H-%M-%S")

    def _salvar_em_arquivo(self, dados, pasta, nome_arquivo):
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(dados, arquivo, ensure_ascii=False, indent=4)
                print(f"Dados salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")

    def _configurar_cookies(self):
        self.cookies = {
            "_ga": "GA1.3.2135935613.1731417901",
            "_ga_9GSME7063L": "GS1.1.1731436526.3.0.1731436545.0.0.0",
            "exibirajuda": "true",
            "tokenDesafio": self.token_desafio,
            "respostaDesafio": self.resposta_captcha
        }
        self.sessao.cookies.update(self.cookies)
        self._salvar_em_arquivo(self.cookies, "cookies", "cookies.json")

    def _resolver_captcha(self, base64_string):
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do CAPTCHA: \033[1;32m{self.resposta_captcha}\033[0m")
            self.url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
            self._configurar_cookies()
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")

    def _fazer_requisicao_captcha(self):
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers={'Accept': 'application/json'})
            resposta.raise_for_status()
            conteudo = resposta.json()
            self.token_desafio = conteudo.get('tokenDesafio')
            self._resolver_captcha(conteudo.get("imagem", ""))
        except Exception as e:
            print(f"Erro ao obter CAPTCHA: {e}")

    def _enviar_documento(self, pagina):
        payload = {
            "name": "query parameters",
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "andField": [self.assunto_de_interesse],
            "paginationPosition": pagina,
            "paginationSize": self.numero_de_pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
        }
        try:
            resposta = self.sessao.post(self.url_post, json=payload, headers={'Content-Type': 'application/json'})
            if resposta.status_code == 200:
                documentos = resposta.json()
                if documentos.get("mensagem") == "A resposta informada é incorreta":
                    print("\033[1;31mCAPTCHA incorreto.\033[0m Gerando novo...")
                    self.url_post = None
                    return False
                self._salvar_em_arquivo(documentos, "documentos", f"assunto_{self.assunto_de_interesse}_pagina_{pagina}_data_{self.gerar_timestamp()}.json")
                return True
            print(f"Erro no POST: {resposta.status_code} - {resposta.text}")
        except Exception as e:
            print(f"Erro ao enviar POST: {e}")
        self.url_post = None
        return False

    def iniciar_sessao(self):
        print("==== Iniciando a Sessão ====")
        for pagina in range(1, 16):  
            if not self.url_post:
                self._fazer_requisicao_captcha()
            if self.url_post and self._enviar_documento(pagina):
                print(f"Página {pagina} processada com sucesso.")
            else:
                print(f"Erro ao processar a página {pagina}. Tentando novamente...")
        print("==== Sessão finalizada ====")


if __name__ == "__main__":
    SessaoJurisprudencia().iniciar_sessao()
