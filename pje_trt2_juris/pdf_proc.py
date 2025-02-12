import requests
from captcha_local_solver import solve_captcha_local
import json

class PdfProcessor:
    def __init__(self, link_id):
        self.URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
        self.URL_PAGE = f'https://pje.trt2.jus.br/juris-backend/api/documentos/{link_id}'
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.cookies = {}

    def fazer_requisicao_captcha(self):
        """Fazer a requisicao do captcha para ser resolvido (GET)"""
        try:
            resposta = self.sessao.get(self.URL_CAPTCHA, headers={'Accept': 'application/json'})
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

    def acessar_pagina(self):
        """Acessa a página inicial"""
        try:
            resposta = self.sessao.post(self.URL_PAGE)
            resposta.raise_for_status()
            return True
        except Exception as e:
            print(f"Erro ao acessar a página inicial: {e}")
            return False

    def acessar_pagina_com_captcha(self):
        """Acessa a página protegida pelo CAPTCHA"""
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

    def extrair_dados_especificos(self, pagina_json):
        """Extrai dados específicos do JSON"""
        dados = {
            "poloAtivo": "",
            "poloPassivo": "",
            "classeJudicial": "",
            "anoProcesso": "",
            "tipoDocumento": ""
        }
        
        try:
            conteudo = json.loads(pagina_json)
            
            dados["poloAtivo"] = ", ".join(conteudo.get("poloAtivo", []))
            dados["poloPassivo"] = ", ".join(conteudo.get("poloPassivo", []))
            dados["classeJudicial"] = conteudo.get("classeJudicial", "")
            dados["anoProcesso"] = conteudo.get("anoProcesso", "")
            dados["tipoDocumento"] = conteudo.get("tipoDocumento", "")
                
            return dados
        except Exception as e:
            print(f"Erro ao extrair dados específicos: {e}")
            return dados

    def coletar_informacoes(self, pagina_json):
        """Coleta as informações específicas da página"""
        try:
            dados_especificos = self.extrair_dados_especificos(pagina_json)
            return dados_especificos, pagina_json
        except Exception as e:
            print(f"Erro ao coletar informações: {e}")
            return {}, None

    def processar(self):
        """Executa o fluxo principal de processamento"""
        if self.acessar_pagina():
            pagina_html = self.acessar_pagina_com_captcha()
            if pagina_html:
                dados_especificos, _ = self.coletar_informacoes(pagina_html)
                print("Informações coletadas:")
                for chave, valor in dados_especificos.items():
                    print(f"{chave}: {valor}")
                return dados_especificos
            else:
                print("Falha em resolver o CAPTCHA repetidamente. Finalizando...")
                return None
        return None

def main(link_ids=None):
    try:
        if link_ids is None:
            print("Nenhum link_id fornecido para processamento!")
            return
        
        all_processed_data = {}
            
        for link_id in link_ids:
            print(f"\nProcessando ID: {link_id}")
            processor = PdfProcessor(link_id)
            result = processor.processar()
            if result:
                all_processed_data[link_id] = result
        
        
        with open("dados_especificos.json", "w", encoding="utf-8") as f:
            json.dump(all_processed_data, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()
