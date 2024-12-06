import json


arquivo_json = 'processos.json'

def coletar_informacoes_processo(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8') as f:
            dados = json.load(f)
            if isinstance(dados, list):
                processos = [item.get("processo") for item in dados if "processo" in item]
            elif isinstance(dados, dict):
                processos = [dados.get("processo")] if "processo" in dados else []
            else:
                raise ValueError("Formato JSON não reconhecido")
            
        return processos
    except FileExistsError:
        print(f"Erro: O arquivo '{arquivo}' não foi encontrado.")
        return []
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{arquivo}' não contém um JSON válido.")
        return []
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    informacoes_processo = coletar_informacoes_processo(arquivo_json)
    if informacoes_processo:
        print("Informações encotradas no campo 'processo':")
        for idx, processo in enumerate(informacoes_processo, start=1):
            print(f"{idx}. {processo}")
    else:
        print("Nenhuma informacões encotrada no campo 'processo'")