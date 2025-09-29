# Multi-stage build para otimizar tamanho da imagem
FROM python:3.11-slim as builder

# Instalar dependências de build
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Criar diretório de trabalho
WORKDIR /app

# Copiar e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

#==============================================================================
# Imagem final de produção
FROM python:3.11-slim

# Metadados da imagem
LABEL maintainer="Radar UFBA Team"
LABEL description="Radar WebScrapping - Sistema de coleta de dados acadêmicos SIGAA UFBA"
LABEL version="1.0.0"

# Variáveis de ambiente
ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Instalar dependências do sistema para Selenium e Chrome
RUN apt-get update && apt-get install -y \
    # Chrome e dependências
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libxss1 \
    libxtst6 \
    xdg-utils \
    # Utilitários
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Instalar Google Chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Instalar ChromeDriver
RUN CHROME_VERSION=$(google-chrome --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+") \
    && CHROMEDRIVER_VERSION=$(curl -s "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*}") \
    && wget -O /tmp/chromedriver.zip "https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VERSION}/chromedriver_linux64.zip" \
    && unzip /tmp/chromedriver.zip -d /tmp/ \
    && mv /tmp/chromedriver /usr/local/bin/chromedriver \
    && chmod +x /usr/local/bin/chromedriver \
    && rm /tmp/chromedriver.zip

# Criar usuário não-root para segurança
RUN groupadd -r radar && useradd -r -g radar -d /app radar

# Criar diretórios necessários
RUN mkdir -p /app/data /app/logs /app/src \
    && chown -R radar:radar /app

# Copiar dependências Python instaladas
COPY --from=builder /root/.local /home/radar/.local
ENV PATH=/home/radar/.local/bin:$PATH

# Definir diretório de trabalho
WORKDIR /app

# Copiar código fonte
COPY --chown=radar:radar src/ ./src/
COPY --chown=radar:radar main.py ./
COPY --chown=radar:radar requirements.txt ./

# Copiar script de entrada
COPY --chown=radar:radar scripts/docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Mudar para usuário não-root
USER radar

# Configurar variáveis de ambiente específicas do Chrome
ENV CHROME_BIN=/usr/bin/google-chrome \
    CHROME_PATH=/usr/bin/google-chrome \
    CHROMEDRIVER_PATH=/usr/local/bin/chromedriver \
    DISPLAY=:99

# Expor porta da aplicação
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import sys; sys.path.insert(0, '/app/src'); exec('try:\\n    from shared.config import Config\\n    print(\"Health check: OK\")\\n    exit(0)\\nexcept Exception as e:\\n    print(f\"Health check failed: {e}\")\\n    exit(1)')"

# Volumes para persistência de dados e logs
VOLUME ["/app/data", "/app/logs"]

# Comando padrão
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["api"]