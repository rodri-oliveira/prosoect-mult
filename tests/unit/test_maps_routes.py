from interfaces.api.routes import _default_maps_estado


def test_default_maps_estado_assumes_sp_when_city_has_no_state():
    assert _default_maps_estado("Americana", "") == "SP"


def test_default_maps_estado_keeps_explicit_state_uppercase():
    assert _default_maps_estado("Niteroi", "rj") == "RJ"


def test_default_maps_estado_stays_empty_without_city():
    assert _default_maps_estado("", "") == ""
