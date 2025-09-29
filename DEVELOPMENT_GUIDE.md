# Radar WebScrapping - Guia de Desenvolvimento

## Índice
1. [Visão Geral](#visão-geral)
2. [Arquitetura do Sistema](#arquitetura-do-sistema)
3. [Estrutura do Projeto](#estrutura-do-projeto)
4. [Configuração do Ambiente](#configuração-do-ambiente)
5. [Guia de Desenvolvimento](#guia-de-desenvolvimento)
6. [Casos de Uso](#casos-de-uso)
7. [Testes](#testes)
8. [Deploy e Produção](#deploy-e-produção)
9. [Troubleshooting](#troubleshooting)

## Visão Geral

O **Radar WebScrapping** é um sistema de coleta automatizada de dados acadêmicos do SIGAA UFBA, desenvolvido seguindo princípios de **Clean Architecture** e **SOLID**. O sistema coleta informações sobre cursos, componentes curriculares e estruturas curriculares, fornecendo dados estruturados para o sistema Radar de recomendação acadêmica.

### Objetivos Principais
- ✅ Coleta automatizada de dados do SIGAA UFBA
- ✅ Arquitetura limpa e manutenível
- ✅ Separação clara de responsabilidades
- ✅ Integração com radar-webapi (Spring Boot)
- ✅ Interface CLI robusta
- ✅ Logging estruturado e observabilidade

### Tecnologias Utilizadas
- **Python 3.11+**
- **Selenium** - Web scraping
- **SQLAlchemy** - ORM assíncrono
- **Pydantic** - Validação de dados
- **Click** - Interface CLI
- **Loguru** - Logging estruturado
- **httpx** - Cliente HTTP assíncrono

## Arquitetura do Sistema

O sistema segue rigorosamente os princípios de **Clean Architecture**, organizando o código em camadas bem definidas:

```
┌─────────────────────────────────────────────────────┐
│                 INTERFACES                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │     CLI     │  │   FastAPI   │  │    Web UI   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│               APPLICATION                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Use Cases   │  │    DTOs     │  │ Interfaces  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│                  DOMAIN                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Entities   │  │Value Objects│  │ Exceptions  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────────┐
│              INFRASTRUCTURE                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Scrapers   │  │Repositories │  │API Clients  │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

### Princípios Arquiteturais

#### 1. **Separação de Responsabilidades**
- **Domain**: Regras de negócio puras
- **Application**: Orquestração de casos de uso
- **Infrastructure**: Implementações técnicas
- **Interfaces**: Pontos de entrada do sistema

#### 2. **Dependency Inversion**
- Camadas internas não dependem de externas
- Abstrações (interfaces) definem contratos
- Implementações concretas são injetadas

#### 3. **Single Responsibility**
- Cada classe tem uma única razão para mudar
- Métodos fazem apenas uma coisa
- Módulos são coesos e focados

## Estrutura do Projeto

```
radar-webscrapping/
├── src/
│   ├── domain/                    # 🔵 Camada de Domínio
│   │   ├── entities/             # Entidades de negócio
│   │   │   ├── __init__.py
│   │   │   ├── Curso.py
│   │   │   ├── ComponenteCurricular.py
│   │   │   └── EstruturaCurricular.py
│   │   ├── value_objects/        # Objetos de valor
│   │   │   ├── __init__.py
│   │   │   ├── CodigoCurso.py
│   │   │   ├── NomeCurso.py
│   │   │   ├── CargaHoraria.py
│   │   │   └── VersaoEstrutura.py
│   │   ├── exceptions/           # Exceções de domínio
│   │   │   ├── __init__.py
│   │   │   ├── DomainException.py
│   │   │   ├── ValidationException.py
│   │   │   └── BusinessRuleException.py
│   │   └── __init__.py
│   │
│   ├── application/              # 🟡 Camada de Aplicação
│   │   ├── interfaces/           # Contratos/Abstrações
│   │   │   ├── __init__.py
│   │   │   ├── ICursoRepository.py
│   │   │   ├── IComponenteCurricularRepository.py
│   │   │   ├── IEstruturaCurricularRepository.py
│   │   │   ├── IScrapingService.py
│   │   │   └── IRadarApiClient.py
│   │   ├── use_cases/            # Casos de uso
│   │   │   ├── __init__.py
│   │   │   ├── ScrapearCursosUseCase.py
│   │   │   ├── ScrapearComponentesUseCase.py
│   │   │   ├── ScrapearEstruturasCurricularesUseCase.py
│   │   │   └── OrquestrarScrapingCompletoUseCase.py
│   │   ├── dtos/                 # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   └── DataTransferObjects.py
│   │   └── __init__.py
│   │
│   ├── infrastructure/           # 🔴 Camada de Infraestrutura
│   │   ├── scrapers/            # Implementações de scraping
│   │   │   ├── __init__.py
│   │   │   ├── SigaaUfbaCursoScraper.py
│   │   │   ├── SigaaUfbaComponenteScraper.py
│   │   │   └── SigaaUfbaEstruturaScraper.py
│   │   ├── repositories/        # Implementações de repositórios
│   │   │   ├── models/          # Models SQLAlchemy
│   │   │   │   ├── __init__.py
│   │   │   │   ├── CursoModel.py
│   │   │   │   ├── ComponenteCurricularModel.py
│   │   │   │   └── EstruturaCurricularModel.py
│   │   │   ├── __init__.py
│   │   │   ├── database.py
│   │   │   ├── SqlAlchemyCursoRepository.py
│   │   │   ├── SqlAlchemyComponenteRepository.py
│   │   │   └── SqlAlchemyEstruturaRepository.py
│   │   ├── api_clients/         # Clientes de APIs externas
│   │   │   ├── __init__.py
│   │   │   └── RadarApiClient.py
│   │   └── __init__.py
│   │
│   ├── interfaces/              # 🟢 Camada de Interface
│   │   ├── cli/                 # Interface linha de comando
│   │   │   ├── __init__.py
│   │   │   ├── CursoController.py
│   │   │   ├── ComponenteController.py
│   │   │   └── EstruturaController.py
│   │   ├── api/                 # Interface REST (futuro)
│   │   │   └── __init__.py
│   │   └── __init__.py
│   │
│   ├── shared/                  # 🟠 Utilitários Compartilhados
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   ├── config.py
│   │   └── utils.py
│   │
│   └── __init__.py
│
├── tests/                       # 🧪 Testes
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                        # 📚 Documentação
├── data/                        # 💾 Dados locais
├── logs/                        # 📋 Arquivos de log
├── scripts/                     # 🔧 Scripts utilitários
├── main.py                      # 🚀 Ponto de entrada
├── requirements.txt             # 📦 Dependências
├── .env.example                 # ⚙️ Variáveis de ambiente
├── CONTEXT.md                   # 📋 Contexto arquitetural
└── README.md                    # 📖 Documentação principal
```

## Configuração do Ambiente

### 1. **Pré-requisitos**
```bash
# Python 3.11 ou superior
python --version

# Git
git --version

# Chrome/Chromium (para Selenium)
google-chrome --version
```

### 2. **Instalação**
```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/radar-webscrapping.git
cd radar-webscrapping

# 2. Criar ambiente virtual
python -m venv venv

# 3. Ativar ambiente virtual
# No Windows:
venv\Scripts\activate
# No Linux/Mac:
source venv/bin/activate

# 4. Instalar dependências
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env conforme necessário
```

### 3. **Configuração do Banco de Dados**
```bash
# Criar estrutura de diretórios
mkdir -p data logs

# O banco SQLite será criado automaticamente na primeira execução
```

### 4. **Configuração do WebDriver**
```bash
# Para Selenium com Chrome
# O webdriver-manager baixará automaticamente o ChromeDriver
# Nenhuma configuração manual necessária
```

## Guia de Desenvolvimento

### Executando o Sistema

#### **Interface CLI**
```bash
# Executar via main.py
python main.py --help

# Ver status do sistema
python main.py status

# Executar scraping de cursos
python main.py scrape-cursos --unidade "Instituto de Matemática"

# Buscar curso específico
python main.py buscar-curso "MAT001"

# Listar cursos coletados
python main.py listar-cursos --unidade "IME"
```

#### **Desenvolvimento de Novos Features**

##### 1. **Adicionando Nova Entidade de Domínio**

```python
# src/domain/entities/NovaEntidade.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class NovaEntidade:
    """Nova entidade seguindo princípios DDD."""
    
    id: str
    nome: str
    
    def __post_init__(self):
        """Validações de domínio."""
        if not self.nome.strip():
            raise ValidationException("nome", self.nome, "Nome não pode ser vazio")
    
    def regra_de_negocio_especifica(self) -> bool:
        """Implementa regra de negócio específica."""
        return len(self.nome) > 3
```

##### 2. **Criando Novo Repositório**

```python
# src/application/interfaces/INovaEntidadeRepository.py
from abc import ABC, abstractmethod
from typing import List, Optional

class INovaEntidadeRepository(ABC):
    """Interface para repositório de nova entidade."""
    
    @abstractmethod
    async def salvar(self, entidade: NovaEntidade) -> None:
        """Salva uma entidade."""
        pass
    
    @abstractmethod
    async def buscar_por_id(self, id: str) -> Optional[NovaEntidade]:
        """Busca entidade por ID."""
        pass
```

```python
# src/infrastructure/repositories/SqlAlchemyNovaEntidadeRepository.py
from ...application.interfaces.INovaEntidadeRepository import INovaEntidadeRepository

class SqlAlchemyNovaEntidadeRepository(INovaEntidadeRepository):
    """Implementação concreta do repositório."""
    
    async def salvar(self, entidade: NovaEntidade) -> None:
        # Implementação usando SQLAlchemy
        pass
```

##### 3. **Implementando Novo Caso de Uso**

```python
# src/application/use_cases/NovoUseCase.py
class NovoUseCase:
    """Novo caso de uso seguindo Clean Architecture."""
    
    def __init__(self, repository: INovaEntidadeRepository):
        self._repository = repository
    
    async def executar(self, dados_entrada: Dict) -> ResultadoDto:
        """Executa lógica do caso de uso."""
        # 1. Validar entrada
        # 2. Aplicar regras de negócio
        # 3. Persistir dados
        # 4. Retornar resultado
        pass
```

### Padrões de Código

#### **1. Naming Conventions**
```python
# Classes: PascalCase
class ScrapearCursosUseCase:
    pass

# Métodos e variáveis: snake_case
def executar_scraping_completo(self):
    codigo_curso = "MAT001"

# Constantes: UPPER_SNAKE_CASE
BASE_URL = "https://sigaa.ufba.br"

# Interfaces: prefixo I
class ICursoRepository:
    pass
```

#### **2. Estrutura de Métodos**
```python
async def metodo_exemplo(self, parametro: str) -> ResultadoDto:
    """
    Docstring explicando o método.
    
    Args:
        parametro: Descrição do parâmetro
        
    Returns:
        Descrição do retorno
        
    Raises:
        ExcecaoEspecifica: Quando ocorre erro específico
    """
    try:
        # 1. Logging inicial
        logger.info(f"Iniciando operação com {parametro}")
        
        # 2. Validação de entrada
        if not parametro.strip():
            raise ValidationException("parametro", parametro, "Parâmetro inválido")
        
        # 3. Lógica principal
        resultado = await self._processar_parametro(parametro)
        
        # 4. Logging de sucesso
        logger.info(f"Operação concluída: {resultado}")
        
        return resultado
        
    except ValidationException:
        raise  # Re-propagar exceções conhecidas
    
    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        raise DomainException(f"Erro no processamento: {e}")
```

#### **3. Tratamento de Exceções**
```python
# Hierarquia de exceções bem definida
try:
    resultado = await operacao_complexa()
except ValidationException as e:
    # Erro de validação - retornar ao usuário
    logger.warning(f"Validação falhou: {e}")
    raise
except BusinessRuleException as e:
    # Violação de regra de negócio
    logger.error(f"Regra de negócio violada: {e}")
    raise
except RepositoryException as e:
    # Erro de persistência
    logger.error(f"Erro no repositório: {e}")
    raise
except Exception as e:
    # Erro inesperado
    logger.critical(f"Erro crítico: {e}")
    raise DomainException(f"Erro interno: {e}")
```

#### **4. Logging Estruturado**
```python
from ...shared.logging import get_logger, create_scraping_logger

# Logger básico
logger = get_logger(__name__)

# Logger estruturado para scraping
scraping_logger = create_scraping_logger("sigaa-cursos", job_id="curso_abc123")

# Uso do logging
logger.info("Operação iniciada")
scraping_logger.info("Curso coletado", 
                    codigo="MAT001", 
                    nome="Matemática",
                    duracao_ms=1500)
```

## Casos de Uso

### 1. **Scraping de Cursos**

```python
# Configuração
configuracao = ConfiguracaoScrapingDto(
    incluir_cursos=True,
    incluir_componentes=False,
    incluir_estruturas=False,
    filtro_unidade="Instituto de Matemática",
    filtro_modalidade="Presencial"
)

# Execução
use_case = ScrapearCursosUseCase(repository, scraper, api_client)
resultado = await use_case.executar(configuracao, sincronizar_backend=True)

# Resultado
print(f"Job {resultado.id}: {resultado.status}")
print(f"Coletados: {resultado.itens_coletados} cursos")
```

### 2. **Scraping Completo (Orquestrado)**

```python
# Scraping sequencial completo
resultado = await orquestrador.executar_scraping_completo(
    configuracao=configuracao,
    tipo_execucao=TipoScrapingCompleto.SEQUENCIAL,
    sincronizar_backend=True
)

# Verificar resultado de cada tipo
if resultado.job_cursos:
    print(f"Cursos: {resultado.job_cursos.itens_coletados}")
if resultado.job_componentes:
    print(f"Componentes: {resultado.job_componentes.itens_coletados}")
if resultado.job_estruturas:
    print(f"Estruturas: {resultado.job_estruturas.itens_coletados}")
```

### 3. **Pipeline para Curso Específico**

```python
# Pipeline completo para um curso
resultado = await orquestrador.executar_pipeline_curso_especifico(
    codigo_curso="MAT001",
    configuracao=configuracao,
    sincronizar_backend=True
)

print(f"Pipeline do curso MAT001: {resultado.sucesso_total}")
```

## Testes

### Estrutura de Testes

```
tests/
├── unit/                    # Testes unitários
│   ├── domain/             # Testes de entidades e VOs
│   ├── application/        # Testes de casos de uso
│   └── infrastructure/     # Testes de implementações
├── integration/            # Testes de integração
│   ├── repositories/       # Testes com banco
│   ├── scrapers/          # Testes com sites reais
│   └── api_clients/       # Testes com APIs
└── e2e/                   # Testes end-to-end
    └── cli/               # Testes da interface CLI
```

### Executando Testes

```bash
# Todos os testes
pytest

# Testes unitários apenas
pytest tests/unit/

# Testes com cobertura
pytest --cov=src --cov-report=html

# Testes específicos
pytest tests/unit/domain/test_curso.py

# Testes com logs detalhados
pytest -v -s tests/
```

### Exemplo de Teste Unitário

```python
# tests/unit/domain/test_curso.py
import pytest
from src.domain.entities.Curso import Curso
from src.domain.value_objects.CodigoCurso import CodigoCurso
from src.domain.exceptions import ValidationException

class TestCurso:
    """Testes para entidade Curso."""
    
    def test_criar_curso_valido(self):
        """Deve criar curso com dados válidos."""
        # Arrange
        codigo = CodigoCurso("MAT001")
        nome = "Matemática"
        
        # Act
        curso = Curso(
            codigo=codigo,
            nome=nome,
            unidade_vinculacao="IME",
            municipio_funcionamento="Salvador",
            modalidade="Presencial",
            turno="Integral",
            grau_academico="Bacharelado"
        )
        
        # Assert
        assert curso.codigo == codigo
        assert curso.nome == nome
        assert curso.eh_curso_valido()
    
    def test_criar_curso_codigo_invalido(self):
        """Deve falhar com código inválido."""
        # Arrange & Act & Assert
        with pytest.raises(ValidationException):
            CodigoCurso("")
```

### Exemplo de Teste de Integração

```python
# tests/integration/repositories/test_curso_repository.py
import pytest
from src.infrastructure.repositories.SqlAlchemyCursoRepository import SqlAlchemyCursoRepository
from src.infrastructure.repositories.database import DatabaseConfig

@pytest.fixture
async def repository():
    """Fixture para repositório com banco de teste."""
    db_session = DatabaseConfig.create_test_session()
    repository = SqlAlchemyCursoRepository(db_session)
    yield repository
    await db_session.close()

@pytest.mark.asyncio
class TestCursoRepository:
    """Testes de integração para repositório de cursos."""
    
    async def test_salvar_e_buscar_curso(self, repository):
        """Deve salvar e recuperar curso do banco."""
        # Arrange
        curso = criar_curso_teste()
        
        # Act
        await repository.salvar(curso)
        curso_recuperado = await repository.buscar_por_codigo(str(curso.codigo))
        
        # Assert
        assert curso_recuperado is not None
        assert curso_recuperado.codigo == curso.codigo
        assert curso_recuperado.nome == curso.nome
```

## Deploy e Produção

### 1. **Configuração de Produção**

```bash
# .env.production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/radar_db
RADAR_API_URL=https://api.radar.ufba.br
LOG_LEVEL=INFO
LOG_FORMAT=json
SELENIUM_HEADLESS=true
```

### 2. **Docker (Opcional)**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    chromium-driver \
    chromium \
    && rm -rf /var/lib/apt/lists/*

# Instalar dependências Python
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar código
COPY . .

# Configurar variáveis de ambiente
ENV PYTHONPATH=/app/src
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROME_DRIVER=/usr/bin/chromedriver

# Comando padrão
CMD ["python", "main.py", "--help"]
```

### 3. **Monitoramento**

```python
# Configuração de logs para produção
configure_logging(
    level="INFO",
    format_type="json"  # Para integração com ELK stack
)

# Métricas estruturadas
logger.info("scraping_concluido", 
           job_id=job.id,
           tipo="cursos",
           itens_coletados=resultado.itens_coletados,
           duracao_segundos=resultado.duracao_total(),
           sucesso=resultado.sucesso_total)
```

## Troubleshooting

### Problemas Comuns

#### 1. **Erro de WebDriver**
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

**Solução:**
```bash
# Instalar webdriver-manager
pip install webdriver-manager

# Ou baixar manualmente o ChromeDriver
# e adicionar ao PATH do sistema
```

#### 2. **Erro de Conexão com Banco**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) database is locked
```

**Solução:**
```bash
# Verificar se há processos usando o banco
lsof data/radar_webscrapping.db

# Ou usar banco em memória para testes
DATABASE_URL=sqlite+aiosqlite:///:memory:
```

#### 3. **Timeout no SIGAA**
```
selenium.common.exceptions.TimeoutException: Message: 
```

**Solução:**
```python
# Aumentar timeout no scraper
scraper = SigaaUfbaCursoScraper(
    timeout=60,  # 60 segundos
    delay_between_requests=2.0  # 2 segundos entre requisições
)
```

#### 4. **Erro de Importação**
```
ModuleNotFoundError: No module named 'src'
```

**Solução:**
```bash
# Executar do diretório raiz
cd radar-webscrapping
python main.py

# Ou configurar PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

### Logs de Debug

```bash
# Executar com logs detalhados
python main.py --log-level DEBUG scrape-cursos

# Ver logs em arquivo
tail -f logs/radar_webscrapping.log

# Filtrar logs por contexto
grep "scraping" logs/radar_webscrapping.log | grep "ERROR"
```

### Validação do Sistema

```bash
# Verificar status geral
python main.py status

# Testar conectividade
python main.py scrape-cursos --no-sync --unidade "Teste"

# Validar configuração
python -c "
from src.infrastructure.repositories.database import get_database_session
session = get_database_session()
print('Banco OK!')
"
```

---

## Próximos Passos

### Funcionalidades Planejadas
1. **Interface Web** - Dashboard para monitoramento
2. **Agendamento** - Execução automática via cron/scheduler
3. **Notificações** - Alertas por email/Slack
4. **Métricas** - Dashboard de observabilidade
5. **API REST** - Interface programática
6. **Testes E2E** - Cobertura completa de cenários

### Melhorias Técnicas
1. **Cache** - Redis para cache de dados temporários
2. **Queue** - RabbitMQ/Celery para processamento assíncrono
3. **Monitoring** - Prometheus/Grafana
4. **CI/CD** - GitHub Actions para deploy automatizado

---

**Desenvolvido seguindo Clean Architecture e princípios SOLID**  
**Sistema Radar - UFBA**  
**Versão 1.0 - 2024**