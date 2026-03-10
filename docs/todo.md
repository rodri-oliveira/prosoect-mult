# CRM Prospecção B2B — TODO List

## Concluído

- [x] Backend Flask + SQLite + Templates Jinja2
- [x] Dashboard com métricas do dia — **FIX:** Cards agora são legíveis em 3 colunas
- [x] Cadastro de Leads com modal rápido
- [x] Listagem de Leads com status e filtros
- [x] Página de detalhe do Lead com histórico de contatos
- [x] Fila de Ligação (Prospecção) — **FIX:** Enriquecida com segmento, observações, contador e clipboard
- [x] Prospecção Ativa com Google Maps integrado (iframe + link externo)
- [x] Filtros ricos: Segmentos (múltipla escolha), Cidade (autocompelte via IBGE), Estado (UF)
- [x] Formulário expandido na Prospecção (telefone, WhatsApp, endereço, responsável, observações)
- [x] Botões "Salvar + Ligar" e "Salvar + WhatsApp"
- [x] Redirect back para /prospeccao após salvar lead
- [x] Relatório Diário com Copiar para Clipboard e Gerar PDF
- [x] Testes E2E automatizados com Playwright
- [x] Configuração do VS Code para Python
- [x] Sidebar dinâmico — destaca a página ativa automaticamente

## Em Andamento

- [/] Relatório Diário — formatando para layout profissional para a gestora

## Backlog (Futuro)

- [ ] Filtro de leads por status na listagem (tabs ou dropdown)
- [ ] Lead Speed — mostrar "X dias sem contato" na lista de leads
- [ ] Pesquisar loja no Google (botão na página de detalhe do lead)
- [ ] Importação de lista de empresas via CSV/Excel
- [ ] Integração com API de CNPJ (ReceitaWS)
- [ ] Score de leads (baseado em interações e resultado)
- [ ] Mapa de clientes (visualização geográfica)
- [ ] Busca automática de empresas (Google Places API — requer chave paga)
- [ ] Múltiplos segmentos por lead no banco de dados (tabela N:N)
- [ ] Linhas de Produto (Grupo Multi, Multikids, Multi Saúde, Blue Pet) associadas ao lead
- [ ] Exportação de relatório semanal/mensal
