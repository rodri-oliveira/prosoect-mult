from application.maps.search_results import (
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_informatica_medio_porte_queries_priorizam_qualidade_b2b():
    result = generate_queries_for_segments(
        segmentos=["Informática (Médio Porte)"],
        cidade="Campinas",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("distribuidora de informática")
    assert "revenda de informática" in joined
    assert "atacado de informática" in joined
    assert "suprimentos de informática" in joined
    assert "empresa de informática" not in joined
    assert '-"assistencia tecnica"' in joined
    assert '-"software"' in joined
    assert '-"provedor"' in joined


def test_informatica_medio_porte_filter_mantem_b2b_e_remove_ruido():
    items = [
        {
            "nome": "Alpha Distribuidora de Informática",
            "segmentos": ["Computer store"],
            "telefone": "(19) 3210-1000",
            "website": "alpha.com.br",
        },
        {
            "nome": "Beta Informática Suprimentos",
            "segmentos": ["Loja de informática"],
            "telefone": "(19) 3201-2000",
        },
        {
            "nome": "Milenio Informática",
            "segmentos": ["Loja de informática"],
            "telefone": "(19) 3201-3000",
            "website": "milenio.com.br",
        },
        {"nome": "João da Silva Informática", "segmentos": ["Loja de informática"], "telefone": "(19) 3201-4000"},
        {"nome": "Help PC Assistência Técnica", "segmentos": ["Computer repair service"]},
        {"nome": "Soft House Sistemas", "segmentos": ["Software company"]},
        {"nome": "Fibra Net Provedor", "segmentos": ["Internet service provider"]},
        {"nome": "Loja Genérica", "segmentos": ["Store"], "query_sources": ["distribuidor de informática em Campinas"]},
    ]

    filtered = _filter_segment_noise(items, "Informática (Médio Porte)")
    names = [item["nome"] for item in filtered]

    assert "Alpha Distribuidora de Informática" in names
    assert "Beta Informática Suprimentos" in names
    assert "Milenio Informática" in names
    assert "João da Silva Informática" not in names
    assert "Help PC Assistência Técnica" not in names
    assert "Soft House Sistemas" not in names
    assert "Fibra Net Provedor" not in names
    assert "Loja Genérica" not in names
    assert filtered[0]["informatica_medio_fit_score"] >= filtered[-1]["informatica_medio_fit_score"]
