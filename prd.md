# PRD – CRM de Prospecção B2B para Vendas Internas (Grupo Multi)

## 1. Visão Geral

Desenvolver um CRM simples focado em prospecção de empresas (CNPJ) para vendas B2B.

O sistema será utilizado por um vendedor interno que realiza prospecção apenas por telefone ou WhatsApp.

O objetivo é:

* organizar leads de lojas
* registrar tentativas de contato
* acelerar prospecção
* gerar relatórios diários de atividade
* permitir filtros por segmentos de mercado

O sistema deve ser extremamente simples, rápido e focado em produtividade.

Ele rodará localmente no computador do usuário sem necessidade de servidor externo ou infraestrutura paga.

---

# 2. Requisitos Técnicos

## Ambiente

Sistema rodando localmente em Windows.

Interface acessada via navegador.

URL local:

http://localhost:5000

Sem dependência de cloud ou serviços pagos.

---

## Stack Tecnológica

Backend

Python
Flask

Frontend

HTML
TailwindCSS
HTMX
Alpine.js

Banco de dados

SQLite

---

## Motivos da Stack

Flask: backend leve e simples
SQLite: banco local sem configuração
HTMX: interface dinâmica sem frameworks pesados
Tailwind: estilização rápida
Alpine.js: pequenas interações de interface

---

# 3. Estrutura do Projeto

Estrutura de pastas sugerida:

crm_prospeccao/

app.py
database.db

/templates
layout.html
dashboard.html
leads.html
lead_detalhe.html
prospeccao.html
fila_prospeccao.html
relatorio.html

/static
/css
/js

/models
lead.py
contato.py

/services
lead_service.py
relatorio_service.py
prospeccao_service.py

---

# 4. Funcionalidades Principais

## 4.1 Dashboard

Tela inicial com resumo do dia.

Exibir:

Ligações realizadas hoje
WhatsApp enviados hoje
Contatos efetivos
Novos leads cadastrados
Interessados
Negociações em andamento

Objetivo: acompanhar produtividade diária.

---

# 4.2 Cadastro de Leads (Lojas)

Cada lead representa uma loja ou empresa.

Campos:

id
nome_loja
cnpj (opcional)
telefone
whatsapp
email
cidade
estado
endereco
responsavel
status
observacoes
data_criacao

---

## 4.3 Segmentos de Loja

Uma loja pode possuir múltiplos segmentos.

Segmentos padrão:

Informática
Celulares
Eletrônicos
Gamer
Assistência técnica
Papelaria
Loja de brinquedos
Loja infantil
Loja de bebê
Farmácia
Pet shop
Agropecuária
Fitness
Ortopédica
Loja de presentes

---

# 4.4 Linhas de Produto (Grupo Multi)

Associar possíveis linhas de produto adequadas para a loja.

Linhas principais:

Grupo Multi (eletrônicos e acessórios)
Multikids (brinquedos)
Multikids Baby
Multi Saúde
Blue Pet

Objetivo: ajudar na abordagem comercial.

---

# 4.5 Status do Lead

Cada lead possui um status comercial.

Status disponíveis:

Novo Lead
Tentativa 1
Tentativa 2
Tentativa 3
Sem contato
Falou com responsável
Apresentação feita
Enviar catálogo
Interessado
Negociação
Cliente ativo
Sem interesse

Status deve poder ser alterado rapidamente.

---

# 4.6 Registro de Contato (Histórico)

Toda interação deve ser registrada.

Tabela de histórico de contatos.

Campos:

id
lead_id
data
tipo_contato
resultado
observacao

Tipos de contato:

Ligação
WhatsApp
Email

Exemplo:

Data: 10/03
Tipo: Ligação
Resultado: Falou com responsável
Observação: Pediu envio de catálogo

---

# 4.7 Botões de Ação Rápida

Dentro da página do lead devem existir botões rápidos.

Abrir WhatsApp

Gerar link:

https://wa.me/numero

Copiar telefone

Pesquisar loja no Google

Registrar ligação rapidamente

Objetivo: reduzir cliques durante prospecção.

---

# 4.8 Prospecção de Lojas

Tela dedicada para encontrar novos leads.

Filtros disponíveis:

estado
cidade
segmento

Exemplo:

estado: SP
cidade: Mogi das Cruzes
segmento: Pet Shop

Resultados exibem:

nome da loja
telefone
endereco
categoria

Cada resultado possui botão:

Adicionar ao CRM

---

# 4.9 Fila de Prospecção

Tela especial para trabalhar leads em sequência.

Interface exemplo:

Lead atual

Nome da loja
Telefone
Segmento
Cidade

Botões:

Ligar
WhatsApp
Sem contato
Interessado
Próximo lead

Ao clicar em uma ação:

* registra contato automaticamente
* atualiza status
* avança para próximo lead

Objetivo: maximizar produtividade de ligações.

---

# 4.10 Lead Speed (Follow-up)

Sistema deve mostrar tempo desde último contato.

Exemplo:

Tech Info — 5 dias sem contato
Pet Center — 12 dias sem contato
Mega Kids — 2 dias

Objetivo: priorizar follow-up.

---

# 4.11 Relatório Diário

Sistema gera relatório automático das atividades do dia.

Botão:

Gerar relatório

Saída exemplo:

Relatório 10/03

Ligações realizadas: 38
WhatsApp enviados: 21
Contatos efetivos: 14
Interessados: 6
Catálogos enviados: 4
Sem interesse: 5

Novos leads cadastrados: 17

Detalhamento:

Tech Info — falou com responsável
Pet Center — pediu catálogo
Baby Store — sem interesse
Mega Eletrônicos — não atendeu

Relatório deve permitir:

copiar texto
exportar PDF

---

# 5. Estrutura do Banco de Dados

Tabela leads

id
nome_loja
cnpj
telefone
whatsapp
email
cidade
estado
endereco
responsavel
status
observacoes
data_criacao

---

Tabela segmentos_loja

id
lead_id
segmento

---

Tabela contatos

id
lead_id
data
tipo_contato
resultado
observacao

---

# 6. Requisitos de UX

Sistema deve ser:

extremamente rápido
simples
com poucos cliques

Adicionar lead deve levar menos de 10 segundos.

Registrar ligação deve levar menos de 5 segundos.

---

# 7. Regras de Simplicidade

Evitar:

automações complexas
excesso de campos
integrações pagas
interfaces pesadas

Este é um CRM pessoal de produtividade.

---

# 8. Roadmap Futuro (Opcional)

Possíveis evoluções futuras:

integração com API de CNPJ
busca automática de empresas
score de leads
mapa de clientes
importação de listas de empresas

Essas funcionalidades não fazem parte da primeira versão.

---

# 9. Definição de Sucesso

O sistema será considerado bem sucedido se:

permitir organizar todos os leads em um único lugar
acelerar prospecção diária
reduzir tempo gasto organizando contatos
permitir gerar relatório diário rapidamente

Objetivo final:

aumentar o número de contatos comerciais por dia.
