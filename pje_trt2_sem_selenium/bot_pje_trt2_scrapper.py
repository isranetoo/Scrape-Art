import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from captcha_local_solver import solve_captcha_local
from parsing import parse_cnj
from lxml import etree

URL_CAPTCHA = 'https://pje.trt2.jus.br/juris-backend/api/captcha'
URL_DOCUMENTOS = 'https://pje.trt2.jus.br/juris-backend/api/documentos'
PASTA_DOCUMENTOS = "processos"
ARQUIVO_UNIFICADO = "processos_unificados.json"
ARQUIVO_INFORMACOES = "informacoes_processos_completo.json"

class Bot_trt2_pje_scrape:
    def __init__(self, assunto: str, procs_por_pagina: int, max_paginas: int = 10):
        """ Classe para pesquisa de jurisprudência no TRT 2. 

        Arquivos: 
            processos: pasta com todos o processos unificados com o filtro
            processos_unificados.json: Arquivo com todos os processos sem filtro
            informacoes_processos_completo.json: 
        Args: 
            assunto: Assunto para pesquisa interessada
            procs_por_pagina: Processos por pagina para ser pesquisado
            max_paginas: numero de paginas a ser pesquisada
        
        """
        self.assunto = assunto
        self.procs_por_pagina = int(procs_por_pagina)
        self.max_paginas = max_paginas
        self.sessao = requests.Session()
        self.token_desafio = None
        self.resposta_captcha = None
        self.url_post = None
        self.cookies = {}

    def fazer_requisicao_captcha(self):
        """Fazer a requisicao do captcha para ser resolvido (GET)"""
        try:
            resposta = self.sessao.get(URL_CAPTCHA, headers={'Accept': 'application/json'})
            resposta.raise_for_status()
            dados = resposta.json()
            self.token_desafio = dados.get('tokenDesafio')
            self.resolver_captcha(dados.get('imagem'))
        except Exception as e:
            print(f"Erro ao obter o CAPTCHA: {e}")

    def resolver_captcha(self, base64_string):
        """Resolve o CAPTCHA com o solver_captcha_local"""
        try:
            if base64_string:
                base64_string = base64_string.split(',')[1] if base64_string.startswith('data:image') else base64_string
                self.resposta_captcha = solve_captcha_local(base64_string)
                print(f"Resposta do CAPTCHA: \033[1;32m{self.resposta_captcha}\033[0m")
                self.url_post = f"{URL_DOCUMENTOS}?tokenDesafio={self.token_desafio}&resposta={self.resposta_captcha}"
                self.configurar_cookies()
        except Exception as e:
            print(f"Erro ao resolver o CAPTCHA: {e}")

    def configurar_cookies(self):
        """Configura e salva o cookie da sessão"""
        self.cookies = {
            "_ga": "GA1.3.2135935613.1731417901",
            "respostaDesafio": self.resposta_captcha,
            "tokenDesafio": self.token_desafio,
        }
        self.sessao.cookies.update(self.cookies)

    def salvar_em_arquivo(self, pasta, nome_arquivo, conteudo):
        """Salva os arquivos necessario do programa"""
        os.makedirs(pasta, exist_ok=True)
        caminho = os.path.join(pasta, nome_arquivo)
        try:
            with open(caminho, 'w', encoding='utf-8') as arquivo:
                json.dump(conteudo, arquivo, ensure_ascii=False, indent=4)
            print(f"Arquivo salvo em: {caminho}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo: {e}")

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

    def coletar_links_processos(self, pagina_html):
        """Coleta os links dos processos da página de resultados"""
        try:
            parser = etree.HTMLParser()
            tree = etree.fromstring(pagina_html, parser)
            links_processos = []
            for i in range(1, 5):  
                xpath = f'//*[@id="divListaResultados"]/mat-list-item[{i}]/div/div[2]/div[1]/a'
                link = tree.xpath(xpath)
                if link:
                    links_processos.append(link[0].get('href'))
            return links_processos
        except Exception as e:
            print(f"Erro ao coletar links dos processos: {e}")
            return []

    def iniciar_sessao(self):
        """Inicia a sessão na ordem correta necessaria para o programa funcionar"""
        print("\033[1;33m==== Iniciando a Sessão ====\033[0m")
        pagina, retries, max_retries = 1, 1, 5
        while pagina <= self.max_paginas:
            if not self.url_post:
                if retries > max_retries:
                    raise Exception("Falha em resolver o CAPTCHA repetidamente. Finalizando...")
                self.fazer_requisicao_captcha()

            if self.url_post and self.enviar_documento(pagina):
                print(f"Página \033[34m{pagina}\033[0m processada com sucesso!")
                pagina_html = self.sessao.get(self.url_post).text
                links_processos = self.coletar_links_processos(pagina_html)
                for link in links_processos:
                    self.obter_detalhes_processo(link)
                pagina += 1
                retries = 1
            else:
                retries += 1

    def obter_detalhes_processo(self, link_processo):
        """Entra no link do processo para obter detalhes como reclamantes e valor da causa"""
        try:
            self.fazer_requisicao_captcha()  
            url_final = f"https://pje.trt2.jus.br{link_processo}"
            resposta = self.sessao.get(url_final, headers={'Accept': 'application/json'})
            resposta.raise_for_status()
            pagina = resposta.text

            parser = etree.HTMLParser()
            tree = etree.fromstring(pagina, parser)

            cnpj = tree.xpath('//*[@id="inteiroTeorHTML"]/main/div/div[1]/ul[1]/li[1]/text()')
            cpf1 = tree.xpath('//*[@id="inteiroTeorHTML"]/main/div/div[1]/ul[1]/li[2]/text()')
            cpf2 = tree.xpath('//*[@id="inteiroTeorHTML"]/main/div/div[1]/ul[1]/li[3]/text()')

            cnpj = cnpj[0].strip() if cnpj else "N/A"
            cpf1 = cpf1[0].strip() if cpf1 else "N/A"
            cpf2 = cpf2[0].strip() if cpf2 else "N/A"

            print(f"CNPJ: {cnpj}")
            print(f"CPF 1: {cpf1}")
            print(f"CPF 2: {cpf2}")

        except Exception as e:
            print(f"Erro ao obter detalhes do processo: {e}")

def coletar_documentos(pasta_origem, arquivo_saida):
    """Coleta as paginas dos processos e as unifica em um unico arquivo processos_unificados.json """
    documentos_unificados = {"documents": []}
    arquivos_json = [f for f in os.listdir(pasta_origem) if f.endswith('.json')]
    for arquivo in arquivos_json:
        try:
            with open(os.path.join(pasta_origem, arquivo), 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                documentos_unificados["documents"].extend(conteudo.get("documents", []))
        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {e}")

    with open(arquivo_saida, 'w', encoding='utf-8') as f:
        json.dump(documentos_unificados, f, ensure_ascii=False, indent=4)
    print(f"Documentos unificados salvos em: \033[32m{arquivo_saida}\033[0m")

def coletar_informacoes(arquivo_entrada, campos, arquivo_saida):
    """
    Coleta as informações do processos_unificados.json e as filtra em outro arquivo JSON informacoes_processos_completo.json
    com o formato BD e valores nulos para campos ausentes.
    """
    try:
        with open(arquivo_entrada, 'r', encoding='utf-8') as f:
            dados = json.load(f).get("documents", [])

        informacoes_completas = []
        for doc in dados:
            numero_processo = doc.get("processo", None)
            area_code, tribunal_code, vara_code, ano, area, tribunal = parse_cnj(numero_processo) if numero_processo else (None, None, None, None, None, None)
            informacoes = {
                "numero": numero_processo,
                "area_code": area_code,
                "tribunal_code": tribunal_code,
                "vara_code": vara_code,
                "ano": ano,
                "area:": area,
                "tribunal": tribunal,
                "comarca": None,
                "valor_causa": doc.get("valorCausa", None),
                "moeda_causa": "R$",
                "fontes": [
                    {
                        "provider": "Interno",
                        "provider_fonte_id": "Interno",
                        "sigla": doc.get("sistema", "PJE-TRT2"),
                        "sistema": "PJE",
                        "tipo": "TRIBUNAL",
                        "instancias": [
                            {
                                "url": "https://pje.trt2.jus.br/jurisprudencia/",
                                "grau": doc.get("instancia", None),
                                "classe": doc.get("classeJudicialSigla", None),
                                "orgao_julgador": doc.get("orgaoJulgador", None),
                                "justica_gratuita": doc.get("justicaGratuita", None),
                                "assunto_principal": doc.get("assunto", [None])[0],
                                "assuntos": doc.get("assunto", []),
                                "envolvidos": [
                                    {
                                        "nome": doc.get("poloAtivo", None),
                                        "tipo": doc.get("reclamante", "RECLAMANTE"),
                                        "polo": doc.get("polo", "ATIVO"),
                                        "id_sistema": {
                                            "login": None,
                                        },
                                        "documento": [
                                            {"tipo": "CPF", "uf": None, "valor": None}
                                        ],
                                        "endereco": {},
                                        "representantes": [
                                            {
                                                "nome": doc.get("nome_adv", None),
                                                "tipo": "ADVOGADO",
                                                "polo": "ATIVO",
                                                "id_sistema": {
                                                    "login": None,
                                                },
                                                "documento": [
                                                    {"tipo": "CPF", "uf": None, "valor": doc.get("cpf", None)},
                                                    {"tipo": "RG", "uf": None, "valor": None},
                                                    {"tipo": "OAB-ADVOGADO", "uf": None, "valor": None}
                                                ],
                                                "endereco": {
                                                    "logradouro": doc.get("longradouro", None),
                                                    "numero": doc.get("numero", None),
                                                    "complemento": doc.get("complemento", None),
                                                    "bairro": doc.get("bairro", None),
                                                    "municipio": doc.get("municipio", None),
                                                    "estado": doc.get("estado", None),
                                                    "cep": doc.get("cep", None),
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "nome": doc.get("poloPassivo", None), 
                                        "tipo": doc.get("reclamado", "RECLAMADO"),
                                        "polo": doc.get("polo", "PASSIVO"),
                                        "id_sistema": {
                                            "login": None,
                                        },
                                        "documento": [
                                            {"tipo": "CPF", "uf": None, "valor": None}
                                        ],
                                        "endereco": {},
                                        "representantes": [
                                            {
                                                "nome": doc.get("nome_adv", None),
                                                "tipo": "ADVOGADO",
                                                "polo": "PASSIVO",
                                                "id_sistema": {
                                                    "login": None
                                                },
                                                "documento": [
                                                    {"tipo": "CPF", "uf": None, "valor": None},
                                                    {"tipo": "RG", "uf": None, "valor": None},
                                                    {"tipo": "OAB-ADVOGADO", "uf": None, "valor": None}
                                                ],
                                                "endereco": {
                                                    "logradouro": None,
                                                    "numero": None,
                                                    "complemento": None,
                                                    "bairro": None,
                                                    "municipio": None,
                                                    "estado": None,
                                                    "cep": None
                                                }
                                            }
                                        ]
                                    },
                                    {
                                        "nome": doc.get("nome_perito", None),
                                        "tipo": "PERITO",
                                        "polo": doc.get("polo", "OUTROS"),
                                        "id_sistema": {
                                            "login": None
                                        },
                                        "documento": [],
                                        "endereco": {},
                                        "representantes": []
                                    }
                            ],
                            "movimentacoes": doc.get("movimentacoes", [
                                {
                                    "titulo": doc.get("movimentoDecisao", None),
                                    "tipoConteudo": doc.get("html", None),
                                    "data": doc.get("dataPublicacao", None),
                                    "ativo": doc.get("ativo", None),
                                    "documento": doc.get("f_ou_t", None),
                                    "mostrarHeaderData": doc.get("header_data", None),
                                    "usuarioCriador": doc.get("usuarioCriador", None),
                                },
                                {
                                    "titulo": doc.get("titulo", None),
                                    "tipoConteudo": doc.get("html", None),
                                    "data": doc.get("dataPublicacao", None),
                                    "ativo": doc.get("ativo", None),
                                    "documento": doc.get("f_ou_t", None),
                                    "mostrarHeaderData": doc.get("header_data", None),
                                    "usuarioCriador": doc.get("usuarioCriador", None),
                                },
                                {
                                    "id": doc.get("id", None),
                                    "idUnicoDocumento": doc.get("idUnicoDocumento", None),
                                    "titulo": doc.get("titulo", None),
                                    "tipo": doc.get("tipoDocumento", None),
                                    "tipoConteudo": doc.get("tipoConteudo","RTF"),
                                    "data": doc.get("dataPublicacao", None),
                                    "ativo": doc.get("ativo", None),
                                    "documentoSigiloso": doc.get("sigiloso", None),
                                    "usuarioPerito": doc.get("usuarioPerito", None),
                                    "documento": doc.get("tipo_doc", None),
                                    "publico": doc.get("tipo_publico", None),
                                    "usuarioJuntada": doc.get("usuarioJuntada", None),
                                    "usuarioCriador": doc.get("usuarioCriador", None),
                                    "instancia": doc.get("instancia", None)
                                }
                            ])
                            }
                        ]
                    }
                ],
                #"juizoDigital": doc.get("meioTramitacao", None),
                #"segredoJustica": doc.get("sigiloso", None),
            }
            informacoes_completas.append(informacoes)

        with open(arquivo_saida, 'w', encoding='utf-8') as f:
            json.dump(informacoes_completas, f, ensure_ascii=False, indent=4)
        print(f"Informações salvas em: \033[32m{arquivo_saida}\033[0m")
    except Exception as e:
        print(f"Erro ao processar informações: {e}")

if __name__ == "__main__":
    procs_por_pagina = input("Digite o número de processos por página: ")
    assunto = input("Digite o assunto de interesse: ")
    sessao = Bot_trt2_pje_scrape(assunto, procs_por_pagina)
    sessao.iniciar_sessao()

    coletar_documentos(PASTA_DOCUMENTOS, ARQUIVO_UNIFICADO)
    campos = ["sigiloso", "anoProcesso", "tipoDocumento",  "instancia", "dataDistribuicao", "processo", "classeJudicial",  "classeJudicialSigla", "dataPublicacao", "orgaoJulgador", "magistrado"]
    coletar_informacoes(ARQUIVO_UNIFICADO, campos, ARQUIVO_INFORMACOES)
