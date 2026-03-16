# TODO - Prospect Mult

## Concluído ✅
- [x] Dividir `interfaces/web/routes.py` por contexto (DDD)
- [x] Migrar JS inline para módulos ES6
- [x] Corrigir testes unitários (30/30 passando)
- [x] Remover arquivos não utilizados
- [x] Corrigir botão "Resultados (beta)" do drawer
- [x] Corrigir erro `window.open` em botões
- [x] Logs detalhados com estatísticas de lojas únicas
- [x] UI com contador de lojas únicas no drawer
- [x] Corrigir autocomplete de cidade - Alpine.js
- [x] Otimizar query Maps - remover termos B2B redundantes

## Análise de Logs (16/03/2026)

### Resultados originais (32 queries)
- 900 lojas encontradas → 138 únicas (15% aproveitamento)
- ~8 minutos de busca

### Eficiência por termo B2B
| Termo | Lojas únicas | % |
|-------|-------------|---|
| distribuidor | 119 | 86% |
| loja | 9 | 7% |
| representante | 7 | 5% |
| revenda | 5 | 4% |
| atacadista | 3 | 2% |
| fornecedor | 3 | 2% |

### Otimização implementada
- Manter: `distribuidor`, `loja`
- Remover: `atacadista`, `revenda`, `fornecedor`
- Adicionar: marcas relevantes (Multilaser, Lenovo, Dell...)
- Adicionar: exclusão `-fechado`

### Resultado esperado
- ~16 queries (50% redução)
- ~4 minutos de busca
- Cobertura similar ou maior (marcas)
