import os
from datetime import datetime


def _row_get(row, key: str, default: str = ""):
    if row is None:
        return default
    try:
        val = row[key]
    except Exception:
        return default
    return default if val is None else val


def build_relatorio_pdf_bytes(relatorio: dict, data_inicio: str, data_fim: str) -> bytes:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from io import BytesIO

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

    elements = []

    elements.append(Paragraph("RELATÓRIO DE PRODUTIVIDADE", title_style))
    elements.append(Paragraph(f"Período: {data_inicio} a {data_fim}", subtitle_style))

    # Métricas (objetivo)
    elements.append(Paragraph("Resumo", section_style))
    resumo_data = [
        [
            'Prospecções',
            'Tentativas',
            'Agendamentos',
            'Convertidos',
            'Ligações',
            'WhatsApp',
            'Efetivos',
            'Novos Leads',
        ],
        [
            str(relatorio.get('total_prospeccoes', 0)),
            str(relatorio.get('tentativas_prospeccao', 0)),
            str(relatorio.get('agendamentos', 0)),
            str(relatorio.get('convertidos', 0)),
            str(relatorio.get('ligacoes', 0)),
            str(relatorio.get('whatsapp', 0)),
            str(relatorio.get('efetivos', 0)),
            str(relatorio.get('novos_leads', 0)),
        ],
    ]

    resumo_table = Table(resumo_data, colWidths=[2.2 * cm] * 8)
    resumo_table.setStyle(
        TableStyle(
            [
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#111827')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d1d5db')),
                ('FONTNAME', (0, 1), (-1, 1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('TOPPADDING', (0, 1), (-1, 1), 6),
                ('BOTTOMPADDING', (0, 1), (-1, 1), 6),
            ]
        )
    )
    elements.append(resumo_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Prospecção (detalhes objetivos)
    detalhes_prosp = relatorio.get('detalhes_prospeccao') or []
    elements.append(Paragraph(f"Prospecção - Detalhes ({len(detalhes_prosp)})", section_style))

    prosp_data = [["Data", "Loja", "Cidade", "Telefone", "Status", "Retorno", "Obs"]]
    for item in detalhes_prosp:
        prosp_data.append(
            [
                str(_row_get(item, 'data_prospeccao', '')),
                str(_row_get(item, 'nome_loja', '')),
                str(_row_get(item, 'cidade', '')),
                str(_row_get(item, 'telefone', '')),
                str(_row_get(item, 'status_prospeccao', '')),
                str(_row_get(item, 'data_retorno', '')),
                str(_row_get(item, 'observacao', '')),
            ]
        )

    prosp_table = Table(
        prosp_data,
        colWidths=[2.0 * cm, 4.8 * cm, 2.6 * cm, 2.8 * cm, 3.0 * cm, 2.2 * cm, 5.0 * cm],
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
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]
        )
    )
    elements.append(prosp_table)
    elements.append(Spacer(1, 0.4 * cm))

    # Leads (detalhes objetivos)
    detalhes_leads = relatorio.get('detalhes_leads') or []
    elements.append(Paragraph(f"Leads - Ações Registradas ({len(detalhes_leads)})", section_style))

    leads_data = [["Data", "Loja", "Cidade", "Tipo", "Resultado", "Obs", "Status"]]
    for item in detalhes_leads:
        leads_data.append(
            [
                str(_row_get(item, 'data', '')),
                str(_row_get(item, 'nome_loja', '')),
                str(_row_get(item, 'cidade', '')),
                str(_row_get(item, 'tipo_contato', '')),
                str(_row_get(item, 'resultado', '')),
                str(_row_get(item, 'observacao', '')),
                str(_row_get(item, 'status_final', '')),
            ]
        )

    leads_table = Table(
        leads_data,
        colWidths=[2.0 * cm, 5.0 * cm, 2.6 * cm, 2.0 * cm, 3.0 * cm, 5.0 * cm, 2.2 * cm],
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

    doc.build(elements)

    buffer.seek(0)
    return buffer.read()


def save_pdf_copy(pdf_bytes: bytes, export_dir: str, filename: str) -> str:
    os.makedirs(export_dir, exist_ok=True)
    path = os.path.join(export_dir, filename)
    with open(path, 'wb') as f:
        f.write(pdf_bytes)
    return path


def default_pdf_filename(data_inicio: str, data_fim: str) -> str:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if data_inicio == data_fim:
        return f"relatorio_{data_inicio}_{stamp}.pdf"
    return f"relatorio_{data_inicio}_a_{data_fim}_{stamp}.pdf"
