# Contexto do Projeto Radar Web Scraping

## Visão Geral do Sistema
O Radar Web Scraping é um dos 4 componentes principais do sistema acadêmico Radar:

1. **radar-webscrapping** (Este projeto) - Python/FastAPI - Coleta de dados
2. **radar-webapi** - Spring Boot/Java 21/MySQL - Backend principal
3. **radar-frontend** - React - Interface do usuário
4. **radar-infrastructure** - Docker Compose - Orquestração

## Arquitetura do Projeto
O projeto segue **Clean Architecture** com as seguintes camadas:

```
src/
├── domain/           # Entidades de negócio e regras (núcleo)
├── application/      # Casos de uso e orquestração
├── infrastructure/   # Implementações técnicas (web, db, etc)
└── interfaces/       # Contratos e abstrações
```

## Princípios Fundamentais

### SOLID
- **S**ingle Responsibility: Uma classe, uma responsabilidade
- **O**pen/Closed: Aberto para extensão, fechado para modificação
- **L**iskov Substitution: Subtipos devem ser substituíveis
- **I**nterface Segregation: Interfaces específicas e coesas
- **D**ependency Inversion: Dependa de abstrações, não implementações

### Clean Architecture
- **Independência de Frameworks**: Regras não dependem de bibliotecas
- **Testabilidade**: Lógica pode ser testada sem UI/DB/Web
- **Independência de UI**: Interface pode mudar sem afetar regras
- **Independência de DB**: Regras não sabem sobre persistência
- **Independência Externa**: Regras não dependem de serviços externos

## Domínio de Negócio

### Site Alvo: SIGAA UFBA
- **Base URL**: https://sigaa.ufba.br/sigaa/
- **Cursos**: `/geral/curso/busca_geral.jsf`
- **Componentes**: `/geral/componente_curricular/busca_geral.jsf`
- **Estruturas Curriculares**: `/graduacao/curriculo/lista.jsf`

### Entidades Principais
1. **Curso**: Representa um curso de graduação
2. **ComponenteCurricular**: Disciplinas e atividades
3. **EstruturaCurricular**: Grade curricular do curso
4. **Programa**: Ementa/programa de um componente

### Regras de Negócio
1. Um curso pode ter múltiplas estruturas curriculares
2. Componentes podem ter pré-requisitos e co-requisitos
3. Estruturas curriculares têm situações (ATIVA, CONSOLIDADA, etc)
4. Componentes têm diferentes tipos (DISCIPLINA, ATIVIDADE)

## Padrões de Design Aplicados

### Repository Pattern
- Abstrai acesso aos dados
- Permite trocar implementação sem afetar regras

### Strategy Pattern
- Diferentes estratégias de scraping por site/página
- Facilita adição de novos sites universitários

### Factory Pattern
- Criação de scrapers específicos
- Desacopla criação de uso

### Observer Pattern
- Monitoramento de progresso
- Notificações de eventos

## Estrutura de Responsabilidades

### Domain Layer
- **Entities**: Curso, ComponenteCurricular, EstruturaCurricular
- **Value Objects**: CodigoCurso, CargaHoraria, Situacao
- **Domain Services**: Regras que não pertencem a uma entidade

### Application Layer
- **Use Cases**: ScrapearCursos, ScrapearComponentes, SincronizarDados
- **DTOs**: Objetos de transferência entre camadas
- **Interfaces**: Contratos para repositories e services

### Infrastructure Layer
- **Web Scrapers**: Implementações concretas de scraping
- **HTTP Clients**: Comunicação com radar-webapi
- **Browser Management**: Controle do Playwright
- **Persistence**: Cache local e armazenamento temporário

### Interfaces Layer
- **REST API**: Endpoints FastAPI
- **CLI**: Interface linha de comando
- **Config**: Configurações e settings

## Convenções de Nomenclatura

### Arquivos
- **PascalCase** para classes: `CursoRepository.py`
- **snake_case** para módulos: `curso_scraper.py`
- **UPPERCASE** para constantes: `CONFIG.py`

### Classes
- **Entidades**: `Curso`, `ComponenteCurricular`
- **Use Cases**: `ScrapearCursosUseCase`
- **Repositories**: `CursoRepository`
- **Services**: `SigaaScrapingService`

### Métodos
- **snake_case**: `obter_cursos()`, `validar_dados()`
- **Prefixos**: `get_`, `set_`, `create_`, `update_`, `delete_`

## Tratamento de Erros

### Hierarquia de Exceções
```python
RadarException
├── DomainException
│   ├── CursoInvalidoException
│   └── ComponenteNaoEncontradoException
├── ApplicationException
│   ├── ScrapingException
│   └── ValidationException
└── InfrastructureException
    ├── NetworkException
    └── BrowserException
```

## Configuração e Ambiente

### Variáveis de Ambiente
- **SIGAA_BASE_URL**: URL base do SIGAA
- **RADAR_API_URL**: URL do radar-webapi
- **BROWSER_HEADLESS**: Modo do navegador
- **LOG_LEVEL**: Nível de logging

### Perfis de Ambiente
- **development**: Debug habilitado, browser visível
- **testing**: Mocks habilitados, dados sintéticos
- **production**: Performance otimizada, logs estruturados

## Integração com radar-webapi

### Endpoints Esperados
- `POST /api/cursos` - Enviar cursos coletados
- `POST /api/componentes` - Enviar componentes curriculares
- `POST /api/estruturas` - Enviar estruturas curriculares
- `GET /api/health` - Health check

### Formato de Dados
- **JSON** com estrutura padronizada
- **ISO 8601** para datas
- **UTF-8** para codificação

## Qualidade de Código

### Métricas
- **Cobertura de testes**: > 80%
- **Complexidade ciclomática**: < 10
- **Linhas por método**: < 20
- **Métodos por classe**: < 15

### Ferramentas
- **pytest**: Testes unitários e integração
- **black**: Formatação automática
- **flake8**: Linting e style guide
- **mypy**: Type checking

## Observabilidade

### Logging
- **Structured logs** em JSON
- **Correlation IDs** para rastreamento
- **Diferentes níveis**: DEBUG, INFO, WARN, ERROR

### Métricas
- **Tempo de scraping** por página
- **Taxa de sucesso/erro**
- **Throughput** (páginas/minuto)
- **Uso de recursos** (CPU, memória)

Este contexto deve ser seguido em todas as implementações e refatorações do projeto.