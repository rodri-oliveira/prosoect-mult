# 🚀 Plano de Implementação: Faturamento e Pós-Venda Inteligente

Este documento detalha a expansão do CRM para suportar o gerenciamento de **Clientes Ativos**, histórico de pedidos e automação de recompra.

## 1. Modelagem de Dados (ERD)

### Nova Tabela: `pedidos`
Armazena o cabeçalho de cada venda realizada.
- `id` (INTEGER, PK): Identificador único.
- `lead_id` (INTEGER, FK): Linca ao cliente na tabela `leads`.
- `data_pedido` (DATE): Data da realização da venda.
- `numero_pedido` (TEXT): ID opcional (ex: número da Nota Fiscal ou ERP).
- `valor_total` (REAL): Valor somado de todos os itens.
- `status` (TEXT): 'Aguardando', 'Faturado', 'Cancelado'.
- `data_proximo_contato` (DATE): Opcional - para automação de CS/Pós-Venda.
- `data_criacao` (DATETIME): Registro de auditoria.

### Nova Tabela: `pedido_itens`
Armazena o detalhamento de produtos de cada pedido (Baseado no padrão Multilaser).
- `id` (INTEGER, PK): Identificador da linha.
- `pedido_id` (INTEGER, FK): Linca ao cabeçalho `pedidos`.
- `familia` (TEXT): Categoria do produto (ME, AC, AC, etc).
- `codigo_produto` (TEXT): SKU do produto (ex: PD588).
- `descricao` (TEXT): Nome detalhado do produto.
- `quantidade` (INTEGER): Qtd vendida.
- `preco_unitario` (REAL): Preço de venda por unidade.
- `preco_total` (REAL): `quantidade * preco_unitario`.

---

## 2. Interface do Usuário (UI)

### A. Aba "Carteira de Clientes"
- Nova opção no menu lateral.
- Lista apenas Leads com status **"Cliente Ativo"**.
- Exibe métricas rápidas: Total Faturado e Data da Última Compra.

### B. Módulo "Converter em Venda" (Lógica de Faturamento)
- Disponível dentro do perfil de cada Lead/Rascunho.
- **Formulário Dinâmico:** Permite adicionar múltiplas linhas de produtos (Família, SKU, Qtd).
- **Cálculo em Tempo Real:** JavaScript para somar o valor total conforme os itens são preenchidos.
- **Agendador de Retorno:** Seleção de data para "Próxima Venda" (+15, +30 ou data livre).

---

## 3. Fluxo de Automação (Retention Bot)

Ao salvar o pedido:
1.  **Status Sync:** Se o Lead era "Interessado" ou "Prospecção", ele é movido automaticamente para **"Cliente Ativo"**.
2.  **Agendador:** Caso uma "Data de Próximo Contato" seja definida, o sistema cria automaticamente um alerta que aparecerá na tela de **Agendamentos** com o selo **"Re-compra"**.
3.  **Histórico Unificado:** Todas as interações (ligações e vendas) aparecem na mesma timeline para você não perder o contexto.

---

## 4. Próximos Passos de Desenvolvimento

1.  [ ] Migração do banco de dados (`database.py`).
2.  [ ] Implementação do Repositório de Vendas (`infrastructure`).
3.  [ ] Criação dos templates HTML para Pedidos e Listagem de Carteira.
4.  [ ] Lógica de JS para o carrinho de compras interno do formulário.
