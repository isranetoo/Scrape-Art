import requests
import json
import re

URL_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/token'
URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_TOKEN_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
URL_BUSCA_JURISPRUDENCIA = 'https://pje.trt2.jus.br/juris-backend/api/jurisprudencia'
URL_CAPTCHA_TOKEN = 'https://pje.trt2.jus.br/juris-backend/api/documentos?tokenCaptcha=eed58f694dc7a573fef0cc124fd4060cd81eefab6342626ad67fddf828d01ed3'

def obter_token_inicial():
    """Obtém o token inicial a partir da API."""
    try:
        response = requests.get(URL_TOKEN, timeout=10)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            token_data = response.json()
            token = token_data.get('token')
            if token:
                print("Token inicial obtido:", token)
                return token
            else:
                print("Erro: 'token' não encontrado na resposta.")
        else:
            print(f"Erro ao obter token inicial. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao fazer requisição para obter o token: {e}")
    return None

def obter_token_captcha_dinamico():
    """Obtém o token de captcha diretamente da URL fornecida."""
    try:
        response = requests.get(URL_CAPTCHA_TOKEN, timeout=10)
        if response.status_code == 200:

            match = re.search(r'tokenCaptcha=([a-f0-9]+)', URL_CAPTCHA_TOKEN)
            if match:
                token_captcha = match.group(1)
                print("Token Captcha dinâmico obtido:", token_captcha)
                return token_captcha
            else:
                print("Erro: Token Captcha não encontrado na URL.")
        else:
            print(f"Erro ao acessar a URL do Token Captcha. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao obter o token Captcha dinâmico: {e}")
    return None

def buscar_documentos(token_captcha, token_desafio):
    """Busca os documentos de jurisprudência com o token de captcha e desafio."""
    params = {
        "tokenDesafio": token_desafio,
        "tokenCaptcha": token_captcha,
        "pagina": 0,
        "tamanho": 10
    }
    try:
        response = requests.get(URL_BUSCA_JURISPRUDENCIA, params=params, timeout=10)
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            resultados = response.json()
            print("Resultados da busca:", json.dumps(resultados, indent=2))
        else:
            print(f"Erro ao buscar documentos. Status Code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar documentos: {e}")

def executar_busca():
    """Função principal para executar a busca completa, desde a obtenção do token até a consulta de jurisprudência."""
    print("Iniciando busca de jurisprudência...")


    token_inicial = obter_token_inicial()
    if not token_inicial:
        return

    token_captcha = obter_token_captcha_dinamico()
    if not token_captcha:
        return


    token_desafio = "64501445e3c4107f9e580c5ff31666b5cfbd0040de664747dad644abef05fa28e97eaa60ed2cb32be598cb2e023228e1506c5288992cc5f9664b57c3ea10eebb688a12a7407b594b8d5dc034d8ef55dc766528cf709f91e27695b40fec18e6fa"

    buscar_documentos(token_captcha, token_desafio)

if __name__ == "__main__":
    executar_busca()
