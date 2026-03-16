# TODO - Prospect Mult

## Concluído ✅
- [x] Dividir `interfaces/web/routes.py` por contexto (DDD)
- [x] Migrar JS inline para módulos ES6
- [x] Corrigir testes unitários (30/30 passando)
- [x] Remover arquivos não utilizados
- [x] Corrigir botão "Resultados (beta)" do drawer

## Em Andamento 🔄
- [ ] Testar UI completa

## Pendente 📋
- [ ] **Otimizar query Maps** - Adicionar logs e UI com estatísticas
  - [ ] Logs: quantas lojas únicas após deduplicação
  - [ ] Logs: overlap entre queries
  - [ ] UI: contador de lojas únicas visível
  - [ ] UI: estatísticas de busca

## Discussão Registrada
Ver memória: "Otimização de Query Maps - Discussão Pendente"

### Decisões
- NÃO implementar pesos por volume (Curva ABC é direcionador, não filtro)
- Manter queries amplas (não afunilar)
- Deduplicação já existe via `maps_place_id`
- Precisa de mais dados para decidir quais termos B2B manter

### Termos B2B
- ✅ Manter: distribuidor, revenda, loja
- ❓ Testar: atacadista, representante, fornecedor (podem ser redundantes)
