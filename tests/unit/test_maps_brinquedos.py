from application.maps.search_results import (
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_brinquedos_queries_priorizam_b2b_e_revenda():
    result = generate_queries_for_segments(
        segmentos=["Brinquedos"],
        cidade="Campinas",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("loja de Brinquedos")
    assert "distribuidor de brinquedos" in joined
    assert "atacadista de brinquedos" in joined
    assert "revenda de brinquedos" in joined
    assert "papelaria e brinquedos" in joined
    assert '-"buffet"' in joined
    assert '-"locacao"' in joined
    assert '-"escola"' in joined


def test_brinquedos_filter_remove_servicos_infantis_e_mantem_revenda():
    items = [
        {"nome": "ABC Distribuidor de Brinquedos", "segmentos": ["Toy store"]},
        {"nome": "Papelaria Mundo Kids", "segmentos": ["Papelaria", "Brinquedos educativos"]},
        {"nome": "Bazar Presentes Avenida", "segmentos": ["Loja de variedades"]},
        {"nome": "Alegria Buffet Infantil", "segmentos": ["Buffet infantil"]},
        {"nome": "Playground Mania", "segmentos": ["Parque infantil"]},
        {"nome": "Moda Infantil Bella", "segmentos": ["Roupa infantil"]},
        {"nome": "Loja Generica", "segmentos": ["Store"]},
    ]

    filtered = _filter_segment_noise(items, "Brinquedos")
    names = [item["nome"] for item in filtered]

    assert "ABC Distribuidor de Brinquedos" in names
    assert "Papelaria Mundo Kids" in names
    assert "Bazar Presentes Avenida" not in names
    assert "Alegria Buffet Infantil" not in names
    assert "Playground Mania" not in names
    assert "Moda Infantil Bella" not in names
    assert "Loja Generica" not in names
