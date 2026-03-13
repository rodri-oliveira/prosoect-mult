from __future__ import annotations

import sqlite3
from typing import Any

from database import DB_PATH
from domain.repositories.agendamentos_repository import AgendamentosRepository, AgendamentosViewData


class SqliteAgendamentosRepository(AgendamentosRepository):
    def rolar_agendamentos_pendentes(self, data_limite: str) -> int:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            """
            UPDATE prospeccao_temp
            SET data_retorno = DATE('now')
            WHERE data_retorno < ?
              AND data_retorno IS NOT NULL
              AND (arquivado = 0 OR arquivado IS NULL)
              AND status_prospeccao IN ('Pediu para retornar', 'Em negociação')
        """,
            (data_limite,),
        )
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected

    def get_view_data(self, data: str, mostrar_todos: bool = False) -> AgendamentosViewData:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # Agendamentos de prospecções
        c.execute(
            """
            SELECT * FROM prospeccao_temp
            WHERE data_retorno = ?
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY hora_retorno
        """,
            (data,),
        )
        retornos_hoje = [dict(row) for row in c.fetchall()]

        c.execute(
            """
            SELECT * FROM prospeccao_temp
            WHERE data_retorno < ?
              AND data_retorno IS NOT NULL
              AND (arquivado = 0 OR arquivado IS NULL)
              AND status_prospeccao IN ('Pediu para retornar', 'Em negociação')
            ORDER BY data_retorno, hora_retorno
        """,
            (data,),
        )
        retornos_atrasados = [dict(row) for row in c.fetchall()]

        retornos_futuros = []
        if mostrar_todos:
            c.execute(
                """
                SELECT * FROM prospeccao_temp
                WHERE data_retorno > ?
                  AND data_retorno IS NOT NULL
                  AND (arquivado = 0 OR arquivado IS NULL)
                ORDER BY data_retorno, hora_retorno
            """,
                (data,),
            )
            retornos_futuros = [dict(row) for row in c.fetchall()]

        # Agendamentos de leads
        c.execute(
            """
            SELECT
                l.id as id,
                l.nome_loja,
                l.cidade,
                l.estado,
                l.telefone,
                l.whatsapp,
                c2.data_retorno,
                c2.hora_retorno,
                (
                    SELECT tipo_contato FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_tipo_contato,
                (
                    SELECT resultado FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_resultado,
                (
                    SELECT observacao FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_observacao
            FROM contatos c2
            JOIN leads l ON c2.lead_id = l.id
            WHERE c2.id = (
                SELECT id
                FROM contatos
                WHERE lead_id = l.id
                  AND data_retorno = ?
                ORDER BY data DESC, id DESC
                LIMIT 1
            )
            ORDER BY (c2.hora_retorno IS NULL) ASC, c2.hora_retorno ASC
        """,
            (data,),
        )
        retornos_leads_hoje = [dict(row) for row in c.fetchall()]

        c.execute(
            """
            SELECT
                l.id as id,
                l.nome_loja,
                l.cidade,
                l.estado,
                l.telefone,
                l.whatsapp,
                c2.data_retorno,
                c2.hora_retorno,
                (
                    SELECT tipo_contato FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_tipo_contato,
                (
                    SELECT resultado FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_resultado,
                (
                    SELECT observacao FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                ) as ultimo_observacao
            FROM contatos c2
            JOIN leads l ON c2.lead_id = l.id
            WHERE c2.id = (
                SELECT id
                FROM contatos
                WHERE lead_id = l.id
                  AND data_retorno < ?
                  AND data_retorno IS NOT NULL
                ORDER BY data_retorno ASC, (hora_retorno IS NULL) ASC, hora_retorno ASC, id DESC
                LIMIT 1
            )
            ORDER BY c2.data_retorno ASC, (c2.hora_retorno IS NULL) ASC, c2.hora_retorno ASC
        """,
            (data,),
        )
        retornos_leads_atrasados = [dict(row) for row in c.fetchall()]

        retornos_leads_futuros = []
        if mostrar_todos:
            c.execute(
                """
                SELECT
                    l.id as id,
                    l.nome_loja,
                    l.cidade,
                    l.estado,
                    l.telefone,
                    l.whatsapp,
                    c2.data_retorno,
                    c2.hora_retorno,
                    (
                        SELECT tipo_contato FROM contatos
                        WHERE lead_id = l.id
                        ORDER BY data DESC
                        LIMIT 1
                    ) as ultimo_tipo_contato,
                    (
                        SELECT resultado FROM contatos
                        WHERE lead_id = l.id
                        ORDER BY data DESC
                        LIMIT 1
                    ) as ultimo_resultado,
                    (
                        SELECT observacao FROM contatos
                        WHERE lead_id = l.id
                        ORDER BY data DESC
                        LIMIT 1
                    ) as ultimo_observacao
                FROM contatos c2
                JOIN leads l ON c2.lead_id = l.id
                WHERE c2.id = (
                    SELECT id
                    FROM contatos
                    WHERE lead_id = l.id
                      AND data_retorno > ?
                    ORDER BY data_retorno ASC, (hora_retorno IS NULL) ASC, hora_retorno ASC, id DESC
                    LIMIT 1
                )
                ORDER BY c2.data_retorno ASC, (c2.hora_retorno IS NULL) ASC, c2.hora_retorno ASC
            """,
                (data,),
            )
            retornos_leads_futuros = [dict(row) for row in c.fetchall()]

        conn.close()

        total_futuros = len([r for r in retornos_futuros if r.get("data_retorno") != data])
        total_leads_futuros = len([r for r in retornos_leads_futuros if r.get("data_retorno") != data])

        return AgendamentosViewData(
            retornos_hoje=retornos_hoje,
            retornos_atrasados=retornos_atrasados,
            retornos_futuros=retornos_futuros if mostrar_todos else [],
            retornos_leads_hoje=retornos_leads_hoje,
            retornos_leads_atrasados=retornos_leads_atrasados,
            retornos_leads_futuros=retornos_leads_futuros,
            total_hoje=len(retornos_hoje),
            total_atrasados=len(retornos_atrasados),
            total_futuros=total_futuros,
            total_leads_hoje=len(retornos_leads_hoje),
            total_leads_atrasados=len(retornos_leads_atrasados),
            total_leads_futuros=total_leads_futuros,
            hoje=data,
        )

    def registrar_tentativa_retorno(self, prospeccao_id: int, observacao: str) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
            VALUES (?, 'RETORNO_TENTATIVA', ?)
        """,
            (prospeccao_id, observacao),
        )
        conn.commit()
        conn.close()
        return True

    def registrar_resultado_retorno(
        self,
        prospeccao_id: int,
        resultado: str,
        observacao: str | None = None,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
            VALUES (?, 'RETORNO_RESULTADO', ?)
        """,
            (prospeccao_id, f"{resultado}{' | ' + observacao if observacao else ''}"),
        )
        conn.commit()
        conn.close()
        return True

    def update_segmento(self, prospeccao_id: int, segmento: str) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE prospeccao_temp SET segmento = ? WHERE id = ?",
            (segmento, prospeccao_id),
        )
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
