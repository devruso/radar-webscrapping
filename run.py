"""
Arquivo principal de inicialização do projeto Radar Web Scraping.

Este arquivo serve como ponto de entrada principal da aplicação,
inicializando todos os componentes necessários.
"""
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Agora podemos importar os módulos do projeto
from src.main import app, run_api

if __name__ == "__main__":
    # Executar API em modo desenvolvimento
    run_api(
        host="localhost",
        port=8000,
        reload=True
    )