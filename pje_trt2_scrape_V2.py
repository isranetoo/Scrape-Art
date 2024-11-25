import base64
import os
import csv
import logging
import time
import random
import re
import requests
import pytesseract
from typing import List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from PIL import Image, ImageEnhance, ImageFilter
from bs4 import BeautifulSoup

class CaptchaResolver:
    @staticmethod
    def preprocessing(image_path):
        """Pré-processar imagem para melhorar a precisão do OCR."""
        try:
            image = Image.open(image_path)
            image = image.convert('L') 
            image = image.filter(ImageFilter.SHARPEN)  
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.0)  
            return image
        except Exception as e:
            logging.error(f"Erro no pré-processamento do CAPTCHA: {e}")
            return None
    
    @staticmethod
    def resolve_captcha(image_path):
        """Resolver CAPTCHA usando OCR Tesseract."""
        try:
            pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
            
            processed_image = CaptchaResolver.preprocessing(image_path)
            if processed_image is None:
                return None
            
            config = '--psm 6 --oem 3 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            texto_captcha = pytesseract.image_to_string(processed_image, config=config)
            
            texto_captcha = re.sub(r'[^a-zA-Z0-9]', '', texto_captcha.strip().upper())
            return texto_captcha[:6] 
        except Exception as e:
            logging.error(f"Erro ao resolver CAPTCHA: {e}")
            return None

class JurisprudenciaScraper:
    URL_BASE = 'https://pje.trt2.jus.br/jurisprudencia/'
    URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'
    URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'

    def __init__(self, max_retries: int = 3):
        self.sessao = self._configurar_sessao(max_retries)
        self.dados_coletados: List[List[str]] = []
        self.logger = logging.getLogger(__name__)
        self.captcha_resolver = CaptchaResolver()

    def _configurar_sessao(self, max_retries: int) -> requests.Session:
        """Configurar sessão robusta com estratégia de repetição."""
        sessao = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=0.3,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adaptador = HTTPAdapter(max_retries=retry_strategy)
        sessao.mount('https://', adaptador)
        
        sessao.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })
        return sessao

    def obter_pagina_inicial(self) -> Optional[str]:
        """Buscar página inicial com tratamento de erros."""
        try:
            resposta = self.sessao.get(self.URL_BASE, timeout=10)
            resposta.raise_for_status()
            return resposta.text
        except requests.RequestException as e:
            self.logger.error(f"Erro ao acessar página inicial: {e}")
            return None

    def resolver_captcha_base64(self, base64_imagem: str) -> Optional[str]:
        """Resolver CAPTCHA a partir de uma imagem base64."""
        try:
            pasta_temp = "temp_captchas"
            os.makedirs(pasta_temp, exist_ok=True)

            caminho_imagem = os.path.join(pasta_temp, "captcha.jpg")

            if ',' in base64_imagem:
                base64_imagem = base64_imagem.split(',')[1]

            with open(caminho_imagem, "wb") as f:
                f.write(base64.b64decode(base64_imagem))

            resultado = self.captcha_resolver.resolve_captcha(caminho_imagem)
            return resultado
        except Exception as e:
            self.logger.error(f"Erro ao resolver CAPTCHA: {e}")
            return None

    def coletar_dados(self, html: str) -> List[List[str]]:
        """Coletar dados dos documentos do HTML."""
        dados_coletados = []
        try:
            soup = BeautifulSoup(html, 'html.parser')
            itens = soup.select('mat-list-item')
            
            for item in itens:
                try:
                    dados = [
                        item.find('a').get('href', 'N/A') if item.find('a') else 'N/A',
                        item.find('h4').text.strip() if item.find('h4') else 'N/A',
                        item.find('p:nth-of-type(1)').text.strip() if item.find('p:nth-of-type(1)') else 'N/A',
                        item.find('p:nth-of-type(2)').text.strip() if item.find('p:nth-of-type(2)') else 'N/A',
                        item.find('p:nth-of-type(4)').text.strip() if item.find('p:nth-of-type(4)') else 'N/A',
                    ]
                    dados_coletados.append(dados)
                except Exception as item_error:
                    self.logger.warning(f"Erro ao processar item: {item_error}")
            
            return dados_coletados
        except Exception as e:
            self.logger.error(f"Erro ao coletar dados: {e}")
            return []

    def salvar_dados_csv(self, dados: List[List[str]], arquivo: str = 'jurisprudencia_dados.csv') -> None:
        """Salvar dados em arquivo CSV."""
        try:
            with open(arquivo, 'w', newline='', encoding='utf-8') as f:
                escritor = csv.writer(f, delimiter=';')
                escritor.writerow(['Inteiro Teor', 'Título', 'Estágio', 'Órgão', 'Amostras'])
                escritor.writerows(dados)
            self.logger.info(f"Dados salvos em {arquivo}")
        except Exception as e:
            self.logger.error(f"Erro ao salvar CSV: {e}")

    def executar_scraping(self, num_paginas: int = 5) -> None:
        """Executar processo completo de scraping."""
        todos_dados = []

        for pagina in range(1, num_paginas + 1):
            self.logger.info(f"Processando página {pagina}")
            
            time.sleep(random.uniform(1, 3))
            
            try:
                html_inicial = self.obter_pagina_inicial()
                if not html_inicial:
                    break
                
                soup = BeautifulSoup(html_inicial, 'html.parser')
                captcha_img = soup.find('img', id='imagemCaptcha')
                
                if captcha_img and 'src' in captcha_img.attrs:
                    resposta_captcha = self.resolver_captcha_base64(captcha_img['src'])
                    if resposta_captcha:
                        self.logger.info(f"CAPTCHA resolvido: {resposta_captcha}")
                
                dados_pagina = self.coletar_dados(html_inicial)
                todos_dados.extend(dados_pagina)
                
                if not dados_pagina:
                    self.logger.warning("Nenhum dado coletado. Possível término.")
                    break
            
            except Exception as e:
                self.logger.error(f"Erro ao processar página {pagina}: {e}")
                break
        
        self.salvar_dados_csv(todos_dados)

def main():
    try:
        scraper = JurisprudenciaScraper()
        scraper.executar_scraping(num_paginas=3)
    except Exception as e:
        logging.error(f"Erro na execução: {e}")

if __name__ == "__main__":
    main()
