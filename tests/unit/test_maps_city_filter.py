from application.maps.search_results import _filter_strict_city


def test_strict_city_rejects_other_city_and_state():
    items = [
        {"nome": "Loja A", "cidade": "Adamantina", "estado": "SP"},
        {"nome": "Loja B", "cidade": "Dracena", "estado": "SP"},
        {"nome": "Loja C", "cidade": "Adamantina", "estado": "MS"},
        {"nome": "Loja D", "cidade": "", "estado": "", "__raw_text": "Rua Central, Dracena - SP"},
    ]

    filtered = _filter_strict_city(items, cidade="Adamantina", estado="SP")

    assert [item["nome"] for item in filtered] == ["Loja A"]
