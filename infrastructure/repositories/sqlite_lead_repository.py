from __future__ import annotations

import sqlite3
from typing import Any

from database import DB_PATH
from domain.repositories.lead_repository import LeadRepository


class SqliteLeadRepository(LeadRepository):
    def get_by_id(self, lead_id: int) -> tuple[dict, list[dict], list[str]] | None:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
        lead_row = c.fetchone()
        if not lead_row:
            conn.close()
            return None

        lead = dict(lead_row)

        c.execute(
            "SELECT * FROM contatos WHERE lead_id = ? ORDER BY data DESC",
            (lead_id,),
        )
        contatos = [dict(row) for row in c.fetchall()]

        c.execute(
            "SELECT segmento FROM segmentos_loja WHERE lead_id = ?",
            (lead_id,),
        )
        segmentos = [str(row["segmento"]).strip() for row in c.fetchall() if str(row["segmento"] or "").strip()]

        conn.close()
        return lead, contatos, segmentos

    def list_by_status(self, status: str | None = None) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if status:
            c.execute(
                """
                SELECT
                    l.*,
                    c2.tipo_contato as ultimo_tipo_contato,
                    c2.resultado as ultimo_resultado,
                    c2.observacao as ultimo_observacao,
                    c2.data as ultimo_contato_data
                FROM leads l
                LEFT JOIN contatos c2 ON c2.id = (
                    SELECT id FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                )
                WHERE l.status = ?
                  AND (c2.data_retorno IS NULL)
                ORDER BY l.id DESC
            """,
                (status,),
            )
        else:
            c.execute(
                """
                SELECT
                    l.*,
                    c2.tipo_contato as ultimo_tipo_contato,
                    c2.resultado as ultimo_resultado,
                    c2.observacao as ultimo_observacao,
                    c2.data as ultimo_contato_data,
                    c2.data_retorno as data_retorno
                FROM leads l
                LEFT JOIN contatos c2 ON c2.id = (
                    SELECT id FROM contatos
                    WHERE lead_id = l.id
                    ORDER BY data DESC
                    LIMIT 1
                )
                WHERE COALESCE(l.status, '') <> 'Sem interesse'
                  AND c2.data_retorno IS NULL
                ORDER BY l.id DESC
            """
            )

        leads = [dict(row) for row in c.fetchall()]
        conn.close()
        return leads

    def create(self, data: dict) -> int:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        status = (data.get("status") or "Novo Lead").strip() or "Novo Lead"

        c.execute(
            """
            INSERT INTO leads (
                nome_loja, cnpj, telefone, whatsapp, email, cidade, estado, endereco, responsavel, status, observacoes, maps_place_id, maps_url, site
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                (data.get("nome_loja") or "").strip(),
                (data.get("cnpj") or "").strip() or None,
                (data.get("telefone") or "").strip() or None,
                (data.get("whatsapp") or "").strip() or None,
                (data.get("email") or "").strip() or None,
                (data.get("cidade") or "").strip() or None,
                (data.get("estado") or "").strip() or None,
                (data.get("endereco") or "").strip() or None,
                (data.get("responsavel") or "").strip() or None,
                status,
                (data.get("observacoes") or data.get("observacao") or "").strip() or None,
                (data.get("maps_place_id") or "").strip() or None,
                (data.get("maps_url") or "").strip() or None,
                (data.get("site") or "").strip() or None,
            ),
        )
        conn.commit()
        lead_id = c.lastrowid

        segmentos = data.get("segmentos")
        if segmentos:
            if isinstance(segmentos, (list, tuple)):
                values = segmentos
            else:
                values = str(segmentos).split(",")
            cleaned = [str(s).strip() for s in values if str(s or "").strip()]
            for seg in cleaned:
                c.execute(
                    "INSERT INTO segmentos_loja (lead_id, segmento) VALUES (?, ?)",
                    (lead_id, seg),
                )
            conn.commit()

        conn.close()
        return lead_id

    def update_status(self, lead_id: int, novo_status: str) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "UPDATE leads SET status = ? WHERE id = ?",
            (novo_status, lead_id),
        )
        
        # Se for sem interesse, limpa as datas de retorno futuras para sair do agendamento
        if novo_status == "Sem interesse":
            c.execute(
                "UPDATE contatos SET data_retorno = NULL, hora_retorno = NULL WHERE lead_id = ?",
                (lead_id,),
            )
            
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0

    def add_contato(
        self,
        lead_id: int,
        tipo_contato: str,
        resultado: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            INSERT INTO contatos (lead_id, tipo_contato, resultado, observacao, data_retorno, hora_retorno)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (lead_id, tipo_contato, resultado, observacao, data_retorno, hora_retorno),
        )
        conn.commit()
        conn.close()
        return True

    def get_retornos_agendados(self, data: str, mostrar_todos: bool = False) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        if mostrar_todos:
            c.execute(
                """
                SELECT c2.*, l.nome_loja as lead_nome, l.cidade, l.estado, l.telefone, l.whatsapp
                FROM contatos c2
                JOIN leads l ON c2.lead_id = l.id
                WHERE c2.data_retorno IS NOT NULL
                ORDER BY c2.data_retorno, c2.hora_retorno
            """
            )
        else:
            c.execute(
                """
                SELECT c2.*, l.nome_loja as lead_nome, l.cidade, l.estado, l.telefone, l.whatsapp
                FROM contatos c2
                JOIN leads l ON c2.lead_id = l.id
                WHERE c2.data_retorno = ?
                ORDER BY c2.hora_retorno
            """,
                (data,),
            )

        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def get_retornos_atrasados(self, data_ref: str) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute(
            """
            SELECT c2.*, l.nome_loja as lead_nome, l.cidade, l.estado, l.telefone, l.whatsapp
            FROM contatos c2
            JOIN leads l ON c2.lead_id = l.id
            WHERE c2.data_retorno < ? AND c2.data_retorno IS NOT NULL
            ORDER BY c2.data_retorno, c2.hora_retorno
        """,
            (data_ref,),
        )

        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    def update(self, lead_id: int, data: dict) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        campos = []
        valores = []
        
        # Mapear campos permitidos para atualização
        mapping = {
            'nome_loja': 'nome_loja',
            'cnpj': 'cnpj',
            'telefone': 'telefone',
            'whatsapp': 'whatsapp',
            'email': 'email',
            'cidade': 'cidade',
            'estado': 'estado',
            'endereco': 'endereco',
            'responsavel': 'responsavel',
            'site': 'site',
            'observacoes': 'observacoes'
        }
        
        for key, col in mapping.items():
            if key in data:
                val = data[key]
                # Normalização simples se for string
                if isinstance(val, str):
                    val = val.strip() or None
                
                campos.append(f"{col} = ?")
                valores.append(val)
                
        if not campos:
            conn.close()
            return False
            
        valores.append(lead_id)
        sql = f"UPDATE leads SET {', '.join(campos)} WHERE id = ?"
        
        c.execute(sql, tuple(valores))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0

    def devolver_para_prospeccao(self, lead_id: int) -> bool:
        """Devolve lead para prospecção: desarquiva a prospecção original e atualiza status."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Buscar a prospecção original que gerou este lead
        c.execute(
            "SELECT id FROM prospeccao_temp WHERE convertido_lead_id = ?",
            (lead_id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return False

        prospeccao_id = row[0]

        # Desarquivar e atualizar status da prospecção
        c.execute(
            "UPDATE prospeccao_temp SET arquivado = 0, status_prospeccao = 'Sem interesse', convertido_lead_id = NULL WHERE id = ?",
            (prospeccao_id,),
        )

        # Registrar evento no histórico da prospecção
        c.execute(
            "INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe) VALUES (?, ?, ?)",
            (prospeccao_id, "STATUS_CHANGE", "Sem interesse | Devolvido de Lead"),
        )

        conn.commit()
        conn.close()
        return True

    def update_basic_info(
        self,
        lead_id: int,
        responsavel: str | None = None,
        email: str | None = None,
        telefone: str | None = None,
        whatsapp: str | None = None,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        updates = []
        params = []

        if responsavel is not None:
            updates.append("responsavel = ?")
            params.append(responsavel)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if telefone is not None:
            updates.append("telefone = ?")
            params.append(telefone)
        if whatsapp is not None:
            updates.append("whatsapp = ?")
            params.append(whatsapp)

        if not updates:
            conn.close()
            return False

        params.append(lead_id)
        query = f"UPDATE leads SET {', '.join(updates)} WHERE id = ?"
        c.execute(query, tuple(params))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
