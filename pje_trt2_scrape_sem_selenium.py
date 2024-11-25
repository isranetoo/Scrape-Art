import base64
import os
import time
import requests
import json
import csv
from io import BytesIO
from PIL import Image
from captcha_local_solver import solve_captcha_local


URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.dados_coletados = []

    def obter_captcha(self):
        """Obtendo a img do Captcha"""
        try:
            response = self.sessao.get(URL_BASE)
            if response.status_code == 200:
                page_content = response.text
                start = page_content.find('data:image/jpeg;base64,') + len('data:image/jpeg;base64,')
                end = page_content.find('"', start)
                base64_image = page_content[start:end]
                if base64_image:
                    print('CAPTCHA Obitido com sucesso.')
                    return base64_image
                else:
                    print(f'erro ao encontrar o CAPTCHA na pagina')
            else:
                print(f'Erro ao carregar a pagina inicial: {response.status_code}')
        except Exception as e:
            print(f"Erro ao obter o CAPTCHA: {e}")
    
    def salvar_captcha(self,base64_string, nome_arquivo="captcha_image.jpeg"):
        """Salvar o CAPTCHA como a depuração."""
        try:
            os.makedirs("images", exist_ok=True)
            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))
            caminho = os.path.join("image",nome_arquivo)
            imagem.save(caminho, "JPEG")
            print(f"CAPTCHA salvo no caminho {caminho}")
        except Exception as e:
            print(f"Erro ao salvar o CAPTCHA: {e}")

    def resolver_captcha(self, base64_string):
        """CAPTCHA resolver usando o Local_Solver"""
        try:
            resposta = solve_captcha_local(base64_string)
            print(f"Resposta do CAPTCHA {resposta}")
            return resposta
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")

    def enviar_captcha(self, resposta_captcha):
        try:
            data={
                "resposta": resposta_captcha,
                "tokenDesafio": self.token_desafio
            }
            headers = {
                'Accept': 'aplication/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0',
                'Referer': URL_BASE
            }
            response = self.sessao.post(URL_DOCS, json=data, headers=headers)
            if response.status_code == 200:
                print(f"CAPTCHA eviado com sucesso")
                return response.json()
            else:
                print(f"Erro ao enviar o CAPTCHA: {response.status_code}")
        except Exception as e:
            print(f"Erro ao enviar CAPTCHA: {e}")

    def coletar_dados(self):
        """Coleta  do dados da API apos o CAPTCHA"""
        try:
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'User-Agent': 'Mozilla/5.0'
            }
            response = self.sessao.get(URL_DOCS, headers=headers)
            if response.status_code == 200:
                print(f"Dados coletados com sucesso")
                return response.json()
            else:
                print(f"Erro ao coletar os dados {response.status_code}")
        except Exception as e:
            print(f"Erro ao coletado os dados: {e}")

    def salvar_dados_em_csv(self, nome_arquivo="dados_jurisprudencia_PJE.csv"):
        """Dados salvados em arquivo CSV"""
        try:
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                if file.tell() == 0:
                    writer.writerow([ 'Interior Teor', 'Título', 'Estágio', 'Orgão', 'Amostras'])
                writer.writerows(self.dados_coletados)
                print(f"Dados coletados {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar os dados em CSV: {e}")

    def iniciar_a_sessao(self):
        """Iniciar a Sessão para resolver o CAPTCHA e coletar os Dados."""
        try:
            print("Iniciando a Sessão")

            base64_image = self.obter_captcha()
            if base64_image:
                self.salvar_captcha(base64_image)


                self.resposta_captcha = self.resolver_captcha(base64_image)
                if self.resposta_captcha:

                    response_data = self.enviar_captcha(self.resposta_captcha)
                    if response_data:

                        dados = self.coletar_dados()
                        if dados: 
                            self.dados_coletados.extend(dados)
                            self.salvar_dados_em_csv()

        except Exception as e:
            print(f"Erro ao iniciar a sessão: {e}")

sessao = SessaoJurisprudencia()
sessao.iniciar_a_sessao()
    

    
            