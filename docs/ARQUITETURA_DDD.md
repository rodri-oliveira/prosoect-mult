# Padrões de Arquitetura DDD - CRM Prospecção

## Princípios Fundamentais

- **Interfaces são adaptadores finos**: apenas recebem request, convertem para DTOs e delegam
- **Application encapsula regras**: use cases com responsabilidade única
- **Domain define contratos**: repositories (Protocol), entidades e DTOs
- **Infrastructure implementa**: SQLite, APIs externas, PDF, etc.
- **Container injeta**: todas as dependências vêm do composition root

---

## Onde cada coisa entra

### 1. Nova funcionalidade (fluxo completo)

```
┌─────────────────────────────────────────────────────────────┐
│ Passo a passo para adicionar feature                        │
├─────────────────────────────────────────────────────────────┤
│ 1. Criar contrato em domain/repositories/                   │
│    └── NovoRepository (Protocol)                            │
│                                                             │
│ 2. Implementar em infrastructure/repositories/             │
│    └── SqliteNovoRepository (concreto)                     │
│                                                             │
│ 3. Adicionar ao container                                  │
│    └── infrastructure/container.py: novo_repository()       │
│                                                             │
│ 4. Criar use cases em application/<modulo>/                │
│    └── DTOs (Request/Response)                              │
│    └── Função with_repo(req, repo) -> Response            │
│    └── Função convenience (opcional): fn(req)               │
│                                                             │
│ 5. Atualizar rotas em interfaces/web/routes.py ou api/     │
│    └── Importar use case e repository do container          │
│    └── Chamar use case com injeção                        │
│                                                             │
│ 6. Validar: py -m compileall .                             │
└─────────────────────────────────────────────────────────────┘
```

### 2. Nova query/listagem

```python
# Domain (contrato)
class NovoRepository(Protocol):
    def listar_por_filtro(self, filtro: str) -> list[dict]: ...

# Infrastructure (implementação)
class SqliteNovoRepository:
    def listar_por_filtro(self, filtro: str) -> list[dict]:
        # SQL aqui, nunca em rota ou use case
        pass

# Application (use case opcional se houver regra)
@dataclass
class ListarRequest:
    filtro: str

def listar_com_filtro(req: ListarRequest, repo: NovoRepository) -> list[dict]:
    return repo.listar_por_filtro(req.filtro)

# Interface (rota)
def nova_rota():
    result = listar_com_filtro(
        ListarRequest(filtro=request.args.get("filtro")),
        novo_repository(),  # do container
    )
    return render_template("template.html", items=result)
```

### 3. Nova ação/mutação

```python
# Domain (contrato)
class NovoRepository(Protocol):
    def executar_acao(self, id: int, dados: dict) -> bool: ...

# Infrastructure
class SqliteNovoRepository:
    def executar_acao(self, id: int, dados: dict) -> bool:
        # Transaction, validações de DB, etc.
        pass

# Application (sempre com regra explícita)
@dataclass
class ExecutarAcaoRequest:
    id: int
    campo: str

@dataclass
class ExecutarAcaoResult:
    ok: bool
    mensagem: str | None = None

def executar_acao(req: ExecutarAcaoRequest, repo: NovoRepository) -> ExecutarAcaoResult:
    # Validações de negócio aqui
    if not req.campo:
        return ExecutarAcaoResult(ok=False, mensagem="Campo obrigatório")
    
    ok = repo.executar_acao(req.id, {"campo": req.campo})
    return ExecutarAcaoResult(ok=ok)

# Interface
@routes.route("/novo/<int:id>/acao", methods=["POST"])
def acao(id: int):
    result = executar_acao(
        ExecutarAcaoRequest(id=id, campo=request.form.get("campo")),
        novo_repository(),
    )
    if not result.ok:
        return redirect(url_for("rota", erro=result.mensagem))
    return redirect(url_for("outra_rota"))
```

---

## Anti-padrões (nunca fazer)

| ❌ Anti-padrão | ✅ Correto |
|--------------|-----------|
| SQL em rota ou use case | SQL apenas em repository |
| Rota com lógica de negócio | Rota só valida input e delega |
| Use case instanciando repository | Use case recebe repo como parâmetro |
| Import direto de sqlite3 fora de infrastructure/ | Todo DB access via repository |
| Template acessando funções de service legado | Template usa dados do use case |
| Função com múltiplas responsabilidades (listar + criar + atualizar) | Uma função = uma ação |

---

## Checklist antes de commit

- [ ] `py -m compileall .` passa sem erro
- [ ] Não há SQL fora de `infrastructure/repositories/`
- [ ] Novo código usa container para dependências
- [ ] Use case tem DTOs (Request/Response) tipados
- [ ] Não duplique funções (verificar se já existe no projeto)
- [ ] Template recebe dados já processados (não faz lógica complexa)

---

## Estrutura de pastas atual

```
prospect-mult/
├── domain/
│   └── repositories/          # Contratos (Protocol)
├── application/
│   ├── prospeccao/           # Use cases de prospecção
│   ├── leads/                # Use cases de leads
│   ├── agendamentos/         # Use cases de agendamentos
│   ├── maps/                 # Use cases de maps
│   └── relatorios/           # Use cases de relatórios
├── infrastructure/
│   ├── repositories/         # Implementações SQLite
│   └── container.py          # Composition root
├── interfaces/
│   ├── web/routes.py         # Rotas Flask (adaptadores)
│   └── api/routes.py         # API Flask (adaptadores)
├── services/                 # Infra/utilitários (CNPJ, PDF, Scraping)
└── templates/                # Jinja2 (apenas apresentação)
```

---

## Evolução futura (quando necessário)

### Se precisar trocar SQLite por Postgres
1. Criar `infrastructure/repositories/postgres_novo_repository.py`
2. Implementar mesmo contrato `NovoRepository`
3. Alterar `container.py` para retornar a nova implementação
4. Zero mudança em application/ ou interfaces/

### Se precisar extrair para microserviço
1. Use cases já estão desacoplados (recebem repos via interface)
2. Rotas viram handlers de mensagens (fila) ou endpoints HTTP
3. Repositories viram clients de API ou mantêm DB próprio

### Se precisar adicionar cache
1. Criar `infrastructure/cache/` com implementações
2. Repository pode usar cache internamente
3. Ou use case pode orquestrar cache + repository

---

## Referência rápida: padrões de nomenclatura

| Elemento | Padrão | Exemplo |
|----------|--------|---------|
| Repository | `<Entidade>Repository` | `LeadRepository` |
| Impl SQLite | `Sqlite<Entidade>Repository` | `SqliteLeadRepository` |
| Use case | `<acao>_<entidade>_with_repo` | `create_lead_with_repo` |
| Request DTO | `<Acao><Entidade>Request` | `CreateLeadRequest` |
| Response DTO | `<Acao><Entidade>Response` | `CreateLeadResponse` |
| Container | `<entidade>_repository()` | `lead_repository()` |

---

## Dúvidas?

- **Onde coloco validação de CNPJ?** → `services/cnpj_service.py` (infra/utilitário) ou gateway se quiser abstrair a fonte
- **Onde coloco geração de PDF?** → `services/relatorio_pdf_service.py` (infra) ou migrar para `infrastructure/reporting/`
- **Onde coloco regra de negócio complexa?** → Use case em `application/`
- **Onde coloco query simples?** → Repository direto, rota chama repository via container
