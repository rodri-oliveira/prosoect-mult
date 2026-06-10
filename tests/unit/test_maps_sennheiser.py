from application.maps.search_results import (
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_sennheiser_queries_buscam_cnpj_com_uso_profissional_de_audio():
    result = generate_queries_for_segments(
        segmentos=["Sennheiser"],
        cidade="Campinas",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("loja de audio profissional")
    assert "audio profissional" in joined
    assert "estudio de gravacao" in joined
    assert "podcast studio" in joined
    assert "integrador audiovisual" in joined
    assert "solucoes av" in joined
    assert "equipamentos para eventos" in joined
    assert "locacao de audio" in joined
    assert "emissora de radio" in joined
    assert "produtora audiovisual" in joined
    assert "sonorizacao para igrejas" in joined
    assert "integrador audio e video" in joined
    assert "casa de show" in joined
    assert "centro de convencoes" in joined
    assert "universidade auditorio" in joined
    assert '-"som automotivo"' in joined
    assert '-"home theater"' in joined
    assert '-"assistencia tecnica"' in joined


def test_sennheiser_filter_mantem_consumidor_final_cnpj_qualificado():
    items = [
        {
            "nome": "Alpha Studio Gravacao e Podcast",
            "segmentos": ["Estudio de gravacao"],
            "query_sources": ["estudio de podcast em Campinas"],
        },
        {"nome": "Radio Cidade FM", "segmentos": ["Emissora de radio"]},
        {
            "nome": "Igreja Central",
            "segmentos": ["Auditorio", "Sonorizacao"],
            "query_sources": ["som para igreja em Campinas"],
        },
        {"nome": "AV Corp Integrador Audio e Video", "segmentos": ["Videoconferencia corporativa"]},
        {
            "nome": "Speed Sound e Film",
            "segmentos": ["Sennheiser"],
            "query_sources": ["broadcast audio em Adamantina", "som para igreja em Adamantina"],
        },
        {
            "nome": "Dorigo Eventos",
            "segmentos": ["Casa de eventos"],
            "query_sources": ["casa de eventos em Adamantina"],
        },
        {
            "nome": "Recanto Maravilha Adamantina",
            "segmentos": ["Casa de eventos"],
            "query_sources": ["casa de eventos em Adamantina"],
        },
        {
            "nome": "Paulo Cesar Alaby",
            "segmentos": ["Sennheiser"],
            "query_sources": ["estudio de gravacao em Adamantina"],
        },
        {"nome": "Som Forte Automotivo", "segmentos": ["Som automotivo"]},
        {"nome": "Eletronica Sao Jose", "segmentos": ["Conserto de TV"], "__raw_text": "Conserto de TV"},
        {"nome": "Cinema House", "segmentos": ["Home theater residencial"]},
    ]

    filtered = _filter_segment_noise(items, "Sennheiser")
    names = [item["nome"] for item in filtered]

    assert "Alpha Studio Gravacao e Podcast" in names
    assert "Radio Cidade FM" in names
    assert "Igreja Central" in names
    assert "AV Corp Integrador Audio e Video" in names
    assert "AV Corp Integrador Audio e Video" in names
    assert "Dorigo Eventos" in names
    assert "Recanto Maravilha Adamantina" in names
    assert "Paulo Cesar Alaby" in names
    assert "Speed Sound e Film" not in names
    assert "Som Forte Automotivo" not in names
    assert "Eletronica Sao Jose" not in names
    assert "Cinema House" not in names
    assert filtered[0]["sennheiser_fit_score"] >= filtered[-1]["sennheiser_fit_score"]
    assert names.index("Alpha Studio Gravacao e Podcast") < names.index("Dorigo Eventos")
    assert names.index("Dorigo Eventos") < names.index("Recanto Maravilha Adamantina")
