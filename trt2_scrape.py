import requests
import json
import re
import os

URL_TOKEN = os.getenv('URL_TOKEN', 'https://pje.trt2.jus.br/juris-backend/api/token')
URL_CAPTCHA = os.getenv('URL_CAPTCHA', 'https://pje.trt2.jus.br/juris-backend/api/captcha')
URL_BUSCA_JURISPRUDENCIA = os.getenv('URL_BUSCA_JURISPRUDENCIA', 'https://pje.trt2.jus.br/juris-backend/api/jurisprudencia')

session = requests.Session()  

def obter_token_inicial():
    """Obtém o token inicial da API."""
    try:
        response = session.get(URL_TOKEN, timeout=10)
        response.raise_for_status()
        if 'application/json' in response.headers.get('Content-Type', ''):
            token_data = response.json()
            return token_data.get('token')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter token inicial: {e}")
    return None

def obter_token_captcha():
    """Obtém o token de captcha via URL e resposta JSON da API."""
    try:
        response = session.get(URL_CAPTCHA, timeout=10)
        response.raise_for_status()
        if 'application/json' in response.headers.get('Content-Type', ''):
            captcha_data = response.json()
            return captcha_data.get('tokenCaptcha')
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter o token Captcha: {e}")
    return None

def buscar_documentos(token_captcha, token_desafio, pagina=0, tamanho=10):
    """Busca documentos de jurisprudência com tokens fornecidos."""
    params = {
        "tokenDesafio": token_desafio,
        "tokenCaptcha": token_captcha,
        "pagina": pagina,
        "tamanho": tamanho
    }
    try:
        response = session.get(URL_BUSCA_JURISPRUDENCIA, params=params, timeout=10)
        response.raise_for_status()
        if 'application/json' in response.headers.get('Content-Type', ''):
            resultados = response.json()
            print("Resultados da busca:", json.dumps(resultados, indent=2))
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar documentos: {e}")

def executar_busca():
    """Execução completa da busca de jurisprudência."""
    print("Iniciando busca de jurisprudência...")
    token_inicial = obter_token_inicial()
    if not token_inicial:
        print("Token inicial não foi obtido.")
        return

    token_captcha = obter_token_captcha()
    if not token_captcha:
        print("Token Captcha não foi obtido.")
        return

    token_desafio = "748e98f6b97f17eebc82d7c8e348ef38840bc1345f5011cea2c2971285ba248b"
    buscar_documentos(token_captcha, token_desafio)

if __name__ == "__main__":
    executar_busca()
