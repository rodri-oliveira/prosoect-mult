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

## Próximos Passos 📋
- [ ] Analisar logs de busca para identificar:
  - Quais termos B2B trazem mais lojas únicas
  - Quais termos são redundantes (new_unique=0)
  - Tempo por query para otimizar performance

## Discussão Registrada
Ver memória: "Otimização de Query Maps - Discussão Pendente"

### Dados para coletar
Após algumas buscas, verificar nos logs:
- `new_unique` por query → termos que trazem lojas novas
- `total_unique` acumulado → cobertura total
- `ms` por query → tempo de execução

### Termos B2B atuais
- distribuidor, atacadista, representante, revenda, fornecedor
- loja (varejo)

### Decisão pendente
Com dados reais, decidir quais termos manter/remover.
