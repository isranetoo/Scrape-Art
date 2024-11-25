import base64
import os
import requests
import csv
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from captcha_local_solver import solve_captcha_local

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.img_src = None
        self.dados_coletados = []

    def obter_pagina_inicial(self):
        """Fazendo as Requisições da pagina inicial"""
        try:
            resposta = self.sessao.get(URL_BASE)
            resposta.raise_for_status()
            return resposta.text
        except Exception as e:
            print(f"Erro ao acessar a pagina inicial: {e}")
            return None
        
    def sair_dialogo(self,html):
        """Clicando no dialogo para sair"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            fechar_botao = soup.select_one("div[role='dialogo'] button span span")
            if fechar_botao:
                print(f"Botão de fechar encotrado")
                fechar_url = fechar_botao.find_parent('button')['onclick']
                if fechar_url:
                    self.sessao.get(fechar_url)
                    print("Janela fechada")
        except Exception as e:
            print(f"Erro ao fechar a janela: {e}")

    def clicar_pesquisar(self,html):
        """Clicando no botao de Pesquisar"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            botao_pesquisar = soup.select_one("button[aria-label='Pesquisar']")
            if botao_pesquisar:
                print("Botão de pesquisar encotrado")
                self.sessao.post(URL_DOCS)
                print("Pesquisa Realizada")
        except Exception as e:
            print(f"Erro ao encontrar o botão de pesquisa: {e}")


    def obter_imagem_captcha(self, html):
        """Obter a imagem do CAPTCHA."""
        try: 
            soup = BeautifulSoup(html, 'html.parser')
            img_element = soup.find('img', id="imagemCaptcha")
            if img_element:
                self.img_src = img_element['src']
                print("Imagem do Captcha encontrada")
            else: 
                print("Image do Captcha NÃO encontrada")
        except Exception as e:
            print(f"Erro ao encontrar a imagem do Captcha: {e}")


    def converter_img_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Convertendo a imagem Base64 para JPEG na pasta Images."""
        try:
            pasta_images = "images"
            os.makedirs(pasta_images, exist_ok=True)

            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string

            imagem =Image.open(BytesIO(base64.b64decode(base64_string)))

            caminho_arquivo = os.path.join(pasta_images, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva como: {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao converter imagem Base64 para JPEG: {e}")

    def resolver_captcha(self, base64_string):
        """Resolvendo o Captcha localmente"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do Captcha: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o Captcha {e}")

    def enviar_resposta_do_captcha(self):
        """Enviando as resposta do capthca para o servidor"""
        try:
            payload = {"resposta": self.resposta_captcha, "tokenDesafio": self.token_desafio}
            resposta = self.sessao.post(URL_DOCS, json=payload)
            print(f"Resposta do Servidor: {resposta.status_code}")
        except Exception as e:
            print(f"Erro ao enviar resposta do captcha: {e}")

    def coletar_dados(self,html):
        """Coletando os dados da pagina"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            itens = soup.select('mat-list-item')
            for item in itens:
                dados = [
                    item.find('a').get('href'),
                    item.find('h4').text.strip(),
                    item.find('p:nth-of-type(1)').text.strip(),
                    item.find('p:nth-of-type(2)').text.strip(),
                    item.find('p:nth-of-type(4)').text.strip(),
                ]
                self.dados_coletados.append(dados)
        except Exception as e:
            print(f"Erro ao coletar os dados: {e}")

    def salvar_os_dados_em_csv(self, nome_arquivo="dados_jurisprudencia_PJE.csv"):
        """Salvando os dados em CSV"""
        try:
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                if file.tell() == 0:
                    writer.writerow(['Interior Teor', 'Título', 'Estágio', 'Orgão', 'Amostras'])
                writer.writerows(self.dados_coletados)
                print(f'Dados salvos no arquivo CSV: {nome_arquivo}')
        except Exception as e:
            print(f"Erro ao salvar o dados em CSV: {e}")

    def iniciar_sessao(self):
        """Iniciando a Sessão"""
        try: 
            html = self.obter_pagina_inicial()
            if not html: 
                return
            
            self.sair_dialogo(html)

            self.clicar_pesquisar(html)
            
            html = self.sessao.get(URL_BASE).text
            self.obter_imagem_captcha(html)
            if self.img_src:
                self.converter_img_base64_para_jpeg(self.img_src)
                self.resolver_captcha(self.img_src)

            self.enviar_resposta_do_captcha()

            html = self.sessao.get(URL_DOCS).text
            self.coletar_dados(html)
            self.salvar_os_dados_em_csv()
        except Exception as e:
            print(f"Erro ao iniciar a Sessão: {e}")


sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
        