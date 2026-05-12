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

O sistema segue padrões modernos de desenvolvimento de software:

*   **Domain-Driven Design (DDD)**: Domínio rico com interfaces de repositório bem definidas.
*   **Dependency Injection**: Container de serviços para desacoplamento de componentes.
*   **Repository Pattern**: Abstração total do acesso a dados (SQLite).
*   **Use Cases (Application Layer)**: Lógica de negócio encapsulada em casos de uso independentes.
*   **Modular JS**: Interface frontend reativa e modularizada sem a necessidade de frameworks pesados.

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
