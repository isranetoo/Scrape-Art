import json
import hashlib

def generate_hash(numero):
    return hashlib.md5(numero.encode()).hexdigest()

try:
    # Read dados_especificos.json
    dados_path = r'C:\Users\IsraelAntunes\OneDrive\pje_trt2\dados_especificos.json'
    with open(dados_path, 'r', encoding='utf-8') as f:
        dados_especificos = json.load(f)
        print(f"Successfully loaded dados_especificos.json")

    # Read informacoes_processos_completo.json
    processos_path = r'C:\Users\IsraelAntunes\OneDrive\pje_trt2\informacoes_processos_completo.json'
    with open(processos_path, 'r', encoding='utf-8') as f:
        processos = json.load(f)
        print(f"Successfully loaded informacoes_processos_completo.json")

    # Counter for tracking updates
    updates_count = 0

    # Update each process
    for processo in processos:
        hash_id = generate_hash(processo['numero'])
        
        if hash_id in dados_especificos:
            polo_ativo = dados_especificos[hash_id]['poloAtivo']
            
            for instancia in processo['fontes'][0]['instancias']:
                for envolvido in instancia['envolvidos']:
                    if envolvido['tipo'] == 'RECLAMANTE' and envolvido['polo'] == 'ATIVO':
                        envolvido['nome'] = [polo_ativo]
                        updates_count += 1
                        print(f"Updated processo {processo['numero']} with {polo_ativo}")

    # Save the updated data
    if updates_count > 0:
        with open(processos_path, 'w', encoding='utf-8') as f:
            json.dump(processos, f, ensure_ascii=False, indent=4)
            print(f"Successfully saved {updates_count} updates to the file")
    else:
        print("No updates were needed")

except Exception as e:
    print(f"An error occurred: {str(e)}")

print("Process completed!")

