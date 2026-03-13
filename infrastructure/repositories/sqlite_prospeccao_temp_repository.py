from __future__ import annotations

import sqlite3

from database import DB_PATH
from domain.repositories.prospeccao_temp_repository import AddProspecctionTempResult, ProspecctionTempRepository


class SqliteProspecctionTempRepository(ProspecctionTempRepository):
    def add_from_maps_data(self, dados: dict) -> AddProspecctionTempResult:
        prospeccao_id, created = self._add_prospeccao_temp_info(dados)
        return AddProspecctionTempResult(prospeccao_id=int(prospeccao_id), created=bool(created))

    def _add_prospeccao_temp_info(self, dados: dict):
        def _norm_text(v: str) -> str:
            return " ".join((v or "").strip().lower().split())

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        obs = dados.get("observacoes")
        if obs is None:
            obs = dados.get("observacao", "")

        status = dados.get("status_prospeccao") if dados.get("status_prospeccao") else "Não contatado"
        if status == "Pediu portfólio":
            status = "Em negociação"

        data_retorno = dados.get("data_retorno") if status in ("Pediu para retornar", "Em negociação") else None
        hora_retorno = dados.get("hora_retorno") if data_retorno else None

        maps_place_id = (dados.get("maps_place_id") or "").strip() or None
        maps_url = (dados.get("maps_url") or "").strip() or None
        cnpj = (dados.get("cnpj") or "").strip() or None

        existente_id = None
        if maps_place_id:
            c.execute(
                """
                SELECT id FROM prospeccao_temp
                WHERE maps_place_id = ?
                  AND (arquivado = 0 OR arquivado IS NULL)
                ORDER BY id DESC
                LIMIT 1
            """,
                (maps_place_id,),
            )
            row = c.fetchone()
            existente_id = row[0] if row else None

        if not existente_id and cnpj:
            c.execute(
                """
                SELECT id FROM prospeccao_temp
                WHERE cnpj = ?
                  AND (arquivado = 0 OR arquivado IS NULL)
                ORDER BY id DESC
                LIMIT 1
            """,
                (cnpj,),
            )
            row = c.fetchone()
            existente_id = row[0] if row else None

        if not existente_id:
            nome_n = _norm_text(dados.get("nome_loja"))
            cidade_n = _norm_text(dados.get("cidade"))
            estado_n = _norm_text(dados.get("estado"))
            if nome_n and cidade_n and estado_n:
                c.execute(
                    """
                    SELECT id, nome_loja, cidade, estado
                    FROM prospeccao_temp
                    WHERE (arquivado = 0 OR arquivado IS NULL)
                    ORDER BY id DESC
                    LIMIT 200
                """
                )
                rows = c.fetchall() or []
                for r in rows:
                    if _norm_text(r[1]) == nome_n and _norm_text(r[2]) == cidade_n and _norm_text(r[3]) == estado_n:
                        existente_id = r[0]
                        break

        if existente_id:
            conn.close()
            return existente_id, False

        c.execute(
            """
            INSERT INTO prospeccao_temp (nome_loja, cnpj, telefone, whatsapp, endereco, cidade, estado, segmento, observacao, data_prospeccao, status_prospeccao, data_retorno, hora_retorno, maps_place_id, maps_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, DATE('now')), COALESCE(?, 'Não contatado'), ?, ?, ?, ?)
        """,
            (
                dados.get("nome_loja"),
                cnpj,
                dados.get("telefone"),
                dados.get("whatsapp"),
                dados.get("endereco"),
                dados.get("cidade"),
                dados.get("estado"),
                dados.get("segmento"),
                obs,
                dados.get("data_prospeccao"),
                status,
                data_retorno,
                hora_retorno,
                maps_place_id,
                maps_url,
            ),
        )
        conn.commit()
        new_id = c.lastrowid
        conn.close()

        return new_id, True
