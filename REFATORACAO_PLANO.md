# Plano de Refatoração DDD - Prospect-Mult

## Problemas Atuais Identificados
1. **app.py** monolítico (32KB) - todas as rotas, controllers e lógica de apresentação misturadas
2. **Templates** com JavaScript inline massivo (prospeccao.html = 65KB)
3. **Services** com múltiplas responsabilidades (prospeccao_service.py = 19KB)
4. **Acoplamento** entre UI, Application e Infrastructure
5. **Sem camada de Application** - controllers chamam services diretamente

## Nova Arquitetura - Camadas DDD

```
prospect-mult/
├── domain/                    # Regras de negócio puras
│   ├── entities/
│   │   ├── lead.py
│   │   ├── prospeccao.py
│   │   └── value_objects/
│   ├── repositories/
│   │   ├── lead_repository.py
│   │   └── prospeccao_repository.py
│   └── services/
│       ├── cnpj_validator.py
│       └── maps_identifier.py
│
├── application/               # Casos de uso / Use Cases
│   ├── commands/
│   │   ├── add_prospeccao.py
│   │   ├── converter_prospeccao.py
│   │   └── update_status.py
│   ├── queries/
│   │   ├── listar_prospeccoes.py
│   │   └── get_relatorio.py
│   └── dto/
│       ├── prospeccao_dto.py
│       └── lead_dto.py
│
├── infrastructure/            # Implementações técnicas
│   ├── database/
│   │   ├── connection.py
│   │   └── migrations/
│   ├── external_apis/
│   │   ├── ibge_client.py
│   │   ├── brasil_api.py
│   │   └── maps_scraper.py
│   └── web/
│       └── app.py            # Só bootstrap e config
│
├── interfaces/                # Adaptadores de interface
│   ├── api/
│   │   ├── controllers/
│   │   │   ├── prospeccao_controller.py
│   │   │   └── lead_controller.py
│   │   ├── routes/
│   │   │   ├── prospeccao_routes.py
│   │   │   └── lead_routes.py
│   │   └── presenters/
│   │       └── json_presenter.py
│   └── web/
│       └── static/js/
│           ├── modules/
│           │   ├── cidade-autocomplete.js
│           │   ├── maps-drawer.js
│           │   └── lead-form.js
│           └── app.js
│
└── templates/                 # Views (só HTML + Alpine mínimo)
    └── ...
```

## Fases de Implementação

### Fase 1: Isolar Domain (Entidades e Regras)
- Extrair entidades puras (Lead, Prospeccao)
- Criar value objects (CNPJ, MapsPlaceId, Endereco)
- Interfaces de Repository (contratos)

### Fase 2: Criar Camada Application
- Commands (ações que mudam estado)
- Queries (leituras otimizadas)
- DTOs para transferência de dados

### Fase 3: Refatorar Infrastructure
- Mover implementações SQLite para infrastructure/database
- Isolar chamadas externas (IBGE, BrasilAPI, Maps)
- Criar migrations versionadas

### Fase 4: Interfaces/API
- Controllers por recurso (não por função)
- Rotas organizadas por domínio
- Presenters para formatar respostas

### Fase 5: Frontend Modular
- Extrair JS do prospeccao.html
- Módulos ES6 com responsabilidade única
- Gerenciamento de estado centralizado

## Critérios de Aceite
- [ ] Cada arquivo tem < 300 linhas
- [ ] Testes unitários para Domain
- [ ] Testes de integração para Application
- [ ] Nenhum JavaScript inline nos templates
- [ ] Dependências sempre injetadas (não hardcoded)

## Começando pela Fase 1 - Domain Entities
