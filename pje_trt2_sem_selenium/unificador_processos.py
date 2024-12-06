import json
import os

def coletar_documentos(pasta_origem, arquivo_saida):
    documentos_unificados = {"documents": []}
    arquivo_json = [f for f in os.listdir(pasta_origem) if f.endswith('.json')]
    for arquivo in arquivo_json:
        caminho_arquivo = os.path.join(pasta_origem, arquivo)
        try:
            with open(caminho_arquivo, 'r', encoding='utf-8') as f:
                conteudo = json.load(f)
                if "documents" in conteudo:
                    documentos_unificados['documents'].extend(conteudo["documents"])
        except Exception as e:
            print(f"Erro ao processar o arquivo {arquivo}: {e}")

        try:
            with open(arquivo_saida, 'w', encoding='utf-8') as f:
                json.dump(documentos_unificados, f, ensure_ascii=False, indent=4)
            print(f"Arquivo unificado salvos em: {arquivo_saida}")
        except Exception as e:
            print(f"Erro ao salvar o arquivo unificado: {e}")

pasta_origem = "documentos"
arquivo_saida = "processos_unificados.json"

coletar_documentos(pasta_origem, arquivo_saida)