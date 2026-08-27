from domain.repositories.maps_existing_keys_repository import ExistingMapsKeys
from application.maps.search_results import SearchMapsResultsRequest, search_maps_results_with_repo


class EmptyExistingKeysRepo:
    def get_existing_maps_keys(self):
        return ExistingMapsKeys(prospeccao_keys=set(), lead_keys=set(), key_status_map={})


def test_maps_failure_does_not_return_fake_example_results(monkeypatch):
    import services.maps_scrape_service as maps_scrape_service

    def fail_scrape(*args, **kwargs):
        raise RuntimeError("browser/network blocked")

    monkeypatch.setattr(maps_scrape_service, "scrape_maps_results", fail_scrape)

    res = search_maps_results_with_repo(
        SearchMapsResultsRequest(
            query='loja de Mobilidade Eletrica em "Americana", SP',
            cidade="Americana",
            estado="SP",
            segmentos=["Mobilidade Eletrica"],
            limit=200,
        ),
        EmptyExistingKeysRepo(),
    )

    assert res.ok is True
    assert res.modo == "mock"
    assert "browser/network blocked" in (res.message or "")
    assert res.items == []
    assert res.merged_before_dedupe == 0
    assert res.merged_after_dedupe == 0
