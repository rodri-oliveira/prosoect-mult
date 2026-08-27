# Multi Prospect CRM 🚀

Uma solução robusta de CRM e Prospecção Inteligente desenvolvida para otimizar o ciclo de vendas B2B, desde a descoberta de leads até o fechamento de contratos.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)
![SQLite](https://img.shields.io/badge/SQLite-3-lightgrey.svg)
![Clean Architecture](https://img.shields.io/badge/Architecture-Clean%20/%20Hexagonal-orange.svg)

## 🌟 Destaques do Projeto

Este projeto foi construído com foco em **escalabilidade**, **manutenibilidade** e **experiência do usuário (UX)**. Utiliza princípios de **Clean Architecture** para garantir que as regras de negócio permaneçam isoladas de detalhes técnicos como bancos de dados ou frameworks web.

### Funcionalidades Principais

- 🔍 **Prospecção Geográfica**: Busca automatizada de empresas via integração com Google Maps.
- 🏢 **Enriquecimento de Dados**: Validação e consulta automática de dados cadastrais (CNPJ) via BrasilAPI.
- 📅 **Gestão de Agendamentos**: Sistema inteligente de retornos com alertas de atraso e "rolagem" automática de pendências.
- 🎯 **Pipeline de Vendas**: Workflow completo para converter rascunhos de prospecção em leads qualificados.
- 📄 **Automação de Documentos**: Geração dinâmica de PDFs para propostas comerciais e especificações técnicas.
- 📊 **Dashboard Estratégico**: Visualização de métricas de desempenho e status do funil em tempo real.

---

## 🏗️ Arquitetura e Design Patterns

O projeto foi estruturado seguindo os princípios de **Clean Architecture (Arquitetura Limpa / Hexagonal)** e **Domain-Driven Design (DDD)**. Esta abordagem separa as regras de negócio de detalhes de implementação como frameworks web ou bancos de dados.

O sistema é dividido em três camadas fundamentais com fluxos de dependência unidirecionais:

*   **`domain/` (Domínio / Core)**: Contém as regras de negócio fundamentais e define as interfaces de repositórios e serviços externos usando `Protocol` em Python. É uma camada pura, sem dependências de frameworks ou infraestrutura.
*   **`application/` (Casos de Uso)**: Contém a lógica de aplicação e orquestração do sistema (ex: registro de tentativas de contato, conversão de lead). Cada caso de uso é isolado, facilitando testes de unidade.
*   **`infrastructure/` & `interfaces/` (Detalhes)**: Contém as implementações concretas (acesso a dados com SQLite usando o **Repository Pattern**, gateways de API externa como a BrasilAPI e integradores de busca do Google Maps) e a camada de entrega da aplicação (rotas do Flask e templates web).

A fiação e o ciclo de vida dessas camadas são desacoplados por meio de um contêiner central de **Injeção de Dependências** (`infrastructure/container.py`).

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Flask.
- **Banco de Dados**: SQLite (escolhido pela simplicidade e portabilidade).
- **Frontend**: HTML5, Tailwind CSS, JavaScript (ES6+), HTMX (para interações SPA-like).
- **Integrações**: Google Maps API, BrasilAPI (CNPJ).
- **Geração de PDF**: ReportLab / FPDF2.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
- Python 3.11 ou superior instalado.

### 1. Clonar e Instalar Dependências
```powershell
# Criar ambiente virtual
py -3 -m venv .venv

# Ativar ambiente (Windows)
.\.venv\Scripts\activate

# Instalar dependências
pip install -r requirements.txt

# Instalar o navegador usado pelo Playwright na busca do Maps
playwright install chromium
```

### 2. Configuração
Crie um arquivo `.env` na raiz do projeto e adicione suas chaves (veja `.env.example` se disponível):
```env
FLASK_DEBUG=True
GOOGLE_MAPS_API_KEY=sua_chave_aqui
```

### 3. Iniciar a Aplicação
```powershell
python app.py
```
Acesse: `http://localhost:5000`

---

## 👨‍💻 Autor

Desenvolvido por **Rodrigo Oliveira**.
Projeto focado em demonstrar competências em **Arquitetura de Software**, **Desenvolvimento Fullstack** e **Resolução de Problemas Complexos de Negócio**.

---
*Este é um projeto profissional pronto para produção, com foco em performance e robustez.*
