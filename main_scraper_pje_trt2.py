import subprocess
import os

def executar_script(script_path):
    try:
        print(f"Executando {script_path}...")
        result = subprocess.run(["python", script_path], check=True)
        print(f"{script_path} executado com sucesso!")
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar {script_path}: {e}")
        return False
    return True

def main():
    pasta_scripts = "pje_trt2_sem_selenium"
    scripts = [
        "pje_trt2_scrape_cookies.py",
        "unificador_processos.py",
        "coleta_processos.py"
    ]
    scripts_com_caminho = [os.path.join(pasta_scripts, script) for script in scripts]
    
    for script_path in scripts_com_caminho:
        if not executar_script(script_path):
            print("Encerrando execução devido a um erro.")
            break

if __name__ == "__main__":
    main()
