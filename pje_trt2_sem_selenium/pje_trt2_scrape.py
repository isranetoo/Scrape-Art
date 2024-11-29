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
        self.data_de_distribuicao= None

    def num_pagina(self):
        self.numero_de_pagina = input("==== Digite o numero de pagina: ")

    def data_distribuicao(self):
        self.data_de_distribuicao = input("==== Digite a data de Distribuição ex: 2024-05-27: ")

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
        
    def enviar_documento(self):
        """Enviando o documento (POST)"""
        if not self.token_desafio or not self.resposta_captcha:
            print("Token de desafio ou resposta do captcha ausente.")
            return False

        url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "andField": [self.assunto_de_interesse],
            #"assunto": ["Abandono de Emprego [55200]", "Adicional de Horas Extras [55365]" , "Adicional de Horas Extras [13787]"],
            #"classeJudicial": ["Agravo Regimental Trabalhista"],
            #"magistrado": ["IEDA REGINA ALINERI PAULI"],
            #"orgaoJulgador": ["10ª Turma - Cadeira 1"],
            #"orgaoJulgadorColegiado": ["10ª Turma"],
            #"dataPublicacao.start": "2023-10-01",
            "dataDistribuicao.start": self.data_de_distribuicao,
            #"dataPublicacao.end": "2024-11-01",
            "paginationPosition": 1,
            "paginationSize": self.numero_de_pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
            #"ordenarPor": "relevancia" 
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
                print(f"Erro ao realizar o POST: {resposta.status_code} - {resposta.text}")
                return False
        except Exception as e:
            print(f"Erro ao enviar o POST: {e}")

    def salvar_documentos(self, documentos):
        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M-%S")
        arquivo_nome = f"documentos_{timestamp}.json"
        pasta = "documentos"
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, arquivo_nome)
        try:
            with open(caminho, 'a', encoding='utf-8',) as arquivo:
                json.dump(documentos, arquivo, ensure_ascii=False, indent=4)
                print(f"Documentos salvos em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar os documentos: {e}")

    def inciar_sessao(self):
        while True:
            self.assunto_interesse()
            self.data_distribuicao()
            self.num_pagina()
            print("==== Iniciando a Sessão ====")
            self.fazer_requisicao_captcha()
            if self.token_desafio and self.resposta_captcha:
                sucesso = self.enviar_documento()
                if sucesso:
                    print("==== Documentos salvos com SUCESSO.")
                    break
                else:
                    ("Erro ao salvar os Documentos...")
            else:
                print("Erro ao resolver captcha. Tentanto novamente...")

if __name__ == "__main__":
    sessao = SessaoJurisprudencia()
    sessao.inciar_sessao()