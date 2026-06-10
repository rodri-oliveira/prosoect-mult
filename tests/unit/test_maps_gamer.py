from application.maps.search_results import (
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_gamer_queries_priorizam_b2b_e_revenda():
    result = generate_queries_for_segments(
        segmentos=["Gamer"],
        cidade="Campinas",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("loja de Gamer")
    assert "distribuidor gamer" in joined
    assert "atacadista gamer" in joined
    assert "revenda gamer" in joined
    assert "loja gamer" in joined
    assert "acessórios gamer" in joined
    assert "loja de pc gamer" in joined
    assert '-"lan house"' in joined
    assert '-"cyber cafe"' in joined
    assert '-"arena e-sports"' in joined
    assert '-"fliperama"' in joined


def test_gamer_filter_remove_consumo_final_e_mantem_revenda():
    items = [
        {"nome": "TechGamer Distribuidora de Periféricos", "segmentos": ["Loja de informática"]},
        {"nome": "Mundo Gamer Revenda e Assistência", "segmentos": ["Loja de eletrônicos"]},
        {"nome": "Cyber Star Lan House", "segmentos": ["Lan house"]},
        {"nome": "Nexus Arena E-Sports", "segmentos": ["Arena de e-sports"]},
        {"nome": "Fliperama Anos 90", "segmentos": ["Salão de jogos"]},
        {"nome": "Cassino Palace", "segmentos": ["Clube de jogos"]},
        {"nome": "Loja Generica", "segmentos": ["Store"]},
    ]

    filtered = _filter_segment_noise(items, "Gamer")
    names = [item["nome"] for item in filtered]

    assert "TechGamer Distribuidora de Periféricos" in names
    assert "Mundo Gamer Revenda e Assistência" in names
    assert "Cyber Star Lan House" not in names
    assert "Nexus Arena E-Sports" not in names
    assert "Fliperama Anos 90" not in names
    assert "Cassino Palace" not in names
