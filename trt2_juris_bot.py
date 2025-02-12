import requests
import json
import os
from datetime import datetime
from pje_trt2_juris.captcha_local_solver import solve_captcha_local
from pje_trt2_juris.parsing import parse_cnj
from lxml import etree

URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
PASTA_DOCUMENTOS = "processos"
ARQUIVO_INFORMACOES = "informacoes_processos_completo.json"

class BasePJEProcessor:
    """Base class with common functionality for both processors"""
    def __init__(self):
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.cookies = {}

    def fazer_requisicao_captcha(self):
        """Fazer a requisicao do captcha para ser resolvido (GET)"""
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers={'Accept': 'application/json'})
            resposta.raise_for_status()
            dados = resposta.json()
            self.token_desafio = dados.get('tokenDesafio')
            self.resolver_captcha(dados.get('imagem'))
            return True
        except Exception as e:
            print(f"Erro ao obter o CAPTCHA: {e}")
            return False

    def resolver_captcha(self, base64_string):
        """Resolve o CAPTCHA usando o solver local"""
        try:
            if base64_string:
                base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
                self.resposta_captcha = solve_captcha_local(base64_string)
                print(f"Resposta do CAPTCHA: \033[1;32m{self.resposta_captcha}\033[0m")
                self.configurar_cookies()
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")

    def configurar_cookies(self):
        """Configura os cookies da sessão"""
        self.cookies = {
            "_ga": "GA1.3.2135935613.1731417901",
            "respostaDesafio": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
        }
        self.sessao.cookies.update(self.cookies)

class DocumentProcessor(BasePJEProcessor):
    """Processor for individual documents"""
    def __init__(self, link_id):
        super().__init__()
        self.URL_PAGE = f'{URL_DOCUMENTOS}/{link_id}'

    def processar(self):
        """Processa um documento específico"""
        max_tentativas = 10
        for tentativa in range(max_tentativas):
            if not self.fazer_requisicao_captcha():
                continue

            try:
                url_post = f"{self.URL_PAGE}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
                resposta = self.sessao.post(url_post)
                resposta.raise_for_status()

                if "A resposta informada é incorreta" in resposta.text:
                    print("\033[1;31mCAPTCHA incorreto.\033[0m Gerando novo...")
                    continue

                return resposta.text

            except Exception as e:
                print(f"Erro na tentativa {tentativa + 1}: {e}")

        return None

class Bot_trt2_pje_juris(BasePJEProcessor):
    """Bot principal para pesquisa de jurisprudência"""
    def __init__(self, assunto: str, procs_por_pagina: int, max_paginas: int = 0):
        super().__init__()
        self.assunto = assunto
        self.procs_por_pagina = int(procs_por_pagina)
        self.max_paginas = max_paginas
        self.url_post = None

    def enviar_documento(self, pagina):
        """Envia os itens necessarios para a coleta dos processos"""
        payload = {
            "resposta": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
            "name": "query parameters",
            "andField": [self.assunto],
            "paginationPosition": pagina,
            "paginationSize": self.procs_por_pagina,
            "fragmentSize": 512,
            "ordenarPor": "dataPublicacao",
        }
        try:
            resposta = self.sessao.post(self.url_post, json=payload, headers={'Content-Type': 'application/json'})
            timestamp = datetime.now().strftime("%d-%m-%Y")
            if resposta.status_code == 200:
                documentos = resposta.json()
                if documentos.get("mensagem") == "A resposta informada é incorreta":
                    print("\033[1;31mCAPTCHA incorreto.\033[0m Gerando novo...")
                    self.url_post = None
                else:
                    nome_arquivo = f"assunto_{self.assunto}_pagina_{pagina}_data_{timestamp}.json"
                    self.salvar_em_arquivo(PASTA_DOCUMENTOS, nome_arquivo, documentos)
                    return True
        except Exception as e:
            print(f"Erro ao processar a página {pagina}: {e}")
        return False
    

def process_documents():
    """Process specific documents using link IDs"""
    try:
        with open('link_ids.json', 'r') as file:
            data = json.load(file)
            link_ids = data.get('link_ids', [])
        
        all_processed_data = {}
        
        for link_id in link_ids:
            print(f"\nProcessando ID: {link_id}")
            processor = DocumentProcessor(link_id)
            result = processor.processar()
            if result:
                all_processed_data[link_id] = result
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        with open(f"dados_especificos_{timestamp}.json", "w", encoding="utf-8") as f:
            json.dump(all_processed_data, f, ensure_ascii=False, indent=2)
            
    except FileNotFoundError:
        print("Arquivo link_ids.json não encontrado!")
    except json.JSONDecodeError:
        print("Erro ao decodificar o arquivo JSON!")
    except Exception as e:
        print(f"Erro inesperado: {e}")

def main():
    """Unified main function with menu system"""
    print("\033[1;36m=== Sistema PJE TRT2 ===\033[0m")
    print("1. Pesquisar jurisprudência")
    print("2. Processar PDFs específicos")
    
    opcao = input("\nEscolha uma opção (1 ou 2): ")
    
    if opcao == "1":
        procs_por_pagina = input("Digite o número de processos por página: ")
        assunto = input("Digite o assunto de interesse: ")
        sessao = Bot_trt2_pje_juris(assunto, procs_por_pagina)
        sessao.run()
    
    elif opcao == "2":
        process_documents()
    
    else:
        print("Opção inválida!")

if __name__ == "__main__":
    main()
