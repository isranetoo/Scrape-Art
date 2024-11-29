import os
import json
import csv
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
        self.assunto_de_interesse = None
        self.numero_de_pagina = None


    def num_pagina(self):
        self.numero_de_pagina = input("==== Digite o numero de Processos por pagina: ")

    def assunto_interesse(self):
        self.assunto_de_interesse = input("==== Digite o assunto de interesse: ")  

    def obter_ip_local(self):
        """Obtendo o IP local"""
        try:
            resposta = requests.get('https://api.ipify.org')
            return resposta.text
        except Exception as e:
            print(f"Erro ao localizar o IP local: {e}")
            return "IP Local NÃO disponivel"
        
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
                    print("Nenhum campo de imagem foi encotrado no JSON")
            except Exception as e:
                print(f"Erro ao encontrar a imagem no JSON: {e}")

    def resolver_captcha(self, base64_string):
        """Resolvendo Captcha com o solve_captcha_local"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            resposta = solve_captcha_local(base64_string)
            self.resposta_captcha = resposta
            print(f"Resposta do CAPTCHA: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")
            self.resposta_captcha = None
        
    def enviar_documentos(self, pagina):
        """Enviando documentos POST"""
        if not self.token_desafio or not self.resposta_captcha:
            print("Token de desafio ou resposta do captcha ausente.")
            return False
        
        url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "andField": [self.assunto_de_interesse],
            "paginationSize": self.numero_de_pagina,
            "paginationPosition": pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
        }
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'User-Agent': self.obter_user_agent(),
        }
        while True:
            try:
                resposta = self.sessao.post(url_post, json=payload, headers=headers)
                if resposta.status_code == 200:
                    documentos = resposta.json()
                    if "mensagem" in documentos and documentos["mensagem"] == "A resposta informada é incorreta":
                        print(f"Erro na resposta: {documentos['mensagem']}. Tentando novamente para pagina {pagina}...")
                        self.fazer_requisicao_captcha()
                        continue
                    else:
                        self.salvar_documentos(documentos, pagina)
                        return True
                else:
                    print(f"Erro ao realizar o POST: {resposta.status_code} - {resposta.text}")
                    return False
            except Exception as e:
                print(f"Erro ao realizar o post: {e}")
                return False

    def salvar_documentos(self, documentos, pagina):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        arquivo_nome = f"documentos_pagina_{pagina}_{timestamp}.json"
        pasta = "documentos"
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, arquivo_nome)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(documentos, arquivo, ensure_ascii=False, indent=4)
                print(f"Documentos da página {pagina} salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar os documentos da página {pagina}: {e}")

    def iniciar_sessao(self):
        self.num_pagina()
        self.assunto_interesse()
        print("==== Iniciando a Sessão ====")
        pagina_atual = 1  
        limite_paginas = 15  
        while pagina_atual <= limite_paginas:
            self.fazer_requisicao_captcha()
            if self.token_desafio and self.resposta_captcha:
                sucesso = self.enviar_documentos(pagina_atual)
                if sucesso:
                    print(f"==== Página {pagina_atual} processada com sucesso.")
                    pagina_atual += 1
                else:
                    print(f"Erro ao processar a página {pagina_atual}. Tentando novamente...")
            else:
                print("Erro ao resolver captcha. Tentando novamente...")

        print("==== Limite de páginas atingido. Sessão finalizada. ====")

if __name__ == "__main__":
    sessao = SessaoJurisprudencia()
    sessao.iniciar_sessao()