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
        nome: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        telefone: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
        mostrar_arquivados: bool = False,
        tipo_telefone: str | None = None,
    ) -> list[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        where_parts = []
        params: list[Any] = []
        tel_digits = ""
        is_phone_search = False
        if telefone:
            tel_input = (telefone or "").strip()
            tel_digits = "".join(ch for ch in tel_input if ch.isdigit())
            # Remover codigo do pais se vier com +55
            if tel_digits.startswith("55") and len(tel_digits) > 11:
                tel_digits = tel_digits[2:]
            if tel_digits:
                is_phone_search = True
        if not mostrar_arquivados and not is_phone_search:
            where_parts.append("(arquivado = 0 OR arquivado IS NULL)")
        # Excluir agendamentos da lista de prospeccao (esses ficam em /agendamentos)
        if not is_phone_search:
            agendamento_statuses = ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Em negociacao', 'Não analisou ainda o material')
            if status not in agendamento_statuses:
                where_parts.append("(data_retorno IS NULL OR data_retorno = '')")
        if status:
            if "," in status:
                status_list = [s.strip() for s in status.split(",") if s.strip()]
                placeholders = ",".join(["?"] * len(status_list))
                where_parts.append(f"status_prospeccao IN ({placeholders})")
                params.extend(status_list)
            else:
                where_parts.append("status_prospeccao = ?")
                params.append(status)
        if nome:
            nome_raw = (nome or "").strip().lower()
            nome_nospace = nome_raw.replace(" ", "")
            where_parts.append("(lower(nome_loja) LIKE ? OR lower(replace(nome_loja, ' ', '')) LIKE ? OR lower(responsavel) LIKE ?)")
            params.append(f"%{nome_raw}%")
            params.append(f"%{nome_nospace}%")
            params.append(f"%{nome_raw}%")
        if segmento:
            where_parts.append("segmento LIKE ?")
            params.append(f"%{segmento}%")
        if cidade:
            where_parts.append("cidade LIKE ?")
            params.append(f"%{cidade}%")
        if estado:
            where_parts.append("estado LIKE ?")
            params.append(f"%{estado}%")
        if tel_digits:
            # Busca parcial por numeros, ignorando formatacao ((), -, espacos)
            tel_pattern = f"%{tel_digits}%"
            tel_sql = (
                "replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            )
            wa_sql = (
                "replace(replace(replace(replace(replace(whatsapp, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            )
            where_parts.append(f"({tel_sql} LIKE ? OR {wa_sql} LIKE ?)")
            params.append(tel_pattern)
            params.append(tel_pattern)
        # Filtro por tipo de telefone (Fixo/Celular)
        if tipo_telefone:
            tel_clean_sql = "replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            if tipo_telefone == 'Fixo':
                where_parts.append(f"substr({tel_clean_sql}, 3, 1) IN ('2', '3', '4', '5')")
            elif tipo_telefone == 'Celular':
                where_parts.append(f"substr({tel_clean_sql}, 3, 1) = '9'")
            elif tipo_telefone == 'Sem telefone':
                where_parts.append("(telefone IS NULL OR telefone = '')")
        if not is_phone_search:
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
        # Ordenacao: a ultima tabulacao/evento aparece sempre primeiro.
        tel_clean = "replace(replace(replace(replace(replace(p.telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
        order_by = f"""
            COALESCE(ev.ultimo_evento, p.updated_at, p.data_criacao) DESC,
            CASE 
                WHEN substr({tel_clean}, 3, 1) IN ('2', '3', '4', '5') THEN 1
                WHEN substr({tel_clean}, 3, 1) = '9' THEN 2
                ELSE 3
            END ASC,
            p.id DESC
        """
        query = f"""
            SELECT p.*
            FROM prospeccao_temp p
            LEFT JOIN (
                SELECT prospeccao_id, MAX(data_evento) AS ultimo_evento
                FROM prospeccao_eventos
                GROUP BY prospeccao_id
            ) ev ON ev.prospeccao_id = p.id
            WHERE {where_clause}
            ORDER BY {order_by}
        """
        
        c.execute(query, params)
        rows = c.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    def get_summary(
        self,
        data_inicio: str | None,
        data_fim: str | None,
        mostrar_arquivados: bool = False,
        status: str | None = None,
        nome: str | None = None,
        segmento: str | None = None,
        cidade: str | None = None,
        estado: str | None = None,
        telefone: str | None = None,
        tipo_telefone: str | None = None,
    ) -> ProspecctionSummary:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        where_parts = []
        params: list[Any] = []
        tel_digits = ""
        is_phone_search = False
        if telefone:
            tel_input = (telefone or "").strip()
            tel_digits = "".join(ch for ch in tel_input if ch.isdigit())
            # Remover codigo do pais se vier com +55
            if tel_digits.startswith("55") and len(tel_digits) > 11:
                tel_digits = tel_digits[2:]
            if tel_digits:
                is_phone_search = True
        if not mostrar_arquivados and not is_phone_search:
            where_parts.append("(arquivado = 0 OR arquivado IS NULL)")
        if status:
            if "," in status:
                status_list = [s.strip() for s in status.split(",") if s.strip()]
                placeholders = ",".join(["?"] * len(status_list))
                where_parts.append(f"status_prospeccao IN ({placeholders})")
                params.extend(status_list)
            else:
                where_parts.append("status_prospeccao = ?")
                params.append(status)
        if nome:
            nome_raw = (nome or "").strip().lower()
            nome_nospace = nome_raw.replace(" ", "")
            where_parts.append("(lower(nome_loja) LIKE ? OR lower(replace(nome_loja, ' ', '')) LIKE ? OR lower(responsavel) LIKE ?)")
            params.append(f"%{nome_raw}%")
            params.append(f"%{nome_nospace}%")
            params.append(f"%{nome_raw}%")
        if segmento:
            where_parts.append("segmento LIKE ?")
            params.append(f"%{segmento}%")
        if cidade:
            where_parts.append("cidade LIKE ?")
            params.append(f"%{cidade}%")
        if estado:
            where_parts.append("estado LIKE ?")
            params.append(f"%{estado}%")
        if tel_digits:
            # Busca parcial por numeros, ignorando formatacao ((), -, espacos)
            tel_pattern = f"%{tel_digits}%"
            tel_sql = (
                "replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            )
            wa_sql = (
                "replace(replace(replace(replace(replace(whatsapp, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            )
            where_parts.append(f"({tel_sql} LIKE ? OR {wa_sql} LIKE ?)")
            params.append(tel_pattern)
            params.append(tel_pattern)
        # Filtro por tipo de telefone (Fixo/Celular)
        if tipo_telefone:
            tel_clean_sql = "replace(replace(replace(replace(replace(telefone, '(', ''), ')', ''), '-', ''), ' ', ''), '+', '')"
            if tipo_telefone == 'Fixo':
                where_parts.append(f"substr({tel_clean_sql}, 3, 1) IN ('2', '3', '4', '5')")
            elif tipo_telefone == 'Celular':
                where_parts.append(f"substr({tel_clean_sql}, 3, 1) = '9'")
            elif tipo_telefone == 'Sem telefone':
                where_parts.append("(telefone IS NULL OR telefone = '')")
        if not is_phone_search:
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
        # Buscar cidades únicas acionadas no período
        c.execute(
            f"SELECT DISTINCT cidade FROM prospeccao_temp WHERE {where_clause} AND cidade IS NOT NULL AND cidade != '' ORDER BY cidade",
            params,
        )
        cidades = [row[0] for row in c.fetchall()]
        conn.close()
        return ProspecctionSummary(total=total, por_status=por_status, cidades=cidades)
    def add(self, dados: dict) -> tuple[int, bool]:
        import logging
        _logger = logging.getLogger(__name__)
        def _norm_text(v: str | None) -> str:
            return " ".join((v or "").strip().lower().split())
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        obs = dados.get("observacoes")
        if obs is None:
            obs = dados.get("observacao", "")
        status = dados.get("status_prospeccao") if dados.get("status_prospeccao") else "Não contatado"
        if status == "Pediu portfólio":
            status = "Em negociação"
        data_retorno = dados.get("data_retorno") if status in ("Pediu para retornar", "Agendamento", "Em negociação") else None
        hora_retorno = dados.get("hora_retorno") if data_retorno else None
        maps_place_id = (dados.get("maps_place_id") or "").strip() or None
        maps_url = (dados.get("maps_url") or "").strip() or None
        cnpj = (dados.get("cnpj") or "").strip() or None
        site = (dados.get("site") or dados.get("website") or "").strip() or None
        _logger.warning(
            "[DEDUP_DEBUG] add() chamado: nome=%s | cidade=%s | estado=%s | maps_place_id=%s | maps_url=%s | cnpj=%s",
            dados.get("nome_loja"), dados.get("cidade"), dados.get("estado"),
            maps_place_id, (maps_url or "")[:80], cnpj,
        )
        existente_id = None
        if maps_place_id:
            c.execute(
                """
                SELECT id, nome_loja, cidade FROM prospeccao_temp
                WHERE maps_place_id = ?
                  AND (arquivado = 0 OR arquivado IS NULL)
                ORDER BY id DESC
                LIMIT 1
            """,
                (maps_place_id,),
            )
            row = c.fetchone()
            if row:
                existente_id = row[0]
                _logger.warning(
                    "[DEDUP_DEBUG] >>> MATCH por maps_place_id! existente_id=%s | nome_existente=%s | cidade_existente=%s | maps_place_id=%s",
                    row[0], row[1], row[2], maps_place_id,
                )
        if not existente_id and cnpj:
            c.execute(
                """
                SELECT id, nome_loja, cidade FROM prospeccao_temp
                WHERE cnpj = ?
                  AND (arquivado = 0 OR arquivado IS NULL)
                ORDER BY id DESC
                LIMIT 1
            """,
                (cnpj,),
            )
            row = c.fetchone()
            if row:
                existente_id = row[0]
                _logger.warning(
                    "[DEDUP_DEBUG] >>> MATCH por CNPJ! existente_id=%s | nome_existente=%s | cidade_existente=%s | cnpj=%s",
                    row[0], row[1], row[2], cnpj,
                )
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
                        _logger.warning(
                            "[DEDUP_DEBUG] >>> MATCH por NOME+CIDADE+ESTADO! existente_id=%s | nome_existente=%s | cidade_existente=%s | nome_novo=%s | cidade_nova=%s",
                            r[0], r[1], r[2], dados.get("nome_loja"), dados.get("cidade"),
                        )
                        break
        if not existente_id:
            _logger.warning("[DEDUP_DEBUG] Nenhum match encontrado. Sera criado novo registro.")
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
            _add_update("responsavel", (dados.get("responsavel") or "").strip() or None)
            _add_update("email", (dados.get("email") or "").strip() or None)
            update_parts.append("updated_at = CURRENT_TIMESTAMP")
            if update_parts:
                c.execute(
                    f"UPDATE prospeccao_temp SET {', '.join(update_parts)} WHERE id = ?",
                    tuple(update_params + [existente_id]),
                )
                conn.commit()
                if status not in ("Não contatado", "NÃ£o contatado", "NĂŁo contatado", "Năo contatado"):
                    detalhe = status
                    if obs:
                        detalhe = f"{status} | {obs}"
                    c.execute(
                        """
                        INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
                        VALUES (?, ?, ?)
                    """,
                        (existente_id, "STATUS_CHANGE", detalhe),
                    )
                    conn.commit()
            conn.close()
            return existente_id, False

        c.execute(
            """
            INSERT INTO prospeccao_temp (nome_loja, cnpj, telefone, whatsapp, endereco, cidade, estado, segmento, status_prospeccao, observacao, data_retorno, data_primeiro_agendamento, tentativas_retorno, data_ultima_tentativa, hora_retorno, maps_place_id, maps_url, site, responsavel, email)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                (dados.get("nome_loja") or "").strip(), cnpj,
                (dados.get("telefone") or "").strip() or None,
                (dados.get("whatsapp") or "").strip() or None,
                (dados.get("endereco") or "").strip() or None,
                (dados.get("cidade") or "").strip() or None,
                (dados.get("estado") or "").strip() or None,
                (dados.get("segmento") or "").strip() or None,
                status, (obs or "").strip() or None, data_retorno, dados.get("data_primeiro_agendamento"),
                dados.get("tentativas_retorno") or 0, dados.get("data_ultima_tentativa"), hora_retorno,
                maps_place_id, maps_url, site, (dados.get("responsavel") or "").strip() or None,
                (dados.get("email") or "").strip() or None,
            ),
        )
        conn.commit()
        new_id = c.lastrowid
        if new_id is None:
            conn.close()
            raise RuntimeError("Erro ao obter o ID inserido.")
        if status != "Não contatado":
            detalhe = status
            if obs:
                detalhe = f"{status} | {obs}"
            c.execute(
                "INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe) VALUES (?, ?, ?)",
                (new_id, "STATUS_CHANGE", detalhe),
            )
            conn.commit()
        conn.close()
        return new_id, True

    def update_status(
        self,
        prospeccao_id: int,
        novo_status: str,
        observacao: str | None = None,
        data_retorno: str | None = None,
        hora_retorno: str | None = None,
        clear_retorno: bool = False,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        fields = ["status_prospeccao = ?", "data_prospeccao = CURRENT_DATE", "updated_at = CURRENT_TIMESTAMP"]
        params: list[Any] = [novo_status]
        if observacao is not None:
            fields.append("observacao = ?")
            params.append(observacao)
        if data_retorno:
            fields.extend(["data_retorno = ?", "hora_retorno = ?"])
            params.extend([data_retorno, hora_retorno])
        elif clear_retorno:
            fields.extend(["data_retorno = NULL", "hora_retorno = NULL"])
        params.append(prospeccao_id)
        c.execute(f"UPDATE prospeccao_temp SET {', '.join(fields)} WHERE id = ?", params)
        affected = c.rowcount
        if affected > 0:
            detalhe = novo_status if not observacao else f"{novo_status} | {observacao}"
            c.execute(
                "INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe) VALUES (?, ?, ?)",
                (prospeccao_id, "STATUS_CHANGE", detalhe),
            )
        conn.commit()
        conn.close()
        return affected > 0
    def agendar_retorno(
        self,
        prospeccao_id: int,
        data_retorno: str,
        hora_retorno: str | None = None,
        observacao: str | None = None,
    ) -> bool:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute(
            "SELECT data_retorno FROM prospeccao_temp WHERE id = ?",
            (prospeccao_id,),
        )
        atual = c.fetchone()
        if not atual:
            conn.close()
            return False
        updates = [
            "data_retorno = ?",
            "hora_retorno = ?",
            "data_prospeccao = CURRENT_DATE",
            "data_ultima_tentativa = CURRENT_DATE",
            "tentativas_retorno = COALESCE(tentativas_retorno, 0) + 1",
            "updated_at = CURRENT_TIMESTAMP",
        ]
        params: list[Any] = [data_retorno, hora_retorno]
        if not atual["data_retorno"]:
            updates.append("data_primeiro_agendamento = COALESCE(data_primeiro_agendamento, ?)")
            params.append(data_retorno)
        if observacao is not None:
            updates.append("observacao = ?")
            params.append((observacao or "").strip() or None)
        params.append(prospeccao_id)
        c.execute(
            f"UPDATE prospeccao_temp SET {', '.join(updates)} WHERE id = ?",
            params,
        )
        affected = c.rowcount
        if affected > 0:
            detalhe = "Agendamento"
            if observacao:
                detalhe = f"Agendamento | {observacao}"
            c.execute(
                """
                INSERT INTO prospeccao_eventos (
                    prospeccao_id, tipo_evento, detalhe, data_retorno_antes, data_retorno_depois
                )
                VALUES (?, 'RETORNO_AGENDADO', ?, ?, ?)
            """,
                (prospeccao_id, detalhe, atual["data_retorno"], data_retorno),
            )
            conn.commit()
        conn.close()
        return affected > 0
    def update_draft(
        self,
        prospeccao_id: int,
        observacao: str | None = None,
        telefone: str | None = None,
        whatsapp: str | None = None,
        responsavel: str | None = None,
        email: str | None = None,
    ) -> bool:
        """Atualiza campos do rascunho registrando histórico da observação se necessário."""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Buscar dados atuais para histórico e comparação
        # Atualizamos a data_prospeccao também ao editar rascunho (pois é uma interação/contato)
        c.execute(
            "SELECT observacao, telefone, whatsapp, responsavel, email FROM prospeccao_temp WHERE id = ?",
            (prospeccao_id,),
        )
        row = c.fetchone()
        if not row:
            conn.close()
            return False
            
        obs_atual = row[0]
        
        # Histórico de observação
        if obs_atual and obs_atual.strip() and observacao and observacao.strip() and obs_atual != observacao:
            c.execute(
                """
                INSERT INTO prospeccao_eventos (prospeccao_id, tipo_evento, detalhe)
                VALUES (?, 'OBSERVACAO_CHANGE', ?)
            """,
                (prospeccao_id, obs_atual),
            )
            conn.commit()
        updates = []
        params: list[Any] = []
        
        if observacao is not None:
            updates.append("observacao = ?")
            params.append((observacao or "").strip() or None)
            updates.append("data_prospeccao = CURRENT_DATE")
        
        if telefone is not None:
            from application.shared.phone_utils import normalize_phone
            updates.append("telefone = ?")
            params.append(normalize_phone(telefone))
            
        if whatsapp is not None:
            from application.shared.phone_utils import normalize_phone
            updates.append("whatsapp = ?")
            params.append(normalize_phone(whatsapp))
            
        if responsavel is not None:
            updates.append("responsavel = ?")
            params.append((responsavel or "").strip() or None)
            
        if email is not None:
            updates.append("email = ?")
            params.append((email or "").strip() or None)
            
        if not updates:
            conn.close()
            return False

        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(prospeccao_id)
        query = f"UPDATE prospeccao_temp SET {', '.join(updates)} WHERE id = ?"
        
        c.execute(query, tuple(params))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    def converter_para_lead(self, prospeccao_id: int) -> int | None:
        """Converte prospecção em lead. Retorna lead_id ou None."""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Buscar dados da prospecção
        c.execute("SELECT * FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        row = c.fetchone()
        if not row:
            conn.close()
            return None
        prospeccao = dict(row)
        # Se já foi convertido, apenas retornar o ID
        if prospeccao.get("convertido_lead_id"):
            lead_id = prospeccao["convertido_lead_id"]
            
            # Garantir que está arquivado
            if not prospeccao.get("arquivado"):
                c.execute("UPDATE prospeccao_temp SET arquivado = 1 WHERE id = ?", (prospeccao_id,))
                conn.commit()
                
            conn.close()
            return lead_id
        # Mapear dados para o novo lead
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
        responsavel = (prospeccao.get("responsavel") or "").strip()
        email = (prospeccao.get("email") or "").strip()
        # Inserir na tabela de leads
        c.execute(
            """
            INSERT INTO leads (nome_loja, cidade, estado, cnpj, telefone, whatsapp, endereco, status, observacoes, maps_place_id, maps_url, site, responsavel, email, data_criacao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, DATE('now'))
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
                responsavel or None,
                email or None,
            ),
        )
        conn.commit()
        lead_id = c.lastrowid
        # Inserir segmentos na tabela segmentos_loja
        if segmento and lead_id:
            segmentos_list = [s.strip() for s in segmento.split(",") if s.strip()]
            for seg in segmentos_list:
                c.execute(
                    "INSERT INTO segmentos_loja (lead_id, segmento) VALUES (?, ?)",
                    (lead_id, seg),
                )
            conn.commit()
        # Atualizar prospecção como convertida e arquivada
        c.execute(
            "UPDATE prospeccao_temp SET convertido_lead_id = ?, arquivado = 1 WHERE id = ?",
            (lead_id, prospeccao_id),
        )
        conn.commit()
        # Migrar histórico de eventos para a tabela contatos do lead
        c.execute("SELECT * FROM prospeccao_eventos WHERE prospeccao_id = ?", (prospeccao_id,))
        eventos = c.fetchall()
        for ev in eventos:
            detalhe = ev['detalhe'] or ""
            # Tentar separar resultado de observação se houver "|"
            if " | " in detalhe:
                res, obs = detalhe.split(" | ", 1)
            else:
                res, obs = detalhe, ""
                
            c.execute(
                """
                INSERT INTO contatos (lead_id, data, tipo_contato, resultado, observacao)
                VALUES (?, ?, ?, ?, ?)
            """,
                (lead_id, ev['data_evento'], "Prospecção", res, obs),
            )
        conn.commit()
        conn.close()
        return lead_id
    def arquivar(self, prospeccao_id: int) -> bool:
        """Arquiva uma prospecção (converte em lead se necessário)."""
        lead_id = self.converter_para_lead(prospeccao_id)
        return lead_id is not None
    def delete(self, prospeccao_id: int) -> bool:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("DELETE FROM prospeccao_temp WHERE id = ?", (prospeccao_id,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    def get_retornos_stats(self) -> dict:
        """Retorna estatísticas detalhadas de agendamentos: hoje, atrasados e urgentes."""
        from datetime import datetime, date, timedelta
        agora = datetime.now()
        hoje_date = date.today().isoformat()
        uma_hora_depois = (agora + timedelta(hours=1)).strftime("%H:%M")
        hora_atual = agora.strftime("%H:%M")
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # 1. Atrasados (Data anterior a hoje)
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno < ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje_date,),
        )
        atrasados = c.fetchone()[0]
        # 2. Hoje (Total para hoje)
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje_date,),
        )
        hoje = c.fetchone()[0]
        # 3. Urgentes (Hoje, e o horário já passou ou falta < 1h)
        # Nota: Se hora_retorno for nulo, consideramos urgente se for hoje
        c.execute(
            """
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE data_retorno = ?
              AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação', 'Aguard. Lista Prod.', 'Não analisou ainda o material')
              AND (arquivado = 0 OR arquivado IS NULL)
              AND (hora_retorno <= ? OR hora_retorno IS NULL)
        """,
            (hoje_date, uma_hora_depois),
        )
        urgentes = c.fetchone()[0]
        conn.close()
        
        return {
            "hoje": hoje,
            "atrasados": atrasados,
            "urgentes": urgentes,
            "total": hoje + atrasados
        }
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
