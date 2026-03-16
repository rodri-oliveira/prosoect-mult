"""
Módulo de geração de PDFs de relatórios.
Responsável por gerar PDFs usando ReportLab.
"""
from __future__ import annotations

import os
from datetime import datetime
from io import BytesIO


def _row_get(row, key: str, default: str = ""):
    if row is None:
        return default
    try:
        val = row[key]
    except Exception:
        return default
    return default if val is None else val


def _fmt_cnpj(val: str) -> str:
    s = '' if val is None else str(val)
    digits = ''.join(ch for ch in s if ch.isdigit())
    if len(digits) != 14:
        return s
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def build_relatorio_pdf_bytes(relatorio: dict, data_inicio: str, data_fim: str) -> bytes:
    """Gera PDF do relatório completo de produtividade."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.0 * cm,
        title="Relatório de Produtividade",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6,
        spaceBefore=10,
    )

    cell_style = ParagraphStyle(
        'Cell',
        parent=styles['Normal'],
        fontSize=7,
        leading=9,
        wordWrap='CJK',
    )

    def _p(val: str):
        v = '' if val is None else str(val)
        return Paragraph(v.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), cell_style)

    elements = []

    elements.append(Paragraph("RELATÓRIO DE PRODUTIVIDADE", title_style))
    elements.append(Paragraph(f"Período: {data_inicio} a {data_fim}", subtitle_style))

    # Métricas Prospecção
    elements.append(Paragraph("Prospecção", section_style))
    prosp_metrics = [
        'Total',
        'Tentativas',
        'Convertidos',
        'Agendados',
        'Tent. Retorno',
        'Reagend. Auto',
    ]
    prosp_values = [
        str(relatorio.get('total_prospeccoes', 0)),
        str(relatorio.get('tentativas_prospeccao', 0)),
        str(relatorio.get('convertidos', 0)),
        str(relatorio.get('agendamentos', 0)),
        str(relatorio.get('tentativas_retorno_periodo', 0)),
        str(relatorio.get('reagendados_auto_periodo', 0)),
    ]
    resumo_data = [prosp_metrics, prosp_values]

    resumo_table = Table(resumo_data, colWidths=[2.5 * cm] * 6)
    resumo_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dbeafe')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#93c5fd')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TOPPADDING', (0, 1), (-1, 1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ]
        )
    )
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.3 * cm))

    # Métricas CRM
    elements.append(Paragraph("CRM (Leads)", section_style))
    crm_metrics = [
        'Ligações',
        'WhatsApp',
        'Efetivos',
        'Interessados',
        'Negócios',
        'Novos Leads',
    ]
    crm_values = [
        str(relatorio.get('ligacoes', 0)),
        str(relatorio.get('whatsapp', 0)),
        str(relatorio.get('efetivos', 0)),
        str(relatorio.get('interessados', 0)),
        str(relatorio.get('negociacoes', 0)),
        str(relatorio.get('novos_leads', 0)),
    ]
    crm_data = [crm_metrics, crm_values]

    crm_table = Table(crm_data, colWidths=[2.5 * cm] * 6)
    crm_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#dcfce7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#166534')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#86efac')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TOPPADDING', (0, 1), (-1, 1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ]
        )
    )
    elements.append(crm_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Prospecção (detalhes objetivos)
    detalhes_prosp = relatorio.get('detalhes_prospeccao') or []
    elements.append(Paragraph(f"Prospecção - Detalhes ({len(detalhes_prosp)})", section_style))

    prosp_data = [["Loja", "CNPJ", "Cidade/UF", "Segmento", "Status", "Retorno", "Observação"]]
    for item in detalhes_prosp:
        retorno = str(_row_get(item, 'data_retorno', ''))
        hora_retorno = str(_row_get(item, 'hora_retorno', ''))
        if retorno and hora_retorno:
            retorno_str = f"{retorno} {hora_retorno}"
        elif retorno:
            retorno_str = retorno
        else:
            retorno_str = '-'
        
        observacao = str(_row_get(item, 'observacao', '')) or '-'

        cidade = str(_row_get(item, 'cidade', ''))
        uf = str(_row_get(item, 'estado', ''))
        cidade_uf = cidade
        if uf:
            cidade_uf = f"{cidade}/{uf}" if cidade else uf
        prosp_data.append(
            [
                _p(_row_get(item, 'nome_loja', '')),
                _p(_fmt_cnpj(_row_get(item, 'cnpj', ''))),
                _p(cidade_uf),
                _p(_row_get(item, 'segmento', '')),
                _p(_row_get(item, 'status_prospeccao', '')),
                _p(retorno_str),
                _p(observacao),
            ]
        )

    prosp_table = Table(
        prosp_data,
        colWidths=[
            4.5 * cm,  # Loja
            2.8 * cm,  # CNPJ
            2.2 * cm,  # Cidade/UF
            2.2 * cm,  # Segmento
            2.5 * cm,  # Status
            2.5 * cm,  # Retorno
            3.0 * cm,  # Observação
        ],
        repeatRows=1,
    )
    prosp_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(prosp_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Leads (detalhes objetivos)
    detalhes_leads = relatorio.get('detalhes_leads') or []
    elements.append(Paragraph(f"Leads - Ações Registradas ({len(detalhes_leads)})", section_style))

    leads_data = [["Loja", "CNPJ", "Cidade/UF", "Segmento", "Status", "Última Ação", "Observação"]]
    for item in detalhes_leads:
        cidade = str(_row_get(item, 'cidade', ''))
        uf = str(_row_get(item, 'estado', ''))
        cidade_uf = cidade
        if uf:
            cidade_uf = f"{cidade}/{uf}" if cidade else uf
        observacao_lead = str(_row_get(item, 'observacao', '')) or '-'
        leads_data.append(
            [
                _p(_row_get(item, 'nome_loja', '')),
                _p(_fmt_cnpj(_row_get(item, 'cnpj', ''))),
                _p(cidade_uf),
                _p(_row_get(item, 'segmentos', '')),
                _p(_row_get(item, 'status_final', '')),
                _p(_row_get(item, 'resultado', '')),
                _p(observacao_lead),
            ]
        )

    leads_table = Table(
        leads_data,
        colWidths=[
            4.0 * cm,  # Loja
            2.5 * cm,  # CNPJ
            2.0 * cm,  # Cidade/UF
            2.0 * cm,  # Segmento
            2.5 * cm,  # Status
            2.5 * cm,  # Última Ação
            3.0 * cm,  # Observação
        ],
        repeatRows=1,
    )
    leads_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#059669')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0fdf4')]),
            ]
        )
    )
    elements.append(leads_table)

    # Eventos de Prospecção (retornos/tentativas/resultados/reagendados)
    detalhes_eventos = relatorio.get('detalhes_eventos_prospeccao') or []
    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(f"Prospecção - Eventos ({len(detalhes_eventos)})", section_style))

    eventos_data = [["Data", "Hora", "Loja", "CNPJ", "Cidade/UF", "Segmento", "Evento", "Resultado"]]

    def _evento_label(tipo: str) -> str:
        if not tipo:
            return ''
        m = {
            'RETORNO_TENTATIVA': 'Tentativa',
            'RETORNO_REAGENDADO_AUTO': 'Reagendado automático',
            'RETORNO_RESULTADO': 'Resultado',
            'STATUS_ATUALIZADO': 'Status atualizado',
        }
        return m.get(tipo, tipo)

    for ev in detalhes_eventos:
        cidade = str(_row_get(ev, 'cidade', ''))
        uf = str(_row_get(ev, 'estado', ''))
        cidade_uf = cidade
        if uf:
            cidade_uf = f"{cidade}/{uf}" if cidade else uf

        evento = _evento_label(str(_row_get(ev, 'tipo_evento', '')))
        eventos_data.append(
            [
                str(_row_get(ev, 'data', '')),
                str(_row_get(ev, 'hora', '')),
                _p(_row_get(ev, 'nome_loja', '')),
                _p(_fmt_cnpj(_row_get(ev, 'cnpj', ''))),
                _p(cidade_uf),
                _p(_row_get(ev, 'segmento', '')),
                _p(evento),
                _p(_row_get(ev, 'detalhe', '')),
            ]
        )

    eventos_table = Table(
        eventos_data,
        colWidths=[
            1.4 * cm,  # Data
            1.0 * cm,  # Hora
            3.5 * cm,  # Loja
            2.5 * cm,  # CNPJ
            2.3 * cm,  # Cidade/UF
            2.2 * cm,  # Segmento
            2.5 * cm,  # Evento
            3.6 * cm,  # Resultado
        ],
        repeatRows=1,
    )
    eventos_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#7c3aed')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 0), (-1, -1), 'CJK'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#faf5ff')]),
            ]
        )
    )
    elements.append(eventos_table)

    doc.build(elements)

    buffer.seek(0)
    return buffer.read()


def build_relatorio_prospeccao_pdf_bytes(relatorio: dict, data_inicio: str, data_fim: str) -> bytes:
    """Gera PDF do relatório de prospecção."""
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.0 * cm,
        title="Análise de Prospecção",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10,
    )
    subtitle_style = ParagraphStyle(
        'Subtitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.gray,
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        'Section',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.HexColor('#111827'),
        spaceAfter=6,
        spaceBefore=10,
    )

    elements = []
    elements.append(Paragraph("ANÁLISE DE PROSPECÇÃO", title_style))
    elements.append(Paragraph(f"Período: {data_inicio} a {data_fim}", subtitle_style))

    total_geral = int(relatorio.get('total_geral', 0) or 0)
    total_tentativas = int(relatorio.get('total_tentativas', 0) or 0)
    total_convertidos = int(relatorio.get('total_convertidos', 0) or 0)
    taxa = 0.0
    if total_tentativas > 0:
        taxa = (total_convertidos / total_tentativas) * 100.0

    elements.append(Paragraph("Resumo", section_style))
    resumo_data = [
        ["Total", "Tentativas", "Convertidos", "Conversão"],
        [str(total_geral), str(total_tentativas), str(total_convertidos), f"{taxa:.1f}%"],
    ]
    resumo_table = Table(resumo_data, colWidths=[4.0 * cm] * 4)
    resumo_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 11),
                ('TOPPADDING', (0, 1), (-1, 1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ]
        )
    )
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.4 * cm))

    resumo_status = relatorio.get('resumo') or []
    elements.append(Paragraph("Resultados por Status", section_style))
    status_data = [["Status", "Total"]]
    for row in resumo_status:
        try:
            status = row['status_prospeccao']
            total = row['total']
        except Exception:
            try:
                status, total = row
            except Exception:
                continue
        status_data.append([str(status), str(total)])

    status_table = Table(status_data, colWidths=[14.0 * cm, 3.0 * cm], repeatRows=1)
    status_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(status_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Estilos para as células da tabela
    cell_style = ParagraphStyle(
        'CellStyle',
        parent=styles['Normal'],
        fontSize=7,
        leading=8,
        alignment=0, # Left
    )
    cell_style_bold = ParagraphStyle(
        'CellStyleBold',
        parent=cell_style,
        fontSize=7,
        fontName='Helvetica-Bold',
        textColor=colors.white,
    )

    items = relatorio.get('items') or relatorio.get('detalhes_prospeccao') or []
    elements.append(Paragraph(f"Lista Detalhada ({len(items)})", section_style))
    
    # Cabeçalho com Paragraph para suportar quebra se necessário
    itens_data = [[
        Paragraph("Data", cell_style_bold),
        Paragraph("Loja", cell_style_bold),
        Paragraph("CNPJ", cell_style_bold),
        Paragraph("Cidade/UF", cell_style_bold),
        Paragraph("Segmento", cell_style_bold),
        Paragraph("Status", cell_style_bold),
        Paragraph("Retorno", cell_style_bold),
        Paragraph("Observação", cell_style_bold)
    ]]

    for item in items:
        cidade = str(_row_get(item, 'cidade', ''))
        uf = str(_row_get(item, 'estado', ''))
        cidade_uf = cidade
        if uf:
            cidade_uf = f"{cidade}/{uf}" if cidade else uf
        
        data_retorno = str(_row_get(item, 'data_retorno', ''))
        hora_retorno = str(_row_get(item, 'hora_retorno', ''))
        retorno = "-"
        if data_retorno:
            retorno = f"{data_retorno} {hora_retorno}" if hora_retorno else data_retorno
        observacao = str(_row_get(item, 'observacao', '')) or '-'

        itens_data.append([
            Paragraph(str(_row_get(item, 'data_prospeccao', '')), cell_style),
            Paragraph(str(_row_get(item, 'nome_loja', '')), cell_style),
            Paragraph(str(_row_get(item, 'cnpj', '') or '-'), cell_style),
            Paragraph(cidade_uf, cell_style),
            Paragraph(str(_row_get(item, 'segmento', '') or '-'), cell_style),
            Paragraph(str(_row_get(item, 'status_prospeccao', '')), cell_style),
            Paragraph(retorno, cell_style),
            Paragraph(observacao, cell_style)
        ])

    itens_table = Table(
        itens_data,
        colWidths=[1.4 * cm, 3.0 * cm, 2.0 * cm, 2.2 * cm, 2.0 * cm, 2.0 * cm, 2.0 * cm, 2.5 * cm],
        repeatRows=1
    )
    itens_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 3),
                ('RIGHTPADDING', (0, 0), (-1, -1), 3),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(itens_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def save_pdf_copy(pdf_bytes: bytes, export_dir: str, filename: str) -> str:
    """Salva cópia do PDF em diretório de exportação."""
    os.makedirs(export_dir, exist_ok=True)
    path = os.path.join(export_dir, filename)
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    return path


def default_pdf_filename(data_inicio: str, data_fim: str) -> str:
    """Gera nome padrão para arquivo PDF."""
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if data_inicio == data_fim:
        return f"relatorio_{data_inicio}_{stamp}.pdf"
    return f"relatorio_{data_inicio}_a_{data_fim}_{stamp}.pdf"
