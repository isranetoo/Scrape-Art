import requests
import re
import webbrowser
import time

# Função para obter o token de desafio
def obter_token():
    url_token = "https://pje.trt2.jus.br/juris-backend/api/token"
    response = requests.get(url_token)
    if response.status_code == 200:
        # Exemplo de como pode ser feito o parsing do token, mas isso pode mudar de acordo com a resposta real
        token = response.json().get("token", "")
        if token:
            return token
    return None

# Função para obter o captcha
def obter_token_captcha():
    url_captcha = "https://pje.trt2.jus.br/juris-backend/api/captcha"
    response = requests.get(url_captcha)
    if response.status_code == 200:
        # Aqui você pode verificar os dados que a API retorna
        print("Captcha obtido com sucesso.")
        return response.json().get("tokenCaptcha", "")
    return None

# Função para obter o tokenDesafio
def obter_token_desafio(token):
    url_desafio = f"https://pje.trt2.jus.br/juris-backend/api/documentos?tokenDesafio={token}&resposta="
    response = requests.get(url_desafio)
    if response.status_code == 200:
        # Aqui você pode manipular a resposta para extrair mais dados, se necessário
        print("TokenDesafio obtido com sucesso.")
        return response.json().get("tokenDesafio", "")
    return None

# Função para acessar o site e abrir o navegador
def abrir_pagina():
    url_inicial = "https://pje.trt2.jus.br/jurisprudencia/"
    print("Abrindo o navegador para você visualizar o captcha e digitar a resposta.")
    webbrowser.open(url_inicial)
    print("Página aberta. Por favor, resolva o captcha manualmente.")

# Função principal para executar o fluxo
def main():
    # Passo 1: Obter o token
    token = obter_token()
    if token:
        print(f"Token obtido: {token}")
        
        # Passo 2: Obter o token captcha
        token_captcha = obter_token_captcha()
        if token_captcha:
            print(f"TokenCaptcha obtido: {token_captcha}")
            
            # Passo 3: Abrir página para resolver captcha manualmente
            abrir_pagina()

            # Passo 4: Esperar o usuário digitar a resposta do captcha
            resposta_manual = input("Digite a resposta do captcha manualmente: ")

            # Passo 5: Fazer a requisição à API de documentos com o tokenDesafio e a resposta
            url_api_documentos = f"https://pje.trt2.jus.br/juris-backend/api/documentos?tokenDesafio={token}&resposta={resposta_manual}"
            response_api = requests.get(url_api_documentos)
            
            if response_api.status_code == 200:
                print("Requisição à API de documentos realizada com sucesso!")
                # Processar os dados da resposta
                print(response_api.json())  # Aqui você pode manipular os dados retornados
            else:
                print("Falha ao acessar a API de documentos.")
        else:
            print("Não foi possível obter o tokenCaptcha.")
    else:
        print("Não foi possível obter o token.")

if __name__ == "__main__":
    main()
