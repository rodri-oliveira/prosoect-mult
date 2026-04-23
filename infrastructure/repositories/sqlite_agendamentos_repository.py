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
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
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
            AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
            ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                hora_retorno
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
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
            ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                data_retorno, 
                hora_retorno
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
                  AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
                ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                data_retorno, hora_retorno
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
                l.responsavel,
                l.maps_url,
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
                  AND data_retorno IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
            )
              AND c2.data_retorno = ?
            ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                (c2.hora_retorno IS NULL) ASC, 
                c2.hora_retorno ASC
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
                l.responsavel,
                l.maps_url,
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
                  AND data_retorno IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
            )
              AND c2.data_retorno < ?
            ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                c2.data_retorno ASC, 
                (c2.hora_retorno IS NULL) ASC, 
                c2.hora_retorno ASC
        """,
            (data,),
        )
        retornos_leads_atrasados = [dict(row) for row in c.fetchall()]

        retornos_futuros = []
        retornos_leads_futuros = []

        if mostrar_todos:
            # Carregar listas completas apenas se necessário
            c.execute(
                """
                SELECT * FROM prospeccao_temp
                WHERE data_retorno > ?
                  AND (arquivado = 0 OR arquivado IS NULL)
                  AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
                ORDER BY 
                CASE 
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                    WHEN substr(replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                    ELSE 3
                END ASC,
                data_retorno, hora_retorno
            """,
                (data,),
            )
            retornos_futuros = [dict(row) for row in c.fetchall()]

            c.execute(
                """
                SELECT
                    l.id as id,
                    l.nome_loja,
                    l.cidade,
                    l.estado,
                    l.telefone,
                    l.whatsapp,
                    l.responsavel,
                    l.maps_url,
                    c2.data_retorno,
                    c2.hora_retorno,
                    (SELECT tipo_contato FROM contatos WHERE lead_id = l.id ORDER BY data DESC LIMIT 1) as ultimo_tipo_contato,
                    (SELECT resultado FROM contatos WHERE lead_id = l.id ORDER BY data DESC LIMIT 1) as ultimo_resultado,
                    (SELECT observacao FROM contatos WHERE lead_id = l.id ORDER BY data DESC LIMIT 1) as ultimo_observacao
                FROM contatos c2
                JOIN leads l ON c2.lead_id = l.id
                WHERE c2.id = (
                    SELECT id FROM contatos
                    WHERE lead_id = l.id
                      AND data_retorno IS NOT NULL
                    ORDER BY id DESC
                    LIMIT 1
                )
                  AND c2.data_retorno > ?
                ORDER BY 
                    CASE 
                        WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) IN ('2', '3', '4', '5') THEN 1
                        WHEN substr(replace(replace(replace(replace(replace(l.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', ''), 3, 1) = '9' THEN 2
                        ELSE 3
                    END ASC,
                    c2.data_retorno ASC, 
                    (c2.hora_retorno IS NULL) ASC, 
                    c2.hora_retorno ASC
            """,
                (data,),
            )
            retornos_leads_futuros = [dict(row) for row in c.fetchall()]

        # Totais Reais (Independente de mostrar_todos) - Sempre atualizados
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno > ?
              AND (arquivado = 0 OR arquivado IS NULL)
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
        """,
            (data,),
        )
        total_futuros = int(c.fetchone()[0])

        c.execute(
            """
            SELECT COUNT(*)
            FROM contatos c2
            JOIN leads l ON c2.lead_id = l.id
            WHERE c2.id = (
                SELECT id
                FROM contatos
                WHERE lead_id = l.id
                  AND data_retorno IS NOT NULL
                ORDER BY id DESC
                LIMIT 1
            )
              AND c2.data_retorno > ?
        """,
            (data,),
        )
        total_leads_futuros = int(c.fetchone()[0])

        conn.close()

        return AgendamentosViewData(
            retornos_hoje=retornos_hoje,
            retornos_atrasados=retornos_atrasados,
            retornos_futuros=retornos_futuros,
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
