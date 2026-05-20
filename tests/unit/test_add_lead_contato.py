from application.leads.add_contato import AddLeadContatoRequest, add_lead_contato_with_repo


class FakeLeadRepository:
    def __init__(self):
        self.contatos: list[dict] = []
        self.status_updates: list[dict] = []

    def get_by_id(self, lead_id: int):
        return ({"id": lead_id}, [], ["Moda"])

    def add_contato(
        self,
        lead_id: int,
        tipo_contato: str,
        resultado: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
    ) -> bool:
        self.contatos.append(
            {
                "lead_id": lead_id,
                "tipo_contato": tipo_contato,
                "resultado": resultado,
                "observacao": observacao,
                "data_retorno": data_retorno,
                "hora_retorno": hora_retorno,
            }
        )
        return True

    def update_status(self, lead_id: int, novo_status: str) -> bool:
        self.status_updates.append({"lead_id": lead_id, "novo_status": novo_status})
        return True


def test_agendar_retorno_continua_exigindo_data_e_hora():
    repo = FakeLeadRepository()

    result = add_lead_contato_with_repo(
        AddLeadContatoRequest(
            lead_id=1,
            tipo_contato="Ligação",
            resultado="Agendar retorno",
            observacao="Retornar depois",
            data_retorno=None,
            hora_retorno=None,
        ),
        repo,
    )

    assert result.ok is False
    assert repo.contatos == []


def test_em_negociacao_nao_exige_agendamento():
    repo = FakeLeadRepository()

    result = add_lead_contato_with_repo(
        AddLeadContatoRequest(
            lead_id=1,
            tipo_contato="Ligação",
            resultado="Em negociação",
            observacao="Cliente avaliando proposta",
            data_retorno=None,
            hora_retorno=None,
        ),
        repo,
    )

    assert result.ok is True
    assert len(repo.contatos) == 1
    assert repo.contatos[0]["resultado"] == "Em negociação"
