import requests
import re
import webbrowser
import time


def obter_token():
    url_token = "https://pje.trt2.jus.br/juris-backend/api/token"
    response = requests.get(url_token)
    if response.status_code == 200:

        token = response.json().get("token", "")
        if token:
            return token
    return None


def obter_token_captcha():
    url_captcha = "https://pje.trt2.jus.br/juris-backend/api/captcha"
    response = requests.get(url_captcha)
    if response.status_code == 200:

        print("Captcha obtido com sucesso.")
        return response.json().get("tokenCaptcha", "")
    return None

def obter_token_desafio(token):
    url_desafio = f"https://pje.trt2.jus.br/juris-backend/api/documentos?tokenDesafio={token}&resposta="
    response = requests.get(url_desafio)
    if response.status_code == 200:
        print("TokenDesafio obtido com sucesso.")
        return response.json().get("tokenDesafio", "")
    return None


def abrir_pagina():
    url_inicial = "https://pje.trt2.jus.br/jurisprudencia/"
    print("Abrindo o navegador para você visualizar o captcha e digitar a resposta.")
    webbrowser.open(url_inicial)
    print("Página aberta. Por favor, resolva o captcha manualmente.")


def main():

    token = obter_token()
    if token:
        print(f"Token obtido: {token}")
        

        token_captcha = obter_token_captcha()
        if token_captcha:
            print(f"TokenCaptcha obtido: {token_captcha}")
            

            abrir_pagina()


            resposta_manual = input("Digite a resposta do captcha manualmente: ")


            url_api_documentos = f"https://pje.trt2.jus.br/juris-backend/api/documentos?tokenDesafio={token}&resposta={resposta_manual}"
            response_api = requests.get(url_api_documentos)
            
            if response_api.status_code == 200:
                print("Requisição à API de documentos realizada com sucesso!")

                print(response_api.json())  
            else:
                print("Falha ao acessar a API de documentos.")
        else:
            print("Não foi possível obter o tokenCaptcha.")
    else:
        print("Não foi possível obter o token.")

if __name__ == "__main__":
    main()
