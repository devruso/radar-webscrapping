# 🚀 Guia Prático de Desenvolvimento - Radar WebScrapping

**Para quem nunca fez webscrapping e quer entender o ambiente DevOps completo**

## 📋 Índice

1. [Entendendo o Que Foi Criado](#entendendo-o-que-foi-criado)
2. [Ambiente de Desenvolvimento Local](#ambiente-de-desenvolvimento-local)  
3. [Workflow Diário de Desenvolvimento](#workflow-diário-de-desenvolvimento)
4. [Testando e Debuggando](#testando-e-debuggando)
5. [Sistema de CI/CD Explicado](#sistema-de-cicd-explicado)
6. [Como Fazer Mudanças Seguras](#como-fazer-mudanças-seguras)
7. [Troubleshooting Comum](#troubleshooting-comum)

---

## 🎯 Entendendo o Que Foi Criado

### O Que Você Tem Agora:

#### 1. **Aplicação Python** 📦
```
src/
├── scrapers/           # Seus scrapers (onde você vai trabalhar mais)
├── services/          # Serviços como API client
├── models/            # Estruturas de dados
└── utils/             # Utilitários
```

#### 2. **Docker Completo** 🐳
- **Dockerfile**: Receita para criar container da aplicação
- **docker-compose.yml**: Ambiente completo local (PostgreSQL, Redis, etc)
- **scripts/docker-entrypoint.sh**: Como o container inicia

#### 3. **GitHub Actions** 🤖
- **5 workflows** que automatizam tudo (testes, builds, deploy)
- Executam automaticamente quando você faz push
- Garantem que código funciona antes de ir para produção

#### 4. **Documentação** 📚
- **README.md**: Visão geral
- **DOCKER.md**: Como usar Docker
- **CONTEXT.md**: Arquitetura do projeto
- **.github/README.md**: Como funcionam os workflows

### Por Que Isso Tudo?

**Sem DevOps** (método tradicional):
```bash
# Você teria que fazer na mão sempre:
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Instalar Chrome, ChromeDriver...
# Configurar banco...
# Rodar testes na mão...
# Build manual...
```

**Com DevOps** (o que você tem agora):
```bash
# Simples assim:
docker-compose up
# TUDO funciona automaticamente!
```

---

## 💻 Ambiente de Desenvolvimento Local

### Opção 1: Desenvolvimento com Docker (Recomendado para Iniciantes)

#### Setup Inicial (só uma vez):
```bash
# 1. Navegue até seu projeto
cd c:\Users\jamil\Documents\programming\radar-webscrapping

# 2. Suba o ambiente completo
docker-compose up -d

# 3. Verifique se tudo subiu
docker-compose ps
```

**O que isso faz:**
- Cria container com Python + Chrome + todas dependências
- Sobe PostgreSQL (banco de dados)
- Sobe Redis (cache)
- Sobe PgAdmin (visualizar banco)
- Configura rede entre todos os serviços

#### Desenvolvimento Diário:
```bash
# Trabalhar no código (edite arquivos normalmente no VS Code)
# Os arquivos são sincronizados automaticamente

# Executar comandos dentro do container
docker-compose exec webscrapping bash

# Ou executar comandos diretamente
docker-compose exec webscrapping python main.py --help
```

### Opção 2: Desenvolvimento Local Nativo

#### Setup (mais trabalhoso, mas você controla tudo):
```bash
# 1. Criar ambiente virtual
python -m venv venv
venv\Scripts\activate

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Instalar Chrome/ChromeDriver
# (Selenium Manager faz automaticamente)

# 4. Configurar .env
cp .env.example .env
# Editar .env com suas configurações
```

---

## 🔄 Workflow Diário de Desenvolvimento

### Cenário: "Quero alterar como o scraper coleta cursos"

#### 1. **Entender o Código Atual**
```bash
# Onde está o código de scraping de cursos?
src/scrapers/curso_scraper.py  # (exemplo)

# Como funciona atualmente?
# Leia CONTEXT.md e DEVELOPMENT_GUIDE.md
```

#### 2. **Fazer Alterações**
```python
# Exemplo: Alterar URL do SIGAA
# Em src/scrapers/curso_scraper.py

class CursoScraper:
    def __init__(self):
        # ANTES:
        self.base_url = "https://sigaa.ufba.br/sigaa/geral/curso/busca_geral.jsf"
        
        # DEPOIS (sua mudança):
        self.base_url = "https://sigaa.ufba.br/sigaa/nova-url-curso.jsf"
```

#### 3. **Testar Localmente**
```bash
# Com Docker
docker-compose exec webscrapping python main.py scrape-cursos --unidade "IME"

# Ou nativo
python main.py scrape-cursos --unidade "IME"
```

#### 4. **Verificar se Funciona**
```bash
# Executar testes
docker-compose exec webscrapping pytest tests/

# Ver logs
docker-compose logs webscrapping
```

#### 5. **Commit e Push**
```bash
git add .
git commit -m "feat: atualizar URL de coleta de cursos"
git push origin main
```

#### 6. **GitHub Actions Automaticamente:**
- ✅ Roda testes
- ✅ Verifica qualidade do código  
- ✅ Faz build Docker
- ✅ Testa segurança
- ❌ Se algo der errado, você recebe notificação

---

## 🧪 Testando e Debuggando

### Tipos de Teste Que Você Pode Fazer:

#### 1. **Teste Rápido - Funciona Básico?**
```bash
# Docker
docker-compose exec webscrapping python -c "from src.scrapers import CursoScraper; print('OK')"

# Nativo  
python -c "from src.scrapers import CursoScraper; print('OK')"
```

#### 2. **Teste Funcional - Scraper Funciona?**
```bash
# Testar scraping de uma unidade específica
docker-compose exec webscrapping python main.py scrape-cursos --unidade "IME" --debug
```

#### 3. **Teste Completo - Todos os Testes**
```bash
# Executar suite completa de testes
docker-compose exec webscrapping pytest tests/ -v

# Com cobertura
docker-compose exec webscrapping pytest tests/ --cov=src --cov-report=html
```

### Debug de Problemas:

#### 1. **Container não sobe**
```bash
# Ver logs detalhados
docker-compose logs webscrapping

# Reconstruir container
docker-compose build --no-cache webscrapping
docker-compose up webscrapping
```

#### 2. **Scraper não funciona**
```bash
# Entrar no container e debuggar
docker-compose exec webscrapping bash

# Executar Python interativo
python

# Testar imports
>>> from src.scrapers import CursoScraper
>>> scraper = CursoScraper()
>>> # Teste passo a passo
```

#### 3. **Problema de dependências**
```bash
# Reinstalar dependências
docker-compose exec webscrapping pip install -r requirements.txt

# Ou rebuild completo
docker-compose build --no-cache
```

---

## 🤖 Sistema de CI/CD Explicado

### O Que Acontece Quando Você Faz `git push`:

#### 1. **GitHub Actions Detecta Mudança**
```
🚀 Push detectado na branch main
📋 Executa workflow: ci-cd.yml
```

#### 2. **Pipeline de Testes (5-8 minutos)**
```
Step 1: Lint (2min)     → Verifica qualidade do código
Step 2: Tests (3min)    → Executa todos os testes
Step 3: Build (2min)    → Tenta fazer build Docker  
Step 4: Security (1min) → Verifica vulnerabilidades
```

#### 3. **Resultado:**
- ✅ **Sucesso**: Código aprovado, pode usar
- ❌ **Falha**: Algo deu errado, você precisa corrigir

### Como Ver Resultados:

#### 1. **GitHub Web Interface**
```
GitHub → Seu Repo → Actions tab
→ Ver workflow em execução
→ Clicar para ver detalhes
```

#### 2. **GitHub CLI (opcional)**
```bash
# Instalar gh CLI
# https://cli.github.com/

# Ver execuções
gh run list

# Ver detalhes
gh run view [run-id]
```

#### 3. **Email/Notificações**
GitHub envia email se pipeline falhar.

### Workflows Explicados:

#### **ci-cd.yml** - Pipeline Principal  
- **Quando**: Toda vez que você faz push/PR
- **O que faz**: Testa tudo, build, security scan
- **Duração**: ~15 minutos
- **Importante**: Se falhar, NÃO faça deploy

#### **ci-simple.yml** - Teste Rápido
- **Quando**: Push/PR (paralelo ao principal)  
- **O que faz**: Testes básicos mais rápidos
- **Duração**: ~8 minutos
- **Importante**: Feedback rápido

#### **dependencies.yml** - Atualização Automática
- **Quando**: Segunda-feira (automático)
- **O que faz**: Atualiza dependências Python
- **Duração**: ~5 minutos
- **Importante**: Mantém projeto seguro

#### **release.yml** - Deploy Produção
- **Quando**: Quando você cria tag (ex: v1.0.0)
- **O que faz**: Build final, publica release
- **Duração**: ~25 minutos
- **Importante**: Só para versões finais

#### **cleanup.yml** - Limpeza
- **Quando**: Domingo (automático)
- **O que faz**: Remove arquivos antigos
- **Duração**: ~3 minutos
- **Importante**: Mantém repo organizado

---

## ✅ Como Fazer Mudanças Seguras

### Processo Recomendado para Iniciantes:

#### 1. **Sempre Trabalhe em Branch**
```bash
# Criar branch para nova feature
git checkout -b feature/melhorar-scraper-cursos

# Fazer suas alterações
# ...

# Commit
git add .
git commit -m "feat: melhorar scraper de cursos"

# Push da branch
git push origin feature/melhorar-scraper-cursos
```

#### 2. **Criar Pull Request**
```bash
# No GitHub:
# → Go to repo → Compare & pull request
# → Escreva descrição do que mudou
# → Create pull request
```

#### 3. **GitHub Actions Testa Automaticamente**
```
🤖 CI/CD roda automaticamente na sua branch
✅ Se passar: pode fazer merge
❌ Se falhar: você precisa corrigir antes
```

#### 4. **Merge Só Se Tudo OK**
```bash
# No GitHub: 
# → Merge pull request (só se CI passou)

# Localmente:
git checkout main
git pull origin main
git branch -d feature/melhorar-scraper-cursos
```

### Para Mudanças Pequenas (Método Simples):

```bash
# Trabalhe direto na main (só para bugs pequenos)
git add .
git commit -m "fix: corrigir typo na URL"
git push origin main

# GitHub Actions testa automaticamente
# Se falhar, corrija imediatamente
```

---

## 🚨 Troubleshooting Comum

### Problema 1: "Docker não sobe"

#### Sintomas:
```bash
docker-compose up
# Erro: container exits immediately
```

#### Soluções:
```bash
# 1. Ver logs detalhados
docker-compose logs webscrapping

# 2. Verificar porta em uso
netstat -an | findstr 8000  # Windows
# Se porta ocupada, mudar no docker-compose.yml

# 3. Limpar tudo e recomeçar
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

### Problema 2: "Selenium não funciona"

#### Sintomas:
```
selenium.common.exceptions.WebDriverException: Message: 'chromedriver' executable needs to be in PATH
```

#### Soluções:
```bash
# 1. No Docker (automático)
docker-compose exec webscrapping google-chrome --version
docker-compose exec webscrapping chromedriver --version

# 2. Local (manual)
# Instalar Chrome
# webdriver-manager faz o resto automaticamente
```

### Problema 3: "GitHub Actions Falha"

#### Sintomas:
```
❌ CI/CD failed
📧 Email de falha
```

#### Soluções:
```bash
# 1. Ver detalhes no GitHub
# → Actions tab → Click na execução falhada

# 2. Problemas comuns:
# - Teste falha: Corrigir teste ou código
# - Build falha: Dependência faltando
# - Lint falha: Código não segue padrão

# 3. Corrigir e push novamente
git add .
git commit -m "fix: corrigir problema de lint"
git push origin main
```

### Problema 4: "Scraper não coleta dados"

#### Sintomas:
```bash
python main.py scrape-cursos
# Retorna lista vazia ou erro
```

#### Debug Passo a Passo:
```bash
# 1. Entrar no container
docker-compose exec webscrapping bash

# 2. Testar Python interativo
python

# 3. Debug manual
>>> from selenium import webdriver
>>> from selenium.webdriver.chrome.options import Options
>>> 
>>> options = Options()
>>> options.add_argument('--headless=false')  # Ver navegador
>>> driver = webdriver.Chrome(options=options)
>>> 
>>> driver.get('https://sigaa.ufba.br')
>>> print(driver.title)
>>> # Verificar se site carrega

# 4. Testar seu scraper
>>> from src.scrapers import CursoScraper
>>> scraper = CursoScraper()
>>> # Testar métodos individuais
```

### Problema 5: "Dependências conflitantes"

#### Sintomas:
```bash
pip install -r requirements.txt
# Conflitos de versão
```

#### Soluções:
```bash
# 1. Limpar ambiente
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows

# 2. Recriar
python -m venv venv
venv\Scripts\activate  # Windows

# 3. Instalar novamente
pip install --upgrade pip
pip install -r requirements.txt

# 4. Se continuar problema, atualizar requirements.txt
pip freeze > requirements-new.txt
# Comparar e corrigir manualmente
```

---

## 📝 Comandos de Referência Rápida

### Docker:
```bash
# Subir ambiente
docker-compose up -d

# Ver logs
docker-compose logs -f webscrapping

# Executar comando
docker-compose exec webscrapping [comando]

# Parar tudo
docker-compose down

# Rebuild
docker-compose build --no-cache
```

### Git:
```bash
# Status
git status

# Adicionar arquivos
git add .

# Commit
git commit -m "mensagem"

# Push
git push origin main

# Criar branch
git checkout -b nome-da-branch

# Trocar branch
git checkout main
```

### Aplicação:
```bash
# Help
python main.py --help

# Scraping específico
python main.py scrape-cursos --unidade "IME"

# Status
python main.py status

# Modo debug
python main.py scrape-cursos --debug
```

### Testes:
```bash
# Todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov=src

# Teste específico
pytest tests/test_curso_scraper.py

# Debug verboso
pytest tests/ -v -s
```

---

## 🎯 Próximos Passos Recomendados

### Semana 1 - Familiarização:
1. ✅ Ler esta documentação completa
2. ✅ Subir ambiente com `docker-compose up`
3. ✅ Executar primeiro scraping: `python main.py scrape-cursos --unidade "IME"`
4. ✅ Fazer primeira alteração simples (ex: mudar uma URL)
5. ✅ Fazer commit e ver GitHub Actions funcionar

### Semana 2 - Desenvolvimento:
1. ✅ Entender arquitetura em `CONTEXT.md`
2. ✅ Modificar lógica de scraping
3. ✅ Adicionar novos testes
4. ✅ Trabalhar com branches/PRs

### Semana 3 - Avançado:
1. ✅ Integrar com radar-webapi
2. ✅ Configurar ambiente de produção
3. ✅ Fazer primeira release (tag v1.0.0)

### Semana 4+ - Maestria:
1. ✅ Customizar workflows
2. ✅ Adicionar novas funcionalidades
3. ✅ Otimizar performance
4. ✅ Monitoramento avançado

---

## 🆘 Onde Buscar Ajuda

### 1. **Documentação do Projeto**
- `README.md` - Visão geral
- `CONTEXT.md` - Arquitetura
- `DOCKER.md` - Como usar Docker
- `.github/README.md` - CI/CD

### 2. **Logs e Debug**
```bash
# Logs da aplicação
docker-compose logs webscrapping

# Logs do GitHub Actions
# GitHub → Actions → Click na execução
```

### 3. **Comunidade**
- **Selenium**: https://selenium-python.readthedocs.io/
- **Docker**: https://docs.docker.com/
- **GitHub Actions**: https://docs.github.com/en/actions

### 4. **Ferramentas Debug**
- **Browser DevTools**: F12 no Chrome
- **Docker Desktop**: Interface gráfica
- **VS Code Extensions**: Python, Docker

---

**🎉 Agora você tem tudo para desenvolver com confiança!**

**Lembre-se**: 
- ✅ Comece pequeno
- ✅ Teste sempre  
- ✅ Use branches para features grandes
- ✅ GitHub Actions é seu amigo - ele previne bugs
- ✅ Docker simplifica tudo

**Boa sorte no desenvolvimento! 🚀**