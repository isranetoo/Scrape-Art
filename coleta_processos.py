import json

arquivo_json = "processos.json"

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
                    entrada = {}
                    for campo in campos_para_coletar:
                        entrada[campo] = doc.get(campo, "Não disponível")
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
    
if __name__ == "__main__":
    campos = ["processo", "anoProcesso", "classeJudicial", "dataPublicacao"]
    informacoes = coletar_informacoes(arquivo_json, campos)
    if informacoes:
        print("Informações coletadas:")
        for idx, info in enumerate(informacoes, start=1):
            detalhes = " - ".join([f"{campo}: {valor}" for campo, valor in info.items()])
            print(f"{idx}. {detalhes}")
    else:
        print("Nenhum informação encotrada.")

