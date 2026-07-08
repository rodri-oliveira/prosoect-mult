# -*- coding: utf-8 -*-
from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Title of the PDF
        self.set_font('Helvetica', 'B', 15)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, 'TABELA COMPARATIVA DE PRECOS', 0, 1, 'C')
        self.set_font('Helvetica', 'I', 10)
        self.cell(0, 5, 'Multilaser vs. Lojas Sennheiser (Site Oficial)', 0, 1, 'C')
        self.ln(5)
        
        # Horizontal line
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

# Initialize PDF
pdf = PDF(orientation='P', unit='mm', format='A4')
pdf.set_margins(10, 10, 10)
pdf.add_page()

# Columns widths (Total 190 mm)
col_widths = {
    "cod_multi": 22,
    "produto": 48,
    "part_number": 20,
    "multi": 25,
    "senn": 27,
    "economia": 25,
    "vantagem": 23
}

# Header Row
pdf.set_font('Helvetica', 'B', 8)
pdf.set_fill_color(230, 235, 245) # Soft Blue
pdf.set_text_color(30, 50, 90)

pdf.cell(col_widths["cod_multi"], 8, 'Cod. Multi', 1, 0, 'C', True)
pdf.cell(col_widths["produto"], 8, 'Produto / Modelo', 1, 0, 'L', True)
pdf.cell(col_widths["part_number"], 8, 'Part Number', 1, 0, 'C', True)
pdf.cell(col_widths["multi"], 8, 'Multilaser', 1, 0, 'R', True)
pdf.cell(col_widths["senn"], 8, 'Sennheiser', 1, 0, 'R', True)
pdf.cell(col_widths["economia"], 8, 'Economia (R$)', 1, 0, 'R', True)
pdf.cell(col_widths["vantagem"], 8, 'Vantagem', 1, 1, 'C', True)

# Data Rows
data = [
    {"cod_multi": "SF104", "produto": "EW-D ME3 SET (Q1-6)", "part_number": "508710", "multi": "R$ 4.492,34", "senn": "R$ 5.737,00", "economia": "R$ 1.244,66", "vantagem": "Multi 21.7%", "status": "multi_cheaper"},
    {"cod_multi": "SF103", "produto": "EW-D ME2 SET (R4-9)", "part_number": "508702", "multi": "R$ 4.492,34", "senn": "Nao disponivel", "economia": "-", "vantagem": "-", "status": "none"},
    {"cod_multi": "SF111", "produto": "EW-D 835-S SET (Q1-6)", "part_number": "508750", "multi": "R$ 4.333,26", "senn": "R$ 6.190,00", "economia": "R$ 1.856,74", "vantagem": "Multi 30.0%", "status": "multi_cheaper"},
    {"cod_multi": "-", "produto": "EW IEM G4-TWIN-G", "part_number": "509615", "multi": "R$ 9.084,13", "senn": "R$ 10.556,00", "economia": "R$ 1.471,87", "vantagem": "Multi 13.9%", "status": "multi_cheaper"},
    {"cod_multi": "MQ018", "produto": "E 609 SILVER", "part_number": "500074", "multi": "R$ 663,16", "senn": "Nao disponivel", "economia": "-", "vantagem": "-", "status": "none"},
    {"cod_multi": "MQ037", "produto": "XS 1", "part_number": "507487", "multi": "R$ 290,57", "senn": "R$ 365,00", "economia": "R$ 74,43", "vantagem": "Multi 20.4%", "status": "multi_cheaper"},
    {"cod_multi": "MQ011", "produto": "E 604", "part_number": "4519", "multi": "R$ 837,42", "senn": "R$ 1.239,00", "economia": "R$ 401,58", "vantagem": "Multi 32.4%", "status": "multi_cheaper"},
    {"cod_multi": "MQ009", "produto": "E 845", "part_number": "4515", "multi": "R$ 722,96", "senn": "Nao disponivel", "economia": "-", "vantagem": "-", "status": "none"},
    {"cod_multi": "MQ007", "produto": "E 835", "part_number": "4513", "multi": "R$ 662,14", "senn": "Nao disponivel", "economia": "-", "vantagem": "-", "status": "none"},
    {"cod_multi": "MQ547", "produto": "HD 280 PRO", "part_number": "506845", "multi": "R$ 773,79", "senn": "R$ 839,00", "economia": "R$ 65,21", "vantagem": "Multi 7.8%", "status": "multi_cheaper"},
    {"cod_multi": "509148CMV", "produto": "XSW IEM SET (C)", "part_number": "509148CMV", "multi": "R$ 4.637,00", "senn": "R$ 4.559,00", "economia": "-R$ 78,00", "vantagem": "Senn. 1.7%", "status": "senn_cheaper"},
    {"cod_multi": "-", "produto": "ADP UHF (470-1075 MHz)", "part_number": "508863", "multi": "R$ 1.922,01", "senn": "R$ 2.279,00", "economia": "R$ 356,99", "vantagem": "Multi 15.7%", "status": "multi_cheaper"},
    {"cod_multi": "SF314", "produto": "XSW 1-825 DUAL-A", "part_number": "508263", "multi": "R$ 4.230,26", "senn": "R$ 5.320,00", "economia": "R$ 1.089,74", "vantagem": "Multi 20.5%", "status": "multi_cheaper"},
    {"cod_multi": "-", "produto": "XSW 1-835 DUAL-A", "part_number": "508270", "multi": "R$ 4.877,42", "senn": "Nao disponivel", "economia": "-", "vantagem": "-", "status": "none"},
    {"cod_multi": "-", "produto": "MD 421 KOMPAKT", "part_number": "700587", "multi": "R$ 2.098,02", "senn": "R$ 2.469,00", "economia": "R$ 370,98", "vantagem": "Multi 15.0%", "status": "multi_cheaper"}
]

pdf.set_font('Helvetica', '', 8)
fill = False

for item in data:
    # Set text colors and styles based on status
    if item["status"] == "senn_cheaper":
        # Highlight Sennheiser Cheaper Row
        pdf.set_fill_color(255, 230, 230) # Light Red
        fill_row = True
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(150, 0, 0)
    elif item["status"] == "multi_cheaper":
        pdf.set_fill_color(230, 245, 230) # Light Green
        fill_row = False
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
    else:
        fill_row = False
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(0, 0, 0)
        
    # Draw cells
    # We want a special color for the "Vantagem" column if Multilaser is cheaper
    pdf.cell(col_widths["cod_multi"], 7, item["cod_multi"], 1, 0, 'C', fill_row)
    pdf.cell(col_widths["produto"], 7, item["produto"], 1, 0, 'L', fill_row)
    pdf.cell(col_widths["part_number"], 7, item["part_number"], 1, 0, 'C', fill_row)
    
    # Check if we should bold Multilaser or Sennheiser
    if item["status"] == "multi_cheaper":
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(col_widths["multi"], 7, item["multi"], 1, 0, 'R', fill_row)
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(col_widths["senn"], 7, item["senn"], 1, 0, 'R', fill_row)
        
        # Color advantage cell
        pdf.set_font('Helvetica', 'B', 8)
        pdf.set_text_color(0, 100, 0) # Green text
        pdf.cell(col_widths["economia"], 7, item["economia"], 1, 0, 'R', fill_row)
        pdf.cell(col_widths["vantagem"], 7, item["vantagem"], 1, 1, 'C', fill_row)
        pdf.set_text_color(0, 0, 0)
        
    elif item["status"] == "senn_cheaper":
        pdf.set_font('Helvetica', '', 8)
        pdf.cell(col_widths["multi"], 7, item["multi"], 1, 0, 'R', fill_row)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(col_widths["senn"], 7, item["senn"], 1, 0, 'R', fill_row)
        
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(col_widths["economia"], 7, item["economia"], 1, 0, 'R', fill_row)
        pdf.cell(col_widths["vantagem"], 7, item["vantagem"], 1, 1, 'C', fill_row)
    else:
        pdf.cell(col_widths["multi"], 7, item["multi"], 1, 0, 'R', fill_row)
        pdf.cell(col_widths["senn"], 7, item["senn"], 1, 0, 'R', fill_row)
        pdf.cell(col_widths["economia"], 7, item["economia"], 1, 0, 'R', fill_row)
        pdf.cell(col_widths["vantagem"], 7, item["vantagem"], 1, 1, 'C', fill_row)

# Output PDF
output_path = r'c:\projetos\prospect-mult\Comparativo_Precos_Sennheiser.pdf'
pdf.output(output_path)
print(f"Sucesso: PDF gerado em {output_path}")
