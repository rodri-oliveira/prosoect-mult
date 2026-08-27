from application.maps.search_results import (
    _filter_segment_noise,
    generate_queries_for_segments,
)


def test_mobilidade_eletrica_queries_priorizam_revenda_e_ebikes():
    result = generate_queries_for_segments(
        segmentos=["Mobilidade Elétrica"],
        cidade="São Paulo",
        estado="SP",
    )

    queries = [spec["q"] for spec in result.queries]
    joined = " | ".join(queries).lower()

    assert result.ok is True
    assert result.primary_query.startswith("loja de Mobilidade Elétrica")
    assert "distribuidor de mobilidade elétrica" in joined
    assert "distribuidor de motos elétricas" in joined
    assert "revenda de bicicletas elétricas" in joined
    assert "loja de motos elétricas" in joined
    assert "concessionária de motos elétricas" in joined
    assert "loja de concessionária" not in joined  # Prefix ignore check
    assert "loja de ebike shop" not in joined       # Prefix ignore check
    assert "ebike shop" in joined
    assert "bicicletaria elétrica" in joined
    assert "watts mobilidade elétrica" in joined


def test_mobilidade_eletrica_filter_remove_eletropostos_e_oficinas_carros():
    items = [
        {
            "nome": "VoltEletro Distribuidora de Motos Elétricas",
            "segmentos": ["Loja de veículos elétricos"],
            "telefone": "(11) 3333-1000",
            "website": "volteletro.com.br",
        },
        {
            "nome": "E-Bike Mania Revenda e Concessionária",
            "segmentos": ["Loja de bicicletas elétricas"],
            "telefone": "(11) 3333-2000",
        },
        {
            "nome": "SP Scooters Elétricas",
            "segmentos": ["Loja de motocicletas"],
            "telefone": "(11) 3333-3000",
        },
        # Ruídos que devem ser removidos
        {"nome": "Eletroposto Shell Recharge", "segmentos": ["Estação de recarga de veículos elétricos"]},
        {"nome": "Bike Itaú Estação 42", "segmentos": ["Ponto de compartilhamento"]},
        {"nome": "Auto Center Silva Troca de Óleo", "segmentos": ["Oficina mecânica"]},
        {"nome": "Auto Elétrica Magoshi", "segmentos": ["Auto elétrica"]},
        {"nome": "Auto Elétrica Jóia de Adamanti", "segmentos": ["Oficina automotiva"]},
        {"nome": "Borracharia e Funilaria do Zé", "segmentos": ["Oficina automotiva"]},
        {"nome": "Ortopedia Central Cadeira de Rodas", "segmentos": ["Produtos ortopédicos"]},
        {"nome": "Padaria e Conveniência 24h", "segmentos": ["Conveniência"]},
    ]

    filtered = _filter_segment_noise(items, "Mobilidade Elétrica")
    names = [item["nome"] for item in filtered]

    # Distribuidora, concessionária e loja mantidas
    assert "VoltEletro Distribuidora de Motos Elétricas" in names
    assert "E-Bike Mania Revenda e Concessionária" in names
    assert "SP Scooters Elétricas" in names

    # Ruídos descartados
    assert "Eletroposto Shell Recharge" not in names
    assert "Bike Itaú Estação 42" not in names
    assert "Auto Center Silva Troca de Óleo" not in names
    assert "Auto Elétrica Magoshi" not in names
    assert "Auto Elétrica Jóia de Adamanti" not in names
    assert "Borracharia e Funilaria do Zé" not in names
    assert "Ortopedia Central Cadeira de Rodas" not in names
    assert "Padaria e Conveniência 24h" not in names

    # Distribuidora/Concessionária B2B deve ter Fit Score alto
    dist_score = next(it["mobilidade_fit_score"] for it in filtered if "VoltEletro" in it["nome"])
    store_score = next(it["mobilidade_fit_score"] for it in filtered if "SP Scooters" in it["nome"])
    assert dist_score >= store_score


def test_mobilidade_eletrica_filter_remove_bicicletarias_tradicionais():
    items = [
        {"nome": "ELETRIKUS MOBILIDADE ELÉTRICA", "segmentos": ["Loja de veículos elétricos"]},
        {"nome": "NXT ADAMANTINA", "segmentos": ["Loja de veículos elétricos"]},
        {"nome": "Bicicletaria & E-Bikes Volt", "segmentos": ["Bicicletaria elétrica"]},
        # Bicicletarias tradicionais a pedal sem sinal elétrico (devem ser descartadas)
        {"nome": "Casa das Bicicletas", "segmentos": ["Bicicletaria"]},
        {"nome": "Bicicletaria Ideal", "segmentos": ["Oficina de bicicletas"]},
        {"nome": "Conserto de Bicicleta do Zezinho", "segmentos": ["Bicicletaria"]},
    ]

    filtered = _filter_segment_noise(items, "Mobilidade Elétrica")
    names = [item["nome"] for item in filtered]

    assert "ELETRIKUS MOBILIDADE ELÉTRICA" in names
    assert "NXT ADAMANTINA" in names
    assert "Bicicletaria & E-Bikes Volt" in names

    assert "Casa das Bicicletas" not in names
    assert "Bicicletaria Ideal" not in names
    assert "Conserto de Bicicleta do Zezinho" not in names


def test_mobilidade_eletrica_accepts_maps_category_without_literal_eletrica():
    items = [
        {"nome": "Mobility Center", "segmentos": ["Motorcycle dealer"]},
        {"nome": "Eletronica Silva", "segmentos": ["Electronics store"]},
    ]

    filtered = _filter_segment_noise(items, "Mobilidade ElÃ©trica")
    names = [item["nome"] for item in filtered]

    assert "Mobility Center" in names
    assert "Eletronica Silva" not in names


def test_mobilidade_eletrica_remove_ruidos_vistos_em_logs():
    items = [
        {"nome": "VELOT AMERICANA - SP", "segmentos": ["Loja de motos eletricas"]},
        {"nome": "GTMax Energy - Energia Solar", "segmentos": ["Empresa de energia solar"]},
        {"nome": "Meta Materiais Eletricos e Hidraulica", "segmentos": ["Loja de materiais eletricos"]},
        {"nome": "Eletricista 24 Horas- Mogi das Cruzes", "segmentos": ["Eletricista"]},
        {"nome": "Rei Dos Vidros Americana", "segmentos": ["Vidracaria"]},
        {"nome": "Margutti Multimarcas Americana", "segmentos": ["Concessionaria"]},
    ]

    filtered = _filter_segment_noise(items, "Mobilidade Eletrica")
    names = [item["nome"] for item in filtered]

    assert "VELOT AMERICANA - SP" in names
    assert "GTMax Energy - Energia Solar" not in names
    assert "Meta Materiais Eletricos e Hidraulica" not in names
    assert "Eletricista 24 Horas- Mogi das Cruzes" not in names
    assert "Rei Dos Vidros Americana" not in names
    assert "Margutti Multimarcas Americana" not in names
