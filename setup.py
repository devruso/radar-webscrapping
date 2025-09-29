"""
Script para configurar e instalar o ambiente de desenvolvimento.

Execute este script para:
1. Instalar dependências Python
2. Configurar navegadores Playwright
3. Verificar configuração
"""
import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description):
    """Executa um comando e exibe o resultado"""
    print(f"\n🔄 {description}")
    print(f"Executando: {command}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ {description} - Concluído")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Erro:")
        print(f"Código de saída: {e.returncode}")
        print(f"Erro: {e.stderr}")
        return False


def main():
    """Função principal de setup"""
    print("🚀 Configurando ambiente Radar Web Scraping")
    print("=" * 50)
    
    # 1. Atualizar pip
    if not run_command("python -m pip install --upgrade pip", "Atualizando pip"):
        return False
    
    # 2. Instalar dependências
    if not run_command("pip install -r requirements.txt", "Instalando dependências Python"):
        return False
    
    # 3. Instalar navegadores Playwright
    if not run_command("playwright install", "Instalando navegadores Playwright"):
        return False
    
    # 4. Instalar dependências do sistema para Playwright
    if not run_command("playwright install-deps", "Instalando dependências do sistema"):
        print("⚠️  Algumas dependências do sistema podem não ter sido instaladas")
        print("    Isso é normal no Windows - os navegadores devem funcionar")
    
    # 5. Verificar instalação
    print("\n🔍 Verificando instalação:")
    print("✅ Python:", sys.version)
    print("✅ Diretório atual:", os.getcwd())
    print("✅ Arquivos do projeto:", os.path.exists("src"))
    
    print("\n🎉 Setup concluído!")
    print("\nPróximos passos:")
    print("1. Configure as variáveis de ambiente no arquivo .env")
    print("2. Execute: python run.py")
    print("3. Acesse: http://localhost:8000")


if __name__ == "__main__":
    main()