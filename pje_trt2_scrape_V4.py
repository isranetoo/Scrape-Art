import base64
import os
import csv
import requests
from time import sleep
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
from captcha_local_solver import solve_captcha_local

URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/desafio/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'


class SessaoJurisprudencia:
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.img_src = None
        self.dados_coletados = []

    def obter_pagina_inicial(self):
        """Fazer requisições da pagina inicial"""
        try:
            resposta = self.sessao.get(URL_BASE)
            resposta.raise_for_status()
            print("Pagina inicial carregada com sucesso")
            return resposta.text
        except requests.RequestException as e:
            print(f"Erro ao acessar a pagina inicial: {e}")
            return None
        
    def fechar_dialogo(self,html):
        """Fezando o PopUp de dialogo"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            fechar_botao = soup.select_one("#ajudaDialogo > div.rodape > button > span > span")
            if fechar_botao:
                print(f"Janela do Dialogo Achada com sucesso")
                respota = self.sessao.get(URL_BASE)
                if respota == 200:
                    print("Janela do Dialogo fechada com sucesso")
                    return respota.text
                else:
                    print("Nenhum botao de fechar foi achado")
        except Exception as e:
            print(f"Erro ao fechar o botão de fechar: {e}")
        return html
    
    def clicar_pesquisar(self, html):
        "Clicar no botão de pesquisar"
        try:
            soup = BeautifulSoup(html, 'html.parser')
            botao_pesquisar = soup.select_one("#buttonPesquisar > span > span")
            if botao_pesquisar:
                print('Botão de pesquisar encotrado')
                resposta = self.sessao.post(URL_BASE)
                if resposta.status_code == 200:
                    print("Botão de pesquisar encotrado com sucesso")
                    return resposta.text
                else:
                    print("Botão de pesquisar NÃO encontrado")
        except Exception as e:
            print(f"Erro ao acharo botão de pesquisar: {e}")
            return html
    
    def obter_imagem_captcha(self,html):
        """Obeter link da imagem do captcha"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            img_element = soup.find('img', id="#imagemCaptcha")
            if img_element:
                self.img_src = img_element['src']
                print(f"imagem encotrada: {self.img_src}")
                return True
            else:
                print("Imagem do captcha NÃO encotrada")
                return False
        except Exception as e:
            print(f"Erro ao encotrar a imagem do Captcha: {e}")
            return False
        
    def converter_base64_para_jpeg(self,base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Converter base64 para Jpeg e salvar na pasta Imagems"""
        try:
            pasta_images = 'images'
            os.makedirs(pasta_images, exist_ok=True)
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image')else base64_string
            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))
            caminho_arquivo = os.path.join(pasta_images, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva como: {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar a imagem do captcha: {e}")

    def resolver_captcha(self,base64_string):
        """Resolvendo o Captcha"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            self.resposta_captcha = solve_captcha_local(base64_string)
            print(f"Resposta do Captcha: {self.resposta_captcha}")
            return True
        except Exception as e:
            print(f"Erro ao resolver o Captcha: {e}")
            return False
        
    def enviar_resposta_captcha(self):
        """Eviando a resposta do Captcha ao servidor"""
        try:
            payload = {"resposta": self.resposta_captcha, "tokenDesafio": self.token_desafio}
            resposta = self.sessao.post(URL_CAPTCHA, json=payload)
            if resposta.status_code == 200:
                print("Captcha resolvido com sucesso")
                return True
            else:
                print(f"Erro ao enviar a resposta do captcha ao servidor")
                return False
        except Exception as e:
            print(f"Erro ao enviar a resposta do CAPTCHA: {e}")
            return False
        
    def coletar_dados(self,html):
        """Coletando os dados da pagina"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            itens = soup.select('mat-list-item')
            for item in itens:
                try:
                    dados = [
                        item.find('a').get('href'),
                        item.find('h4').text.strip(),
                        item.find('p:nth-of-type(1)').text.strip(),
                        item.find('p:nth-of-type(2)').text.strip(),
                        item.find('p:nth-of-type(4)').text.strip(),
                    ]
                    self.dados_coletados.append(dados)
                except AttributeError:
                    print("Erro ao extrair um item. Continuando:")
        except Exception as e:
            print(f"Erro ao  coletar os Dados: {e}")

    def salvar_dados_em_csv(self,nome_arquivo="dados_jurisprudencia_PJE.csv"):
        """Salvando os dados coletados em CSV"""
        try:
            with open(nome_arquivo, 'a', newline='', encoding='utf-8') as file:
                writer = csv.writer(file, delimiter=';')
                if file.tell() == 0:
                    writer.writerow['Inteiro Teor', 'Título', 'Estágio', 'Órgão', 'Amostras']
                writer.writerow(self.dados_coletados)
            print(f"Dados salvos em: {nome_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar os dados coletados: {e}")

    def iniciar_sessao(self):
        """Fluxo de iniciação"""
        try:
            html = self.obter_pagina_inicial()
            if not html:
                return
            
            html = self.fechar_dialogo(html)
            html = self.clicar_pesquisar(html)

            html = self.sessao.get(URL_BASE).text
            if self.obter_imagem_captcha(html):
                if self.img_src.startswith('http'):
                    resposta = self.sessao.get(self.img_src)
                    base64_string = base64.b64encode(resposta.content).decode('utf-8')
                else:
                    base64_string = self.img_src

            self.converter_base64_para_jpeg(base64_string)
            if self.resolver_captcha(base64_string):
                if self.enviar_resposta_captcha():
                    html = self.sessao.get(URL_BASE).text
                    self.coletar_dados(html)
                    self.salvar_dados_em_csv()
        except Exception as e:
            print(f"Erro na sessão: {e}")


