from application.maps.search_results import (
    _filter_large_retail,
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_varejistas_medio_porte_queries_e_exclusoes():
    result = generate_queries_for_segments(
        segmentos=["Varejistas de Médio Porte"],
        cidade="Ribeirão Preto",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("supermercado")
    assert "hipermercado" in joined
    assert "loja de móveis e eletro" in joined
    assert "atacarejo" in joined
    assert "loja de utilidades domésticas" in joined
    assert '-"magazine luiza"' in joined
    assert '-"casas bahia"' in joined
    assert '-"lojas cem"' in joined
    assert '-"pernambucanas"' in joined
    assert '-"marabraz"' in joined
    assert '-"farmacia"' in joined
    assert '-"drogaria"' in joined


def test_varejistas_medio_porte_filter_large_retail_bloqueia_gigantes():
    items = [
        {"nome": "Magazine Luiza - Centro", "segmentos": ["Loja de departamentos"]},
        {"nome": "Casas Bahia Filial 12", "segmentos": ["Loja de eletrodomésticos"]},
        {"nome": "Lojas Cem - Ribeirão", "segmentos": ["Loja de móveis e eletro"]},
        {"nome": "Pernambucanas Modas e Lar", "segmentos": ["Loja de departamentos"]},
        {"nome": "Marabraz Móveis", "segmentos": ["Loja de móveis"]},
        {"nome": "Assaí Atacadista", "segmentos": ["Atacadista"]},
        {"nome": "Supermercado Gricki Regional", "segmentos": ["Supermercado"]},
        {"nome": "Móveis e Eletro Santa Helena", "segmentos": ["Loja de móveis e eletro"]},
        {"nome": "Bazar e Utilidades Real", "segmentos": ["Loja de variedades"]},
    ]

    filtered = _filter_large_retail(items)
    names = [item["nome"] for item in filtered]

    assert "Magazine Luiza - Centro" not in names
    assert "Casas Bahia Filial 12" not in names
    assert "Lojas Cem - Ribeirão" not in names
    assert "Pernambucanas Modas e Lar" not in names
    assert "Marabraz Móveis" not in names
    assert "Assaí Atacadista" not in names
    assert "Supermercado Gricki Regional" in names
    assert "Móveis e Eletro Santa Helena" in names
    assert "Bazar e Utilidades Real" in names


def test_varejistas_medio_porte_filter_mantem_tier3_e_remove_ruido():
    items = [
        {
            "nome": "Supermercado Savegnago Filial 3",
            "segmentos": ["Supermercado"],
            "telefone": "(16) 3600-1000",
        },
        {
            "nome": "Eletromóveis Estrela do Interior",
            "segmentos": ["Loja de eletrodomésticos"],
            "telefone": "(16) 3600-2000",
        },
        {
            "nome": "Bazar e Utilidades da Praça",
            "segmentos": ["Loja de utilidades"],
            "telefone": "(16) 3600-3000",
        },
        {"nome": "Mercado Municipal de Mogi das Cruzes", "segmentos": ["Mercado"]},
        {"nome": "Moveis e Eletros USADOS S. FRA", "segmentos": ["Loja de móveis"]},
        {"nome": "Drogaria São Paulo", "segmentos": ["Farmácia"]},
        {"nome": "Auto Peças do Paulinho", "segmentos": ["Oficina mecânica"]},
        {"nome": "Clínica Odontológica Sorriso", "segmentos": ["Dentista"]},
        {"nome": "Restaurante e Churrascaria Boiadeiro", "segmentos": ["Restaurante"]},
        {"nome": "Marmitaria da Vovó", "segmentos": ["Lanchonete"]},
    ]

    filtered = _filter_segment_noise(items, "Varejistas de Médio Porte")
    names = [item["nome"] for item in filtered]

    assert "Supermercado Savegnago Filial 3" in names
    assert "Eletromóveis Estrela do Interior" in names
    assert "Bazar e Utilidades da Praça" in names
    assert "Mercado Municipal de Mogi das Cruzes" not in names
    assert "Moveis e Eletros USADOS S. FRA" not in names
    assert "Drogaria São Paulo" not in names
    assert "Auto Peças do Paulinho" not in names
    assert "Clínica Odontológica Sorriso" not in names
    assert "Restaurante e Churrascaria Boiadeiro" not in names
    assert "Marmitaria da Vovó" not in names

    # Fit score ranking: Supermercado (+80) > Eletromóveis (+50) > Bazar (+30)
    scores = [item["varejo_medio_fit_score"] for item in filtered]
    assert scores[0] >= scores[1] >= scores[2]
    assert filtered[0]["nome"] == "Supermercado Savegnago Filial 3"
