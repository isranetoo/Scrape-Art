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
        self.token_desafio = self.resposta_captcha = self.assunto_de_interesse = self.numero_de_pagina = self.url_post = None
        self.cookies = {}

    def gerar_timestamp(self):
        return datetime.now().isoformat()

    def obter_entrada(self, prompt):
        return input(prompt)

    def fazer_requisicao_captcha(self):
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers=self.headers())
            resposta.raise_for_status()
            dados = resposta.json()
            base64_img = dados.get("imagem")
            if base64_img:
                self.token_desafio = dados.get("tokenDesafio")
                self.resolver_captcha(base64_img)
            else:
                print("Nenhum campo de imagem encontrado no JSON")
        except Exception as e:
            print(f"Erro ao buscar CAPTCHA: {e}")

    def resolver_captcha(self, base64_string):
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            self.url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
            self.coletar_e_configurar_cookies()
            print(f"Resposta do CAPTCHA: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver CAPTCHA: {e}")

    def coletar_e_configurar_cookies(self):
        self.cookies = {
            "_ga": "GA1.3.2135935613.1731417901",
            "_ga_9GSME7063L": "GS1.1.1731436526.3.0.1731436545.0.0.0",
            "exibirajuda": "true",
            "respostaDesafio": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
        }
        self.sessao.cookies.update(self.cookies)
        self.salvar_arquivo(self.cookies, "cookies", "cookies.json", "Cookies")

    def salvar_arquivo(self, conteudo, pasta, nome_arquivo, tipo):
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
                print(f"{tipo} salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar {tipo}: {e}")

    def enviar_documento(self, pagina):
        if not self.url_post:
            print("URL de POST não definida. Tentando gerar novo CAPTCHA.")
            return False

        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "andField": [self.assunto_de_interesse],
            "paginationPosition": pagina,
            "paginationSize": self.numero_de_pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
        }
        try:
            resposta = self.sessao.post(self.url_post, json=payload, headers=self.headers(), cookies=self.cookies)
            timestamp = datetime.now().strftime("%d-%m-%Y")
            if resposta.status_code == 200:
                documentos = resposta.json()
                if documentos.get("mensagem") == "A resposta informada é incorreta":
                    print("Resposta do CAPTCHA incorreta. Gerando novo CAPTCHA...")
                    self.url_post = None
                    return False
                self.salvar_arquivo(documentos, "documentos", f"assunto_{self.assunto_de_interesse}_pagina_{pagina}_data_{timestamp}_num_{self.numero_de_pagina}.json", "Documentos")
                return True
            else:
                print(f"Erro ao enviar documento: {resposta.status_code} - {resposta.text}")
                self.url_post = None
                return False
        except Exception as e:
            print(f"Erro ao enviar documento: {e}")
            self.url_post = None
            return False

    def iniciar_sessao(self):
        self.numero_de_pagina = self.obter_entrada("Digite o número de processos por página: ")
        self.assunto_de_interesse = self.obter_entrada("Digite o assunto de interesse: ")
        print("==== Iniciando a Sessão ====")
        for pagina in range(1, 41):
            if not self.url_post:
                self.fazer_requisicao_captcha()
            if self.url_post and self.enviar_documento(pagina):
                print(f"Página {pagina} processada com sucesso.")
            else:
                print(f"Erro ao processar a página {pagina}. Tentando novamente...")
        print("==== Sessão finalizada ====")

    def headers(self):
        return {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        }

if __name__ == "__main__":
    SessaoJurisprudencia().iniciar_sessao()
