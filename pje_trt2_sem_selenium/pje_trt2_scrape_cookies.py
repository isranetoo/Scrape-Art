import json
from datetime import datetime
import requests
from captcha_local_solver import solve_captcha_local
import os

URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.assunto_de_interesse = None
        self.numero_de_pagina = None
        self.url_post = None
        self.cookies = {}

    def num_pagina(self):
        self.numero_de_pagina = input("==== Digite o número de processos por página: ")

    def assunto_interesse(self):
        self.assunto_de_interesse = input("==== Digite o assunto de interesse: ")

    def gerar_timestamp(self):
        return datetime.now().isoformat()

    def fazer_requisicao_captcha(self):
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
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
            print(f"Erro ao encontrar a imagem no JSON: {e}")

    def resolver_captcha(self, base64_string):
        """Resolvendo CAPTCHA com o solve_captcha_local"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            resposta = solve_captcha_local(base64_string)
            self.resposta_captcha = resposta
            print(f"Resposta do CAPTCHA: \033[1;32m{self.resposta_captcha}\033[0m")
            self.url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
            self.coletar_e_configurar_cookies()
        except Exception as e:
            print(f"\033[1;31mErro ao resolver o CAPTCHA: {e}\033[0m")
            self.resposta_captcha = None

    def coletar_e_configurar_cookies(self):
        """Coleta e configura os cookies para a sessão"""
        try:
            self.cookies = {
                "_ga": "GA1.3.2135935613.1731417901",
                "_ga_9GSME7063L": "GS1.1.1731436526.3.0.1731436545.0.0.0",
                "exibirajuda": "true",
                "tokenDesafio": self.token_desafio,
                "respostaDesafio": self.resposta_captcha
            }
            self.sessao.cookies.update(self.cookies)
            self.salvar_cookies()
            print(f"Cookies configurados com sucesso: \033[1;34m{self.cookies}\033[0m")
        except Exception as e:
            print(f"\033[1;31mErro ao configurar os cookies:\033[0m {e}")

    def salvar_cookies(self):
        """Salvando os cookies em um arquivo .json"""
        pasta = "cookies"
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, "cookies.json")
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                if self.cookies:
                    json.dump(self.cookies, arquivo, ensure_ascii=False, indent=4)
                    print(f"Cookies salvos em: {caminho}")
                else:
                    arquivo.write("Nenhum cookie foi armazenado.")
                    print(f"\033[1;31mCookies não encontrados. Arquivo salvo vazio em:\033[0m {caminho}")
        except Exception as e:
            print(f"Erro ao salvar os cookies: {e}")

    def enviar_documento(self, pagina):
        """Enviando o documento (POST) utilizando os cookies configurados"""
        if not self.url_post:
            print("URL de POST não está definida. Tentando gerar um novo CAPTCHA.")
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
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
            'Cookie': "; ".join([f"{key}={value}" for key, value in self.cookies.items()])  
        }
        try:
            resposta = self.sessao.post(self.url_post, json=payload, headers=headers, cookies=self.cookies)
            if resposta.status_code == 200:
                documentos = resposta.json()
                if "mensagem" in documentos and documentos["mensagem"] == "A resposta informada é incorreta":
                    print("\033[1;31mResposta do CAPTCHA incorreta.\033[0m Gerando novo CAPTCHA...")
                    self.cookies = None
                    return False
                else:
                    self.salvar_documentos(documentos, pagina)
                    return True
            else:
                print(f"Erro ao realizar o POST: {resposta.status_code} - {resposta.text}")
                self.cookies = None
                return False
        except Exception as e:
            print(f"Erro ao enviar o POST: {e}")
            self.cookies = None
            return False

    def salvar_documentos(self, documentos, pagina):
        """Salvando os documentos"""
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        arquivo_nome = f"assunto_{self.assunto_de_interesse}_pagina_{pagina}_data_{timestamp}.json"
        pasta = "documentos"
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, arquivo_nome)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(documentos, arquivo, ensure_ascii=False, indent=4)
                print(f"Documentos da página {pagina} salvos em: \033[1;32m{caminho}\033[0m")
        except Exception as e:
            print(f"Erro ao salvar os documentos da página {pagina}: {e}")

    def iniciar_sessao(self):
        self.num_pagina()
        self.assunto_interesse()
        print("\033[1;33m==== Iniciando a Sessão ====\033[0m")
        pagina_atual = 1
        limite_paginas = 10
        while pagina_atual <= limite_paginas:
            if not self.url_post:
                self.fazer_requisicao_captcha()
            if self.url_post:
                sucesso = self.enviar_documento(pagina_atual)
                if sucesso:
                    print(f"==== Página {pagina_atual} processada com sucesso.")
                    pagina_atual += 1
                else:
                    print(f"Erro ao processar a página {pagina_atual}. Tentando novamente...")

        print("\033[1;33m==== Limite de páginas atingido. Sessão finalizada. ====\033[0m")


if __name__ == "__main__":
    sessao = SessaoJurisprudencia()
    sessao.iniciar_sessao()
