from __future__ import annotations

import sqlite3
from datetime import date

from database import DB_PATH
from domain.repositories.relatorio_repository import RelatorioRepository


class SqliteRelatorioRepository(RelatorioRepository):
    def get_resumo_hoje(self) -> dict:
        hoje = date.today().isoformat()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute("SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND tipo_contato = 'Ligação'", (hoje,))
        ligacoes = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND tipo_contato = 'WhatsApp'", (hoje,))
        whatsapp = c.fetchone()["qtd"]

        c.execute(
            "SELECT COUNT(*) as qtd FROM contatos WHERE date(data) = ? AND resultado NOT IN ('Sem contato', 'Não atendeu')",
            (hoje,),
        )
        efetivos = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM leads WHERE date(data_criacao) = ?", (hoje,))
        novos_leads = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM prospeccao_temp
            WHERE data_prospeccao = ?
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (hoje,),
        )
        novas_prospeccoes = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Interessado'")
        interessados = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Negociação'")
        negociacoes = c.fetchone()["qtd"]

        conn.close()

        return {
            "ligacoes": ligacoes,
            "whatsapp": whatsapp,
            "efetivos": efetivos,
            "novos_leads": novos_leads,
            "novas_prospeccoes": novas_prospeccoes,
            "interessados": interessados,
            "negociacoes": negociacoes,
        }

    def get_relatorio_completo(self, data_inicio: str | None = None, data_fim: str | None = None) -> dict:
        if not data_inicio:
            data_inicio = date.today().isoformat()
        if not data_fim:
            data_fim = data_inicio

        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM contatos
            WHERE date(data) BETWEEN ? AND ? AND tipo_contato = 'Ligação'
        """,
            (data_inicio, data_fim),
        )
        ligacoes = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM contatos
            WHERE date(data) BETWEEN ? AND ? AND tipo_contato = 'WhatsApp'
        """,
            (data_inicio, data_fim),
        )
        whatsapp = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM contatos
            WHERE date(data) BETWEEN ? AND ?
              AND resultado NOT IN ('Sem contato', 'Não atendeu', 'Pulado na fila')
        """,
            (data_inicio, data_fim),
        )
        efetivos = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM leads
            WHERE date(data_criacao) BETWEEN ? AND ?
        """,
            (data_inicio, data_fim),
        )
        novos_leads = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Interessado'")
        interessados = c.fetchone()["qtd"]

        c.execute("SELECT COUNT(*) as qtd FROM leads WHERE status = 'Negociação'")
        negociacoes = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
        """,
            (data_inicio, data_fim),
        )
        total_prospeccoes = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
              AND status_prospeccao != 'Não contatado'
        """,
            (data_inicio, data_fim),
        )
        tentativas_prospeccao = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT status_prospeccao, COUNT(*) as total
            FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
            GROUP BY status_prospeccao
        """,
            (data_inicio, data_fim),
        )
        status_prospeccao = c.fetchall()

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
              AND convertido_lead_id IS NOT NULL
        """,
            (data_inicio, data_fim),
        )
        convertidos = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
              AND status_prospeccao = 'Pediu para retornar'
              AND data_retorno IS NOT NULL
        """,
            (data_inicio, data_fim),
        )
        agendamentos = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT * FROM prospeccao_temp
            WHERE data_prospeccao BETWEEN ? AND ?
              AND (arquivado = 0 OR arquivado IS NULL)
            ORDER BY data_prospeccao DESC, data_criacao DESC
        """,
            (data_inicio, data_fim),
        )
        detalhes_prospeccao = c.fetchall()

        c.execute(
            """
            SELECT c.resultado, c.observacao, c.tipo_contato,
                   l.nome_loja, l.status as status_final, l.cidade, l.estado,
                   l.cnpj, date(c.data) as data,
                   (SELECT GROUP_CONCAT(segmento, ', ') FROM segmentos_loja WHERE lead_id = l.id) as segmentos
            FROM contatos c
            JOIN leads l ON c.lead_id = l.id
            WHERE date(c.data) BETWEEN ? AND ?
            ORDER BY c.data DESC
        """,
            (data_inicio, data_fim),
        )
        detalhes_leads = c.fetchall()

        c.execute(
            """
            SELECT e.tipo_evento, e.detalhe,
                   date(e.data_evento) as data,
                   strftime('%H:%M', e.data_evento) as hora,
                   e.data_retorno_antes, e.data_retorno_depois,
                   p.nome_loja, p.cidade, p.estado, p.telefone, p.hora_retorno,
                   p.segmento, p.cnpj
            FROM prospeccao_eventos e
            JOIN prospeccao_temp p ON p.id = e.prospeccao_id
            WHERE date(e.data_evento) BETWEEN ? AND ?
              AND e.tipo_evento IN ('RETORNO_TENTATIVA', 'RETORNO_REAGENDADO_AUTO', 'RETORNO_RESULTADO', 'STATUS_ATUALIZADO')
            ORDER BY e.data_evento DESC
        """,
            (data_inicio, data_fim),
        )
        detalhes_eventos_prospeccao = c.fetchall()

        c.execute(
            """
            SELECT COUNT(*) as qtd
            FROM prospeccao_eventos
            WHERE date(data_evento) BETWEEN ? AND ?
              AND tipo_evento = 'RETORNO_TENTATIVA'
        """,
            (data_inicio, data_fim),
        )
        tentativas_retorno_periodo = c.fetchone()["qtd"]

        c.execute(
            """
            SELECT COUNT(*) as qtd
            FROM prospeccao_eventos
            WHERE date(data_evento) BETWEEN ? AND ?
              AND tipo_evento = 'RETORNO_REAGENDADO_AUTO'
        """,
            (data_inicio, data_fim),
        )
        reagendados_auto_periodo = c.fetchone()["qtd"]

        conn.close()

        return {
            "periodo": {"inicio": data_inicio, "fim": data_fim},
            "ligacoes": ligacoes,
            "whatsapp": whatsapp,
            "efetivos": efetivos,
            "novos_leads": novos_leads,
            "interessados": interessados,
            "negociacoes": negociacoes,
            "total_prospeccoes": total_prospeccoes,
            "tentativas_prospeccao": tentativas_prospeccao,
            "convertidos": convertidos,
            "agendamentos": agendamentos,
            "tentativas_retorno_periodo": tentativas_retorno_periodo,
            "reagendados_auto_periodo": reagendados_auto_periodo,
            "status_prospeccao": status_prospeccao,
            "detalhes_prospeccao": detalhes_prospeccao,
            "detalhes_leads": detalhes_leads,
            "detalhes_eventos_prospeccao": detalhes_eventos_prospeccao,
        }

    def get_relatorio_prospeccao(self, data_inicio: str | None = None, data_fim: str | None = None) -> dict:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        where_clause = "1=1"
        params: list[str] = []

        if data_inicio:
            where_clause += " AND data_prospeccao >= ?"
            params.append(data_inicio)
        if data_fim:
            where_clause += " AND data_prospeccao <= ?"
            params.append(data_fim)

        c.execute(
            f"""
            SELECT * FROM prospeccao_temp
            WHERE {where_clause}
            ORDER BY data_prospeccao DESC, data_criacao DESC
        """,
            params,
        )
        items = c.fetchall()

        c.execute(
            f"""
            SELECT data_prospeccao, status_prospeccao, COUNT(*) as total
            FROM prospeccao_temp
            WHERE {where_clause}
            GROUP BY data_prospeccao, status_prospeccao
            ORDER BY data_prospeccao DESC
        """,
            params,
        )
        por_dia = c.fetchall()

        c.execute(
            f"""
            SELECT status_prospeccao, COUNT(*) as total
            FROM prospeccao_temp
            WHERE {where_clause}
            GROUP BY status_prospeccao
        """,
            params,
        )
        resumo = c.fetchall()

        c.execute(
            f"""
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE {where_clause} AND status_prospeccao != 'Não contatado'
        """,
            params,
        )
        total_tentativas = c.fetchone()[0]

        c.execute(
            f"""
            SELECT COUNT(*) FROM prospeccao_temp
            WHERE {where_clause} AND convertido_lead_id IS NOT NULL
        """,
            params,
        )
        total_convertidos = c.fetchone()[0]

        conn.close()

        return {
            "items": items,
            "por_dia": por_dia,
            "resumo": resumo,
            "total_geral": len(items),
            "total_tentativas": total_tentativas,
            "total_convertidos": total_convertidos,
            "periodo": {"inicio": data_inicio, "fim": data_fim},
        }
