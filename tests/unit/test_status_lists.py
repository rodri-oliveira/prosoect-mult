from application.shared.status import STATUS_LEADS


def test_status_leads_contem_novas_etapas_comerciais():
    assert "Envio de documentação" in STATUS_LEADS
    assert "Em análise de documentação" in STATUS_LEADS
    assert "Envio de orçamento" in STATUS_LEADS
