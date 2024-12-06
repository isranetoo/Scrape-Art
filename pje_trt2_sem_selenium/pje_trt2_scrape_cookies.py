import json
import requests
import os
from datetime import datetime
from captcha_local_solver import solve_captcha_local

URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self, assunto: str, procs_por_pagina: int, max_paginas: int = 10):
        """ Classe para pesquisa de jurisprudencia no TRT 2

        Args:
            assunto: Assunto a ser pesquisado
            procs_por_pagina: Numero de processo em cada pagina
            max_paginas: Numero maximo de paginas a serem coletadas
                         Normalmente o site para de funcionar após 10k processos coletados
        """
        self.assunto = assunto
        self.procs_por_pagina = procs_por_pagina
        self.max_paginas = max_paginas

        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.url_post = None
        self.cookies = {}

    def fazer_requisicao_captcha(self):
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers={'Accept': 'application/json'})
            resposta.raise_for_status()
            dados = resposta.json()
            self.token_desafio = dados.get('tokenDesafio')
            self.resolver_captcha(dados.get('imagem'))
        except Exception as e:
            print(f"Erro ao obter o CAPTCHA: {e}")

    def resolver_captcha(self, base64_string):
        try:
            if base64_string:
                base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
                self.resposta_captcha = solve_captcha_local(base64_string)
                print(f"Resposta do CAPTCHA: \033[1;32m{self.resposta_captcha}\033[0m")
                self.url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
                self.configurar_cookies()
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")

    def configurar_cookies(self):
        self.cookies = {
                "_ga": "GA1.3.2135935613.1731417901",
                "_ga_9GSME7063L": "GS1.1.1731436526.3.0.1731436545.0.0.0",
                "exibirajuda": "true",
                "respostaDesafio": self.resposta_captcha,
                "tokenDesafio": self.token_desafio,
            }
        self.sessao.cookies.update(self.cookies)
        self.salvar_em_arquivo("cookies", "cookies.json", self.cookies)

    def salvar_em_arquivo(self, pasta, nome_arquivo, conteudo):
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
            print(f"Arquivo salvo em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar os arquivo: {e}")

    def enviar_documento(self, pagina):
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "andField": [self.assunto],
            "paginationPosition": pagina,
            "paginationSize": self.procs_por_pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
        }
        try:
            resposta = self.sessao.post(self.url_post, json=payload, headers={'Content-Type': 'application/json'})
            timestamp = datetime.now().strftime("%d-%m-%Y")
            if resposta.status_code == 200:
                documentos = resposta.json()
                if documentos.get("mensagem") == "A resposta informada é incorreta":
                    print("\033[1;31mCAPTCHA incorreto.\033[0m Gerando novo...")
                    self.url_post = None
                else:
                    self.salvar_em_arquivo("documentos", f"assunto_{self.assunto}_pagina_{pagina}_data_{timestamp}_num_pagina_{self.procs_por_pagina}.json", documentos)
                    return True
        except Exception as e:
            print(f"Erro ao salvar o arquivo JSON: {e}")
        return False

    def iniciar_sessao(self):
        print("\033[1;33m==== Iniciando a Sessão ====\033[0m")
        max_retries = 5
        retries, pagina = 1, 1
        while pagina < self.max_paginas + 1:
            if not self.url_post:
                if retries >= max_retries:
                    raise Exception(f"Unable to solve {retries} captcahs in a row... stopping scrape")
                else:
                    self.fazer_requisicao_captcha()

            if self.url_post and self.enviar_documento(pagina):
                print(f"Página \033[1;34m{pagina}\033[0m processada com \033[1;32mSucesso.\033[0m")
                pagina += 1
            else:
                print(f"Erro ao processar {pagina}, Tentando novamente...")
                retries += 1



if __name__ == "__main__":
    procs_por_pagina = input("==== Digite o número de processos por página: ")
    assunto = input("==== Digite o assunto de interesse: ")

    scrapper = SessaoJurisprudencia(assunto=assunto, procs_por_pagina=procs_por_pagina)
    scrapper = scrapper.iniciar_sessao()