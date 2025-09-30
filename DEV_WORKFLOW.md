# 🔄 Fluxo de Desenvolvimento Diário

**Guia prático para trabalhar no radar-webscrapping no dia a dia**

## 🌅 Começando o Dia de Trabalho

### 1. **Setup Inicial (primeira vez no dia)**

```bash
# Navegue até o projeto
cd c:\Users\jamil\Documents\programming\radar-webscrapping

# Atualize o código
git pull origin main

# Suba o ambiente Docker
docker-compose up -d

# Verifique se tudo subiu
docker-compose ps
```

**O que você verá se tudo estiver OK:**
```
Name                     State       Ports
webscrapping             Up          0.0.0.0:8000->8000/tcp
postgres                 Up          5432/tcp
redis                    Up          6379/tcp
```

### 2. **Verificação Rápida do Sistema**

```bash
# Teste básico - aplicação responde?
docker-compose exec webscrapping python main.py status

# Teste scraping simples
docker-compose exec webscrapping python main.py scrape-cursos --help
```

---

## 🛠️ Desenvolvendo uma Nova Feature

### Cenário: "Preciso modificar como o scraper coleta dados de componentes curriculares"

#### Passo 1: Entender o Código Atual

```bash
# Ver estrutura dos scrapers
ls src/scrapers/

# Ler código atual (exemplo)
cat src/scrapers/componente_scraper.py
```

#### Passo 2: Criar Branch para Trabalhar

```bash
# Criar branch descritiva
git checkout -b feature/melhorar-coleta-componentes

# Verificar que está na branch certa
git branch
```

#### Passo 3: Fazer Alterações

**Exemplo prático - Modificar URL de coleta:**

```python
# Em src/scrapers/componente_scraper.py

class ComponenteScraper:
    def __init__(self):
        # ANTES:
        self.base_url = "https://sigaa.ufba.br/sigaa/geral/componente_curricular/busca_geral.jsf"
        
        # DEPOIS (sua alteração):
        self.base_url = "https://sigaa.ufba.br/sigaa/graduacao/componente_curricular/lista.jsf"
        
    def coletar_componentes(self):
        # Sua lógica aqui
        pass
```

#### Passo 4: Testar Alteração Localmente

```bash
# Teste específico da sua alteração
docker-compose exec webscrapping python -c "
from src.scrapers.componente_scraper import ComponenteScraper
scraper = ComponenteScraper()
print('URL configurada:', scraper.base_url)
"

# Teste funcional
docker-compose exec webscrapping python main.py scrape-componentes --codigo "MAT001"
```

#### Passo 5: Executar Testes Completos

```bash
# Testes relacionados aos componentes
docker-compose exec webscrapping pytest tests/ -k "componente" -v

# Se criou novos testes, execute todos
docker-compose exec webscrapping pytest tests/ -v
```

#### Passo 6: Commit das Alterações

```bash
# Verificar o que mudou
git status
git diff

# Adicionar arquivos modificados
git add src/scrapers/componente_scraper.py

# Se criou testes
git add tests/test_componente_scraper.py

# Commit com mensagem descritiva
git commit -m "feat: atualizar URL de coleta de componentes curriculares

- Mudança da URL de busca geral para lista específica
- Melhora na precisão dos dados coletados
- Testes atualizados para nova URL"

# Push da branch
git push origin feature/melhorar-coleta-componentes
```

#### Passo 7: Pull Request e Testes Automáticos

```bash
# No GitHub:
# 1. Vá para seu repositório
# 2. GitHub mostrará "Compare & pull request"
# 3. Clique e descreva suas mudanças
# 4. Create pull request
```

**GitHub Actions automaticamente:**
- ✅ Roda todos os testes
- ✅ Verifica qualidade do código
- ✅ Faz build Docker
- ✅ Verifica segurança

#### Passo 8: Merge (só se tudo passou)

```bash
# Se CI passou:
# → GitHub: Merge pull request

# Limpar localmente:
git checkout main
git pull origin main
git branch -d feature/melhorar-coleta-componentes
```

---

## 🐛 Debuggando Problemas

### Cenário: "Scraper não está coletando dados"

#### Debug Passo a Passo:

#### 1. **Verificar Logs Básicos**

```bash
# Ver logs recentes
docker-compose logs --tail=50 webscrapping

# Logs em tempo real
docker-compose logs -f webscrapping
```

#### 2. **Entrar no Container para Debug Manual**

```bash
# Abrir bash no container
docker-compose exec webscrapping bash

# Você agora está dentro do container
# Teste Python interativo
python
```

#### 3. **Debug Interativo**

```python
# No Python dentro do container:

# Testar imports
>>> from src.scrapers.curso_scraper import CursoScraper
>>> from selenium import webdriver
>>> from selenium.webdriver.chrome.options import Options

# Configurar Chrome para ver o que está acontecendo
>>> options = Options()
>>> options.add_argument('--no-sandbox')
>>> options.add_argument('--disable-dev-shm-usage')
>>> # Para debug visual, remova headless:
>>> # options.add_argument('--headless=false')

>>> driver = webdriver.Chrome(options=options)

# Testar conexão com SIGAA
>>> driver.get('https://sigaa.ufba.br')
>>> print("Título da página:", driver.title)
>>> print("URL atual:", driver.current_url)

# Se chegou até aqui, Selenium funciona
# Agora teste seu scraper
>>> scraper = CursoScraper()
>>> # Teste métodos individuais
>>> driver.quit()
>>> exit()
```

#### 4. **Debug de URL Específica**

```python
# Teste se uma URL específica funciona
>>> import requests
>>> response = requests.get('https://sigaa.ufba.br/sigaa/geral/curso/busca_geral.jsf')
>>> print("Status:", response.status_code)
>>> print("Conteúdo (primeiros 200 chars):", response.text[:200])
```

#### 5. **Testar Scraper com Debug Detalhado**

```bash
# Voltar ao bash do container
exit  # sair do Python

# Executar com debug máximo
export LOG_LEVEL=DEBUG
python main.py scrape-cursos --unidade "IME" --debug

# Ver arquivos de log
ls logs/
tail -f logs/scraping.log
```

---

## 🧪 Testando Suas Alterações

### Tipos de Teste Durante Desenvolvimento:

#### 1. **Teste Rápido (Smoke Test)**

```bash
# Teste se básico funciona (30 segundos)
docker-compose exec webscrapping python -c "
from src.scrapers import CursoScraper
scraper = CursoScraper()
print('✅ Import OK')
"
```

#### 2. **Teste Funcional Específico**

```bash
# Teste uma função específica
docker-compose exec webscrapping python -c "
from src.scrapers.curso_scraper import CursoScraper
scraper = CursoScraper()
cursos = scraper.buscar_cursos_por_unidade('IME')
print(f'✅ Encontrados {len(cursos)} cursos')
"
```

#### 3. **Teste de Integração**

```bash
# Teste completo end-to-end
docker-compose exec webscrapping python main.py scrape-cursos --unidade "IME" --limit 5
```

#### 4. **Testes Unitários**

```bash
# Executar testes específicos
docker-compose exec webscrapping pytest tests/test_curso_scraper.py -v

# Teste com coverage
docker-compose exec webscrapping pytest tests/ --cov=src --cov-report=term-missing
```

#### 5. **Teste de Performance**

```bash
# Medir tempo de execução
docker-compose exec webscrapping python -c "
import time
from src.scrapers.curso_scraper import CursoScraper

start = time.time()
scraper = CursoScraper()
cursos = scraper.buscar_cursos_por_unidade('IME')
end = time.time()

print(f'⏱️ Tempo: {end-start:.2f}s')
print(f'📊 Cursos/segundo: {len(cursos)/(end-start):.2f}')
"
```

---

## 🔄 Workflow para Diferentes Tipos de Mudança

### 1. **Bug Fix Simples (método rápido)**

```bash
# Para correções pequenas, trabalhe direto na main
git pull origin main

# Faça a correção
# ... edite arquivos ...

# Teste rápido
docker-compose exec webscrapping python main.py status

# Commit e push
git add .
git commit -m "fix: corrigir typo na URL do SIGAA"
git push origin main

# GitHub Actions testa automaticamente
```

### 2. **Nova Feature (método seguro)**

```bash
# Sempre usar branch
git checkout -b feature/nova-funcionalidade

# Desenvolver
# ... suas alterações ...

# Testar localmente
pytest tests/

# Push da branch
git push origin feature/nova-funcionalidade

# Pull Request no GitHub
# Merge só depois que CI passar
```

### 3. **Refatoração Grande**

```bash
# Branch específica
git checkout -b refactor/reorganizar-scrapers

# Trabalhar em etapas pequenas
# Commit frequentemente
git add .
git commit -m "refactor: mover classe base para módulo separado"

# Continuar...
git add .
git commit -m "refactor: atualizar imports após reorganização"

# Push da branch
git push origin refactor/reorganizar-scrapers

# Pull Request com descrição detalhada
```

---

## 📊 Monitorando Qualidade do Código

### Durante Desenvolvimento:

#### 1. **Qualidade de Código (Linting)**

```bash
# Verificar estilo do código
docker-compose exec webscrapping flake8 src/

# Formatação automática
docker-compose exec webscrapping black src/

# Verificar tipos
docker-compose exec webscrapping mypy src/
```

#### 2. **Cobertura de Testes**

```bash
# Ver cobertura atual
docker-compose exec webscrapping pytest tests/ --cov=src --cov-report=html

# Abrir relatório HTML (fora do container)
# Vai criar htmlcov/index.html
# Abra no navegador para ver detalhes
```

#### 3. **Análise de Segurança**

```bash
# Verificar vulnerabilidades em dependências
docker-compose exec webscrapping safety check

# Análise de código
docker-compose exec webscrapping bandit -r src/
```

---

## 🚀 Preparando para Deploy

### Antes de Fazer Release:

#### 1. **Teste Local Completo**

```bash
# Executar todos os testes
docker-compose exec webscrapping pytest tests/ -v

# Teste de build
docker build -t radar/webscrapping:test .

# Teste do container build
docker run --rm radar/webscrapping:test cli --help
```

#### 2. **Verificar Documentação**

```bash
# README.md atualizado?
# CHANGELOG.md atualizado?
# Versão no requirements.txt?
```

#### 3. **Create Release Tag**

```bash
# Certifique-se que está na main
git checkout main
git pull origin main

# Criar tag de versão
git tag v1.0.0
git push origin v1.0.0

# GitHub Actions automaticamente:
# - Faz build de produção
# - Cria release no GitHub
# - Publica Docker image
```

---

## 🎯 Comandos de Emergência

### "Algo deu muito errado!"

#### 1. **Reset Completo do Ambiente**

```bash
# Parar tudo
docker-compose down -v

# Limpar containers
docker system prune -f

# Remover imagens
docker rmi radar/webscrapping

# Reconstruir do zero
docker-compose build --no-cache
docker-compose up -d
```

#### 2. **Voltar para Última Versão que Funcionava**

```bash
# Ver commits recentes
git log --oneline -10

# Voltar para commit específico
git reset --hard [hash-do-commit]

# Força push (CUIDADO!)
git push origin main --force
```

#### 3. **Backup dos Dados**

```bash
# Backup do banco local
docker-compose exec postgres pg_dump -U postgres radar_webscrapping > backup.sql

# Backup de logs
docker-compose exec webscrapping tar czf /tmp/logs-backup.tar.gz logs/
docker cp webscrapping_container:/tmp/logs-backup.tar.gz ./
```

---

## 📈 Métricas de Qualidade

### Acompanhe Estes Indicadores:

#### 1. **Build Time**
- GitHub Actions deve completar em < 20 minutos
- Se está demorando mais, otimize

#### 2. **Test Coverage**
- Objetivo: > 80%
- Comando: `pytest tests/ --cov=src`

#### 3. **Code Quality**
- Sem erros de flake8
- Sem warnings de mypy

#### 4. **Performance de Scraping**
- Cursos: < 30 segundos para uma unidade
- Componentes: < 60 segundos para um curso

---

## 📝 Checklist Diário

### Antes de Começar:
- [ ] `git pull origin main`
- [ ] `docker-compose up -d`
- [ ] `docker-compose ps` (tudo UP?)

### Durante Desenvolvimento:
- [ ] Trabalhar em branch para features
- [ ] Testar localmente antes de commit
- [ ] Commits pequenos e frequentes
- [ ] Mensagens de commit descritivas

### Antes de Finalizar:
- [ ] `pytest tests/` (todos passam?)
- [ ] `git status` (tudo commitado?)
- [ ] Push da branch
- [ ] CI passou no GitHub?

### Limpeza:
- [ ] Merge da branch
- [ ] Delete branch local
- [ ] `docker-compose down` (se não vai usar)

---

**🎉 Com este fluxo, você desenvolve com segurança e qualidade!**

**Lembre-se:**
- ✅ Docker simplifica o ambiente
- ✅ GitHub Actions previne bugs em produção
- ✅ Branches protegem código principal
- ✅ Testes garantem qualidade
- ✅ Logs ajudam no debug

**Bom desenvolvimento! 🚀**