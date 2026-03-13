from __future__ import annotations

import sqlite3
from typing import Any

from database import DB_PATH
from domain.repositories.prospeccao_repository import ProspecctionSummary, ProspeccaoRepository


class SqliteProspeccaoRepository(ProspeccaoRepository):
    def get_by_id(self, prospeccao_id: int) -> dict | None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        row = c.fetchone()
        conn.close()
        return dict(row) if row else None

    def list_by_filters(
        self,
        status: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        mostrar_arquivados: bool = False,
    ) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        where_parts = []
        params: list[Any] = []

        if not mostrar_arquivados:
            where_parts.append("(arquivado = 0 OR arquivado IS NULL)")

        if status:
            where_parts.append("status_prospeccao = ?")
            params.append(status)

        if segmento:
            where_parts.append("segmento LIKE ?")
            params.append(f"%{segmento}%")

        if cidade:
            where_parts.append("cidade LIKE ?")
            params.append(f"%{cidade}%")

        if estado:
            where_parts.append("estado LIKE ?")
            params.append(f"%{estado}%")

        if data_inicio and data_fim:
            where_parts.append("date(data_prospeccao) BETWEEN date(?) AND date(?)")
            params.extend([data_inicio, data_fim])
        elif data_inicio:
            where_parts.append("date(data_prospeccao) >= date(?)")
            params.append(data_inicio)
        elif data_fim:
            where_parts.append("date(data_prospeccao) <= date(?)")
            params.append(data_fim)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        c.execute(
            f"SELECT * FROM prospeccao_temp WHERE {where_clause} ORDER BY id DESC",
            params,
        )
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_summary(self, data_inicio: str | None, data_fim: str | None, mostrar_arquivados: bool = False) -> ProspecctionSummary:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        where_parts = []
        params: list[Any] = []

        if not mostrar_arquivados:
            where_parts.append("(arquivado = 0 OR arquivado IS NULL)")

        if data_inicio and data_fim:
            where_parts.append("date(data_prospeccao) BETWEEN date(?) AND date(?)")
            params.extend([data_inicio, data_fim])
        elif data_inicio:
            where_parts.append("date(data_prospeccao) >= date(?)")
            params.append(data_inicio)
        elif data_fim:
            where_parts.append("date(data_prospeccao) <= date(?)")
            params.append(data_fim)

        where_clause = " AND ".join(where_parts) if where_parts else "1=1"

        c.execute(f"SELECT COUNT(*) FROM prospeccao_temp WHERE {where_clause}", params)
        total = c.fetchone()[0]

        c.execute(
            f"SELECT status_prospeccao, COUNT(*) FROM prospeccao_temp WHERE {where_clause} GROUP BY status_prospeccao",
            params,
        )
        por_status = {row[0]: row[1] for row in c.fetchall()}

        conn.close()
        return ProspecctionSummary(total=total, por_status=por_status)

    def add(self, dados: dict) -> tuple[int, bool]:
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
        site = (dados.get("site") or dados.get("website") or "").strip() or None

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
            update_parts: list[str] = []
            update_params: list = []

            def _add_update(col: str, val) -> None:
                if val is None:
                    return
                if isinstance(val, str) and not val.strip():
                    return
                update_parts.append(f"{col} = ?")
                update_params.append(val)

            _add_update("observacao", (obs or "").strip() or None)
            _add_update("status_prospeccao", (status or "").strip() or None)
            _add_update("data_retorno", data_retorno)
            _add_update("hora_retorno", hora_retorno)
            _add_update("cnpj", cnpj)
            _add_update("telefone", (dados.get("telefone") or "").strip() or None)
            _add_update("whatsapp", (dados.get("whatsapp") or "").strip() or None)
            _add_update("endereco", (dados.get("endereco") or "").strip() or None)
            _add_update("segmento", (dados.get("segmento") or "").strip() or None)
            _add_update("maps_place_id", maps_place_id)
            _add_update("maps_url", maps_url)
            _add_update("site", site)

            if update_parts:
                c.execute(
                    f"UPDATE prospeccao_temp SET {', '.join(update_parts)} WHERE id = ?",
                    tuple(update_params + [existente_id]),
                )
                conn.commit()
            conn.close()
            return existente_id, False

        c.execute(
            """
            INSERT INTO prospeccao_temp (nome_loja, cnpj, telefone, whatsapp, endereco, cidade, estado, segmento, status_prospeccao, observacao, data_retorno, data_primeiro_agendamento, tentativas_retorno, data_ultima_tentativa, hora_retorno, maps_place_id, maps_url, site)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                (dados.get("nome_loja") or "").strip(),
                cnpj,
                (dados.get("telefone") or "").strip() or None,
                (dados.get("whatsapp") or "").strip() or None,
                (dados.get("endereco") or "").strip() or None,
                (dados.get("cidade") or "").strip() or None,
                (dados.get("estado") or "").strip() or None,
                (dados.get("segmento") or "").strip() or None,
                status,
                (obs or "").strip() or None,
                data_retorno,
                dados.get("data_primeiro_agendamento"),
                dados.get("tentativas_retorno") or 0,
                dados.get("data_ultima_tentativa"),
                hora_retorno,
                maps_place_id,
                maps_url,
                site,
            ),
        )
        conn.commit()
        new_id = c.lastrowid
        conn.close()

        return new_id, True

    def update_status(
        self,
        prospeccao_id: int,
        novo_status: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        fields = ["status_prospeccao = ?"]
        params: list[Any] = [novo_status]

        if observacao is not None:
            fields.append("observacao = ?")
            params.append(observacao)

        if data_retorno:
            fields.append("data_retorno = ?")
            params.append(data_retorno)
            if hora_retorno:
                fields.append("hora_retorno = ?")
                params.append(hora_retorno)

        params.append(prospeccao_id)

        c.execute(
            f"UPDATE prospeccao_temp SET {', '.join(fields)} WHERE id = ?",
            params,
        )
        conn.commit()
        affected = c.rowcount

        # Registrar evento no histórico
        if affected > 0:
            detalhe = novo_status
            if observacao:
                detalhe = f"{novo_status} | {observacao}"
            c.execute(
                """
                INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
                VALUES (?, ?, ?)
            """,
                (prospeccao_id, "STATUS_CHANGE", detalhe),
            )
            conn.commit()

        conn.close()
        return affected > 0

    def arquivar(self, prospeccao_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE prospeccao_temp SET arquivado = 1 WHERE id = ?",
            (prospeccao_id,),
        )
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0

    def converter_para_lead(self, prospeccao_id: int) -> int | None:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute(
            "SELECT * FROM prospeccao_temp WHERE id = ? AND (arquivado = 0 OR arquivado IS NULL)",
            (prospeccao_id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return None

        col_names = [desc[0] for desc in c.description]
        prospeccao = dict(zip(col_names, row))

        if prospeccao.get("convertido_lead_id"):
            lead_id = prospeccao["convertido_lead_id"]
            conn.close()
            return lead_id

        nome = (prospeccao.get("nome_loja") or "").strip()
        cidade = (prospeccao.get("cidade") or "").strip()
        estado = (prospeccao.get("estado") or "").strip()
        cnpj = (prospeccao.get("cnpj") or "").strip()
        telefone = (prospeccao.get("telefone") or "").strip()
        whatsapp = (prospeccao.get("whatsapp") or "").strip()
        endereco = (prospeccao.get("endereco") or "").strip()
        segmento = (prospeccao.get("segmento") or "").strip()
        observacao = (prospeccao.get("observacao") or "").strip()
        maps_place_id = (prospeccao.get("maps_place_id") or "").strip()
        maps_url = (prospeccao.get("maps_url") or "").strip()
        site = (prospeccao.get("site") or "").strip()

        c.execute(
            """
            INSERT INTO leads (nome_loja, cidade, estado, cnpj, telefone, whatsapp, endereco, status, observacoes, maps_place_id, maps_url, site, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'))
        """,
            (
                nome,
                cidade or None,
                estado or None,
                cnpj or None,
                telefone or None,
                whatsapp or None,
                endereco or None,
                "Novo Lead",
                observacao or None,
                maps_place_id or None,
                maps_url or None,
                site or None,
            ),
        )
        conn.commit()
        lead_id = c.lastrowid

        c.execute(
            "UPDATE prospeccao_temp SET convertido_lead_id = ?, arquivado = 1 WHERE id = ?",
            (lead_id, prospeccao_id),
        )
        conn.commit()
        conn.close()
        return lead_id

    def delete(self, prospeccao_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0

    def get_total_retornos_hoje(self) -> int:
        from datetime import date

        hoje = date.today().isoformat()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao = 'Pediu para retornar'
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje,),
        )
        total = int(c.fetchone()[0])
        conn.close()
        return total

    def get_eventos(self, prospeccao_id: int) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            """
            SELECT * FROM prospeccao_eventos
            WHERE prospeccao_id = ?
            ORDER BY data_evento DESC
        """,
            (prospeccao_id,),
        )
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
