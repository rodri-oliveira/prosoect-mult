from application.agendamentos.registrar_tentativa import (
    RegistrarTentativaRequest,
    registrar_tentativa_with_repo,
)


class FakeAgendamentosRepository:
    def __init__(self):
        self.resultados = []

    def rolar_agendamentos_pendentes(self, data_limite: str) -> int:
        return 0

    def get_view_data(self, data: str, mostrar_todos: bool = False):
        raise NotImplementedError

    def registrar_tentativa_retorno(self, prospeccao_id: int, observacao: str) -> bool:
        return True

    def registrar_resultado_retorno(
        self,
        prospeccao_id: int,
        resultado: str,
        observacao: str | None = None,
    ) -> bool:
        self.resultados.append(
            {
                "prospeccao_id": prospeccao_id,
                "resultado": resultado,
                "observacao": observacao,
            }
        )
        return True

    def update_segmento(self, prospeccao_id: int, segmento: str) -> bool:
        return True


class FakeProspeccaoRepository:
    def __init__(self):
        self.agendamentos = []

    def get_by_id(self, prospeccao_id: int) -> dict | None:
        return {"id": prospeccao_id, "segmento": "Papelaria"}

    def agendar_retorno(
        self,
        prospeccao_id: int,
        data_retorno: str,
        hora_retorno: str | None = None,
        observacao: str | None = None,
    ) -> bool:
        self.agendamentos.append(
            {
                "prospeccao_id": prospeccao_id,
                "data_retorno": data_retorno,
                "hora_retorno": hora_retorno,
                "observacao": observacao,
            }
        )
        return True

    def update_draft(self, **kwargs) -> bool:
        return True

    def update_status(self, *args, **kwargs) -> bool:
        return True

    def arquivar(self, prospeccao_id: int) -> bool:
        return True

    def converter_para_lead(self, prospeccao_id: int) -> int | None:
        return None


def test_agendar_retorno_nao_exige_observacao_para_reagendar():
    agendamentos_repo = FakeAgendamentosRepository()
    prospeccao_repo = FakeProspeccaoRepository()

    result = registrar_tentativa_with_repo(
        RegistrarTentativaRequest(
            prospeccao_id=122,
            resultado="Agendar retorno",
            observacao=None,
            data_retorno="2026-05-20",
            hora_retorno="15:00",
            segmento=None,
            pos_acao=None,
        ),
        agendamentos_repo,
        prospeccao_repo,
    )

    assert result.ok is True
    assert prospeccao_repo.agendamentos == [
        {
            "prospeccao_id": 122,
            "data_retorno": "2026-05-20",
            "hora_retorno": "15:00",
            "observacao": None,
        }
    ]
    assert agendamentos_repo.resultados[0]["resultado"] == "Agendar retorno"


def test_agendar_retorno_continua_exigindo_hora():
    agendamentos_repo = FakeAgendamentosRepository()
    prospeccao_repo = FakeProspeccaoRepository()

    result = registrar_tentativa_with_repo(
        RegistrarTentativaRequest(
            prospeccao_id=122,
            resultado="Agendar retorno",
            observacao=None,
            data_retorno="2026-05-20",
            hora_retorno=None,
            segmento=None,
            pos_acao=None,
        ),
        agendamentos_repo,
        prospeccao_repo,
    )

    assert result.ok is False
    assert prospeccao_repo.agendamentos == []
