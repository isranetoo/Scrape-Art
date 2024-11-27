import os
import json
import base64
from io import BytesIO
from PIL import Image
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


    def fazer_requisicao_hearders(self,url):
        """Fazendo a Requisição do Hearder"""
        headers = {
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Connection': 'keep-alive',
            'Referer': URL_CAPTCHA,
            'Authorization': f"Bearer {self.token_desafio}",
            'User-Agent': 'Mozilla/5.0'
        }
        try:
            resposta = self.sessao.get(url, headers=headers)
            resposta.raise_for_status()
            try:
                conteudo_json = resposta.json()
                if "imagem" in conteudo_json and conteudo_json["imagem"]:
                    base64_img = conteudo_json["imagem"]
                    self.token_desafio = conteudo_json.get('tokenDesafio')
                    print("Imagem Base64 retirada do Json")
                    self.converter_base64_para_jpeg(base64_img)
                    self.resolver_captcha(base64_img)
                else:
                    print("Nenhum campo de imagem foi encotrado no JSON")
            except json.JSONDecodeError:
                print(f"Resposta NÃO é um Json: {resposta.text[:500]}")
        except Exception as e:
            print(f"Erro ao coletar a imagem JSON: {e}")


    def obter_cookie(self, url):
        """Coletando o Cookie da pagina"""
        try:
            resposta = self.sessao.get(url)
            resposta.raise_for_status()
            cookie = resposta.cookies.get_dict()
            print(f"Cookie coletado: {cookie}")
            return cookie
        except requests.exceptions.RequestException as e:
            print(f"Erro ao coletar o Cookie: {e}")


    def obter_documentos(self):
        """Coletando os documentos usando o TokenCaptcha"""
        try:
            if not self.token_desafio or not self.resposta_captcha:
                print("Token Desafio ou resposta ausentes")
                return
            token_captcha = self.token_desafio
            url_documentos = f"{URL_DOCUMENTOS}?tokenCaptcha={token_captcha}"
            print(f"Requisitando documentos na URL: {url_documentos}")

            resposta = self.sessao.get(url_documentos)
            resposta.raise_for_status()

            conteudo_json = resposta.json()
            documentos = conteudo_json.get("documentos", [])
            print(f"Total de documentos coletado: {len(documentos)}")
            for doc in documentos:
                print(json.dumps(doc, indent=4, ensure_ascii=False))
        except Exception as e:
            print(f"Erro ao coletar os documentos: {e}")

    
    def converter_base64_para_jpeg(self, base64_string, captcha_nome="captcha_imagem.jpeg"):
        """Convertento img Base64 para Jpeg"""
        try:
            pasta_imagem = "images"
            os.makedirs(pasta_imagem, exist_ok=True)

            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string

            imagem = Image.open(BytesIO(base64.b64decode(base64_string)))

            caminho_arquivo = os.path.join(pasta_imagem, captcha_nome)
            imagem.save(caminho_arquivo, "JPEG")
            print(f"Imagem salva na pasta Images: {caminho_arquivo}")
        except Exception as e:
            print(f"Erro ao salvar a imagem: {e}")
    

    def resolver_captcha(self, base64_string):
        """Resolvendo o Captcha"""
        try:
            base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
            resposta = solve_captcha_local(base64_string)
            self.resposta_captcha = resposta
            print(f"Resposta do Captcha: {self.resposta_captcha}")
            return resposta
        except Exception as e:
            print(f"Erro ao resolver o Captcha: {e}")
            self.resposta_captcha = None

    
    def enviar_resposta_captcha(self):
        """Enviando a resposta do Captcha ao servidor"""
        try:
            if not self.resposta_captcha or not self.token_desafio:
                print("Captcha ou token do desafion ausente")
                return
            
            payload = {"resposta": self.resolver_captcha, "tokenDesafion": self.token_desafio}
            headers = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
                'User-Agent': 'Mozilla/5.0'
            }
            print("Eviando payload,", payload)
            print("Eviando o hearders:", headers)

            resposta = self.sessao.post(URL_CAPTCHA, json=payload, headers=headers)
            print(f"Resposta do servidor: {resposta.status_code} - {resposta.text}")

            if resposta.status_code == 405:
                print("Metodo HTTP não permitido.")
        except Exception as e:
            print(f"Erro ao enviar a resposta captcha: {e}")


    def enviar_documento(self):
        """Realiza o POST para enviar o documento com o token e a resposta do captcha."""
        try:
            if not self.token_desafio or not self.resposta_captcha:
                print("Token de desafio ou resposta do captcha ausente.")
                return
            url_post = (
                f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
            )
            print(f"URL montada para o POST: {url_post}")
            payload = {
                "resposta": self.resposta_captcha, 
                "tokenDesafio": self.token_desafio 
            }
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Content-Type': 'application/json',
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
                'Referer': URL_BASE,
                'Origin': 'https://pje.trt2.jus.br',
                'Authorization': f"Bearer {self.token_desafio}",
                'Cache-Control': 'no-cache',
            }
            resposta = self.sessao.post(url_post, json=payload, headers=headers)
            print(f"Resposta do servidor: {resposta.status_code} - {resposta.text}")

            if resposta.status_code == 200:
                print("POST realizado com sucesso.")
                return resposta.json()
            else:
                print(f"Erro ao realizar POST: {resposta.status_code} - {resposta.text}")
        except Exception as e:
            print(f"Erro ao enviar o documento: {e}")


            
                
    def inciando_sessao(self):
        """Fluxo de iniciar a Sessão"""
        try:
            print("Iniciando a Sessão")

            '''cookies = self.obter_cookie(URL_BASE)
            if cookies:
                print(f"Cookies coletados: {cookies}")
            else:
                print("Erro ao coletar o Cookie")'''
            
            self.fazer_requisicao_hearders(URL_CAPTCHA)

            if self.token_desafio and self.resposta_captcha:
                self.obter_documentos()
                print(f"Token de desafio obtido: {self.token_desafio}")
            else:
                print("Erro ao encotrar o Token")
            
            self.enviar_resposta_captcha()

            self.enviar_documento()



            html_final = self.sessao.get(URL_BASE).text
            if html_final:
                print('Sessão inicializada corretamente')
            else:
                print("Falha ao inicializar a Pagina")
        except Exception as e:
            print(f"Erro ao iniciar a Sessção: {e}")


sessao = SessaoJurisprudencia()
sessao.inciando_sessao()
            