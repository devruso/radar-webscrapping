#!/usr/bin/env python3
"""
Ponto de entrada principal da aplicação radar-webscrapping.

Script para executar diferentes interfaces e operações do sistema
seguindo princípios de Clean Architecture.
"""

import sys
import asyncio
from pathlib import Path

# Adicionar src ao path para imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.interfaces.cli.CursoController import cli


if __name__ == "__main__":
    """Executa a interface CLI."""
    try:
        cli()
    except KeyboardInterrupt:
        print("\nOperação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)