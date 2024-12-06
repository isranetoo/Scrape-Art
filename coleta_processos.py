import json

arquivo_entrada = "processos.json"
arquivo_saida = "informacoes_processos.json"

def coletar_informacoes(arquivo, campos_para_coletar):
    """
        Coletando as informações espesificas de um arquivo JSON.

        Args:
            arquivo (str): Nome do arquivo JSON.
            campos_para_coletar (list): Lista de campos a serem extraidos.

        returns:
            list: Lista de dicíonario com as informações coletadas
    """
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if isinstance(dados, dict) and "documents" in dados:
                documentos = dados["documents"]
                infomacoes = []
                for doc in documentos:
                    entrada = {campo: doc.get(campo, "Não disponível") for campo in campos_para_coletar}
                    infomacoes.append(entrada)
            else:
                raise ValueError("Formato JSON não encotrado ou chave 'documents' ausente")
            
        return infomacoes
    except FileNotFoundError:
        print(f"Erro: O arquivo '{arquivo}' não foi encotrado.")
        return []
    except json.JSONEncoder:
        print(f"Erro: o arquivo '{arquivo}' não contém um JSON válido")
        return []
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return []
    
def salvar_informacoes_em_arquivo(informacoes, arquivo):
        """
            Salvar informações coletadas em um arquivo JSON.

            Args:
                informacoes (list): Lista de informações coletadas.
                arquivo (str): Nome do arquivo de sáida.
        """
        try:
            with open(arquivo, 'w', encoding='utf-8') as f:
                json.dump({"documents": informacoes}, f, ensure_ascii=False, indent=4)
            print(f"Informações salvas com \033[1;32mSUCESSO\033[0m no arquivo \033[1;34m'{arquivo}'\033[0m")
        except Exception as e:
            print(f"Erro ao salvar as informações: {e}")
    
if __name__ == "__main__":
    campos = ["sigiloso","anoProcesso","tipoDocumento","dataDistribuicao", "instancia", "processo", "orgaoJulgador", "magistrado", "classeJudicialSigla", "classeJudicial", "dataPublicacao",]
    informacoes = coletar_informacoes(arquivo_entrada, campos)
    if informacoes:
        salvar_informacoes_em_arquivo(informacoes, arquivo_saida)
    else:
        print("Nenhum informação encotrada para salvar.")

