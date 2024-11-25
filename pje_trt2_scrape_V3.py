import base64
import os
import time
import csv
from io import BytesIO
from PIL import Image
import requests
from bs4 import BeautifulSoup
from captcha_local_solver import solve_captcha_local

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'


class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.img_src = None
        self.dados_coletados = []

    def obter_pagina_inicial(self):
        """Fazer requisição para a página inicial."""
        try:
            resposta = self.sessao.get(URL_BASE)
            resposta.raise_for_status()
            return resposta.text
        except requests.RequestException as e:
            print(f"Erro ao acessar a página inicial: {e}")
            return None

    def sair_dialogo(self, html):
        """Sair da janela de diálogo usando BeautifulSoup."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            fechar_botao = soup.select_one("#ajudaDialogo > div.rodape > button")

            if fechar_botao:
                print("Botão de fechar encontrado na página.")
                response = self.sessao.get(URL_BASE)  
                if response.status_code == 200:
                    print("Janela de diálogo fechada com sucesso.")
                    return response.text
                else:
                    print(f"Falha ao fechar a janela. Código de status: {response.status_code}")
            else:
                print("Nenhum botão de fechar encontrado com o seletor fornecido.")
        except Exception as e:
            print(f"Erro ao tentar fechar o diálogo: {e}")
        return html

    def clicar_pesquisar(self, html):
        """Clicar no botão de pesquisa."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            botao_pesquisar = soup.select_one("#buttonPesquisar > span > span")
            if botao_pesquisar:
                print("Botão de pesquisar encontrado.")
                response = self.sessao.post(URL_BASE)  
                if response.status_code == 200:
                    print("Pesquisa realizada com sucesso.")
                    return response.text  
                else:
                    print(f"Falha ao realizar a pesquisa. Status: {response.status_code}")
            else:
                print("Botão de pesquisar não encontrado no HTML recebido.")
        except Exception as e:
            print(f"Erro ao clicar no botão de pesquisa: {e}")
        return html

    def obter_imagem_captcha(self, html):
        """Obter link da imagem do Captcha."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            img_element = soup.find('img', id="imagemCaptcha")
            if img_element:
                self.img_src = img_element['src']
                print(f"Imagem Captcha encontrada: {self.img_src}")
            else:
                print("Imagem Captcha não encontrada.")
        except Exception as e:
            print(f"Erro ao obter a imagem do captcha: {e}")

    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converter base64 para JPEG e salvar na pasta 'images'."""
        try:
            pasta_images = "images"
            os.makedirs(pasta_images, exist_ok=True)

            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string

            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))

            caminho_arquivo = os.path.join(pasta_images, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva como {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao converter base64 para JPEG: {e}")

    def resolver_captcha(self, base64_string):
        """Resolver o Captcha localmente."""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do captcha: {self.resposta_captcha}")
        except Exception as e:
            print(f"Erro ao resolver o captcha: {e}")

    def enviar_resposta_captcha(self):
        """Enviar a resposta do captcha ao servidor."""
        try:
            payload = {"resposta": self.resposta_captcha, "tokenDesafio": self.token_desafio}
            resposta = self.sessao.post(URL_DOCUMENTOS, json=payload)
            print(f"Resposta do servidor: {resposta.status_code}")
            if resposta.status_code == 200:
                print("Captcha resolvido e resposta enviada com sucesso.")
        except Exception as e:
            print(f"Erro ao enviar resposta do captcha: {e}")

    def coletar_dados(self, html):
        """Coletar dados dos elementos relevantes na página."""
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
            print(f"Erro ao coletar dados: {e}")

    def salvar_dados_em_csv(self, nome_arquivo="dados_jurisprudencia_PJE.csv"):
        """Salvar dados em CSV."""
        try:
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                if file.tell() == 0:
                    writer.writerow(['Inteiro Teor', 'Título', 'Estágio', 'Órgão', 'Amostras'])
                writer.writerows(self.dados_coletados)
            print(f"Dados salvos em {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar dados em CSV: {e}")

    def iniciar_sessao(self):
        """Fluxo principal para iniciar a sessão e coletar dados."""
        try:
            html = self.obter_pagina_inicial()
            if not html:
                return

            html = self.sair_dialogo(html)

            html = self.clicar_pesquisar(html)

            html = self.sessao.get(URL_BASE).text  
            self.obter_imagem_captcha(html)
            if self.img_src:
                if self.img_src.startswith('http'):
                    response = self.sessao.get(self.img_src)
                    base64_string = base64.b64encode(response.content).decode('utf-8')
                else:
                    base64_string = self.img_src

                self.converter_base64_para_jpeg(base64_string)
                self.resolver_captcha(base64_string)

            self.enviar_resposta_captcha()

            html = self.sessao.get(URL_BASE).text
            self.coletar_dados(html)

            self.salvar_dados_em_csv()
        except Exception as e:
            print(f"Erro na sessão: {e}")


sessao = SessaoJurisprudencia()
sessao.iniciar_sessao()
