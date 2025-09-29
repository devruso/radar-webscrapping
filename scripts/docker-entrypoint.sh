#!/bin/bash

# ===============================================================================
# Docker Entrypoint Script para Radar WebScrapping
# ===============================================================================

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para logging
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# ===============================================================================
# CONFIGURAÇÕES INICIAIS
# ===============================================================================

log "🚀 Iniciando Radar WebScrapping Container"

# Definir variáveis padrão se não existirem
export PYTHONPATH="${PYTHONPATH:-/app/src}"
export APP_ENV="${APP_ENV:-production}"
export LOG_LEVEL="${LOG_LEVEL:-INFO}"
export SELENIUM_HEADLESS="${SELENIUM_HEADLESS:-true}"

log "📋 Configurações do ambiente:"
log "   - APP_ENV: $APP_ENV"
log "   - LOG_LEVEL: $LOG_LEVEL"
log "   - PYTHONPATH: $PYTHONPATH"
log "   - SELENIUM_HEADLESS: $SELENIUM_HEADLESS"

# ===============================================================================
# VALIDAÇÕES DO AMBIENTE
# ===============================================================================

log "🔍 Validando ambiente..."

# Verificar se Chrome está instalado
if ! command -v google-chrome &> /dev/null; then
    error "Google Chrome não encontrado!"
    exit 1
fi

# Verificar se ChromeDriver está instalado
if ! command -v chromedriver &> /dev/null; then
    error "ChromeDriver não encontrado!"
    exit 1
fi

# Verificar versões
CHROME_VERSION=$(google-chrome --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")
CHROMEDRIVER_VERSION=$(chromedriver --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+")

log "✅ Chrome: $CHROME_VERSION"
log "✅ ChromeDriver: $CHROMEDRIVER_VERSION"

# ===============================================================================
# PREPARAÇÃO DE DIRETÓRIOS
# ===============================================================================

log "📁 Preparando diretórios..."

# Criar diretórios necessários
mkdir -p /app/data
mkdir -p /app/logs
mkdir -p /tmp/selenium

# Definir permissões
chmod 755 /app/data
chmod 755 /app/logs
chmod 777 /tmp/selenium

log "✅ Diretórios preparados"

# ===============================================================================
# CONFIGURAÇÃO DO SELENIUM
# ===============================================================================

log "🔧 Configurando Selenium..."

# Configurar display virtual se não existir
if [ -z "$DISPLAY" ]; then
    export DISPLAY=:99
    log "   - DISPLAY configurado: $DISPLAY"
fi

# Configurar variáveis do Chrome
export CHROME_BIN="${CHROME_BIN:-/usr/bin/google-chrome}"
export CHROME_PATH="${CHROME_PATH:-/usr/bin/google-chrome}"
export CHROMEDRIVER_PATH="${CHROMEDRIVER_PATH:-/usr/local/bin/chromedriver}"

log "✅ Selenium configurado"

# ===============================================================================
# VALIDAÇÃO DA APLICAÇÃO
# ===============================================================================

log "🧪 Validando aplicação Python..."

# Testar importação básica
python3 -c "
import sys
sys.path.insert(0, '/app/src')
try:
    from shared.config import Config
    print('✅ Módulos da aplicação carregados com sucesso')
except Exception as e:
    print(f'❌ Erro ao carregar módulos: {e}')
    sys.exit(1)
" || exit 1

# ===============================================================================
# MIGRAÇÃO DE BANCO DE DADOS
# ===============================================================================

if [ "$APP_ENV" != "testing" ]; then
    log "🗄️  Executando migrações de banco..."
    
    # Executar migrações se necessário
    python3 -c "
import sys
sys.path.insert(0, '/app/src')
try:
    from infrastructure.repositories.database import DatabaseConfig
    import asyncio
    
    async def migrate():
        db_config = DatabaseConfig()
        await db_config.create_tables()
        print('✅ Migrações executadas com sucesso')
    
    asyncio.run(migrate())
except Exception as e:
    print(f'⚠️  Aviso na migração: {e}')
    # Não falhar se as tabelas já existem
"
fi

# ===============================================================================
# HEALTH CHECK INICIAL
# ===============================================================================

log "🏥 Executando health check inicial..."

python3 -c "
import sys
sys.path.insert(0, '/app/src')
try:
    # Testar configurações básicas
    from shared.logging import get_logger
    logger = get_logger('healthcheck')
    logger.info('Health check executado com sucesso')
    print('✅ Health check passou')
except Exception as e:
    print(f'❌ Health check falhou: {e}')
    sys.exit(1)
" || exit 1

# ===============================================================================
# EXECUTAR COMANDO
# ===============================================================================

log "🎯 Executando comando: $*"

# Decidir qual comando executar baseado no primeiro argumento
case "$1" in
    "api")
        log "🌐 Iniciando API FastAPI..."
        exec python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
        ;;
    "cli")
        log "💻 Executando interface CLI..."
        shift
        exec python3 main.py "$@"
        ;;
    "scrape-cursos")
        log "📚 Executando scraping de cursos..."
        shift
        exec python3 main.py scrape-cursos "$@"
        ;;
    "scrape-componentes")
        log "📋 Executando scraping de componentes..."
        shift
        exec python3 main.py scrape-componentes "$@"
        ;;
    "scrape-estruturas")
        log "🏗️  Executando scraping de estruturas..."
        shift
        exec python3 main.py scrape-estruturas "$@"
        ;;
    "scheduler")
        log "⏰ Iniciando scheduler..."
        exec python3 -c "
import sys
sys.path.insert(0, '/app/src')
from interfaces.scheduler.SchedulerService import SchedulerService
import asyncio

async def main():
    scheduler = SchedulerService()
    await scheduler.start()

if __name__ == '__main__':
    asyncio.run(main())
"
        ;;
    "worker")
        log "👷 Iniciando worker para processamento em background..."
        exec python3 -c "
import sys
sys.path.insert(0, '/app/src')
from interfaces.worker.WorkerService import WorkerService
import asyncio

async def main():
    worker = WorkerService()
    await worker.start()

if __name__ == '__main__':
    asyncio.run(main())
"
        ;;
    "bash")
        log "🐚 Iniciando shell bash..."
        exec /bin/bash
        ;;
    "python")
        log "🐍 Iniciando Python..."
        shift
        exec python3 "$@"
        ;;
    *)
        log "🔧 Executando comando personalizado..."
        exec "$@"
        ;;
esac