# 🤖 GitHub Actions Workflows

Este diretório contém todos os workflows de CI/CD do projeto Radar WebScrapping.

## 📋 Workflows Disponíveis

### 1. 🔍 `ci-cd.yml` - Pipeline Completo
**Trigger**: Push/PR para `main` e `develop`, tags `v*`

**Jobs**:
- **Lint**: Code quality, formatação, type checking
- **Test**: Testes unitários e integração com PostgreSQL/Redis
- **Build**: Build e push da imagem Docker
- **Integration Test**: Testes com containers
- **Security**: Scan de vulnerabilidades com Trivy
- **Deploy**: Deploy automático para tags (produção)
- **Cleanup**: Limpeza de packages antigos

**Duração**: ~15-20 minutos

### 2. 🔍 `ci-simple.yml` - Pipeline Simplificado
**Trigger**: Push/PR para `main` e `develop`

**Jobs**:
- **Simple CI**: Lint, tests básicos, build Docker
- Setup Chrome/ChromeDriver
- Testes com PostgreSQL/Redis

**Duração**: ~8-12 minutos

### 3. 🤖 `dependencies.yml` - Atualização de Dependências  
**Trigger**: Agendado (segundas 9h UTC), manual

**Jobs**:
- **Update Dependencies**: Auto-update requirements.txt
- **Security Audit**: Scan de vulnerabilidades
- **Docker Base Check**: Verificar updates da imagem base

**Duração**: ~5 minutos

### 4. 🚀 `release.yml` - Pipeline de Release
**Trigger**: Tags `v*.*.*`, manual

**Jobs**:
- **Pre-Release Validation**: Validar formato da versão
- **Release Build**: Build multi-platform 
- **Release Test**: Testes específicos de release
- **Create Release**: Criar release no GitHub
- **Notify Integration**: Notificar radar-infra

**Duração**: ~25-30 minutos

### 5. 🧹 `cleanup.yml` - Manutenção Automática
**Trigger**: Agendado (domingos 2h UTC), manual

**Jobs**:
- **Cleanup Cache**: Limpar cache do GitHub Actions
- **Cleanup Packages**: Remover imagens Docker antigas
- **Cleanup Artifacts**: Remover artefatos antigos
- **Repository Health**: Health check do repositório

**Duração**: ~3-5 minutos

## 🔧 Configuração Necessária

### Secrets do GitHub
```
GITHUB_TOKEN - Automático, usado para packages
```

### Permissions
O repositório precisa das seguintes permissões:
- **Actions**: read/write
- **Contents**: read/write
- **Packages**: write
- **Security**: write (para SARIF uploads)

### Configuração do Repositório

#### 1. Habilitar GitHub Packages
```bash
# Settings > General > Features
☑️ GitHub Packages
```

#### 2. Configurar Branch Protection
```bash
# Settings > Branches > Add rule para 'main'
☑️ Require status checks to pass
☑️ Require branches to be up to date
- ✅ lint
- ✅ test
☑️ Require pull request reviews
☑️ Dismiss stale reviews
☑️ Restrict pushes
```

#### 3. Configurar Environments
```bash
# Settings > Environments > New environment
Name: production
☑️ Required reviewers: [seu-usuario]
```

## 🚦 Status Badges

Adicione ao README.md:

```markdown
[![CI/CD](https://github.com/devruso/radar-webscrapping/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/devruso/radar-webscrapping/actions/workflows/ci-cd.yml)
[![Dependencies](https://github.com/devruso/radar-webscrapping/actions/workflows/dependencies.yml/badge.svg)](https://github.com/devruso/radar-webscrapping/actions/workflows/dependencies.yml)
[![Release](https://github.com/devruso/radar-webscrapping/actions/workflows/release.yml/badge.svg)](https://github.com/devruso/radar-webscrapping/actions/workflows/release.yml)
```

## 📊 Workflow Tips

### Executar Workflows Manualmente

```bash
# Via GitHub CLI
gh workflow run ci-cd.yml

# Via GitHub CLI com inputs
gh workflow run release.yml -f version=v1.0.0

# Via interface web
# Actions > Select workflow > Run workflow
```

### Debug de Workflows

```bash
# Ver logs
gh run list
gh run view [run-id]

# Download artifacts
gh run download [run-id]
```

### Desenvolvimento Local

```bash
# Instalar act (GitHub Actions local)
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Executar workflow localmente
act -j lint  # Executar job específico
act push     # Simular push event
```

## 🔒 Security

### SARIF Upload
Os workflows fazem upload automático de resultados de segurança:
- **Bandit**: Análise de código Python
- **Trivy**: Scan de vulnerabilidades Docker
- **Safety**: Vulnerabilidades em dependências

### Dependabot
Configure no `.github/dependabot.yml`:
- ✅ Python dependencies 
- ✅ Docker base images
- ✅ GitHub Actions

### Secrets Scanning
- ✅ Detect-secrets no pre-commit
- ✅ GitHub native secret scanning

## 📈 Monitoring

### Workflow Metrics
- **Build time**: Média 15min (CI/CD completo)
- **Success rate**: >95% (objetivo)
- **Cache hit rate**: >80% (dependencies)

### Alerts
Configure notificações para:
- ❌ Workflow failures
- 🐌 Build time > 30min
- 🔒 Security vulnerabilities

## 🚀 Release Process

### Automatic (Recomendado)
```bash
git tag v1.0.0
git push origin v1.0.0
# Pipeline automático de release
```

### Manual
```bash
# GitHub Actions > release.yml > Run workflow
# Input: version = v1.0.0
```

### Release Notes
São geradas automaticamente incluindo:
- 📦 Docker images
- 🔧 Integration instructions
- 📋 Changelog
- 🛡️ Security info
- 🧪 Test coverage

## 🤝 Contributing

### Para adicionar novo workflow:

1. **Criar arquivo**: `.github/workflows/nome.yml`
2. **Testar localmente**: `act -j job-name`
3. **Documentar**: Adicionar seção neste README
4. **PR**: Incluir testes do workflow

### Boas práticas:
- ✅ Jobs paralelos quando possível
- ✅ Cache de dependências
- ✅ Fail fast em erros críticos
- ✅ Artifacts para debugging
- ✅ Matrix builds para multi-platform

---

**Desenvolvido para o Sistema Radar** 🎯  
**CI/CD com GitHub Actions** 🤖