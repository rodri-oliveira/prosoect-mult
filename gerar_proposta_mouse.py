from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Cabeçalho Oficial
        logo_path = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090681266.png'
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=190)
        self.ln(60)
        
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'PROPOSTA DE EQUIVALÊNCIA TÉCNICA', 0, 1, 'L')
        self.set_draw_color(0, 0, 0)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def footer(self):
        footer_img = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090697124.png'
        if os.path.exists(footer_img):
            self.image(footer_img, x=10, y=self.h - 45, w=110)
        
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')

pdf = PDF()
pdf.add_page()

# Texto de Introdução
pdf.set_font('helvetica', '', 10)
pdf.multi_cell(0, 5, 'Prezado cliente,\n\nConforme solicitado, apresentamos a solução técnica que atende aos requisitos de conectividade Bluetooth e ergonomia padrão para uso profissional. Abaixo, detalhamos o comparativo do modelo Multi MS850 (MO401).\n')
pdf.ln(5)

# Tabela Comparativa
pdf.set_font('helvetica', 'B', 10)
pdf.set_fill_color(220, 220, 220)
# Cabeçalhos da Tabela
pdf.cell(50, 8, 'REQUISITO', 1, 0, 'C', True)
pdf.cell(70, 8, 'SOLICITADO PELO CLIENTE', 1, 0, 'C', True)
pdf.cell(70, 8, 'MODELO MULTI MS850', 1, 1, 'C', True)

pdf.set_font('helvetica', '', 9)
items = [
    ('Tamanho', 'Padrão (Ergonômico)', 'Padrão (Design Premium)'),
    ('Sensor', 'LED / Óptico', 'LED Óptico de Alta Precisão'),
    ('Conexão', 'Bluetooth', 'Bluetooth 3.0 / 5.0 (Dual Channel)'),
    ('Conectividade', 'Sem Fio', 'Sem Fio 2.4GHz + Bluetooth'),
    ('Diferencial', '-', 'Multidispositivos (Conecta até 3 aparelhos)'),
    ('Nível de Ruído', '-', 'Tecnologia Silent (Clique Silencioso)')
]

for req, sol, multi in items:
    pdf.cell(50, 8, req, 1, 0, 'L')
    pdf.cell(70, 8, sol, 1, 0, 'C')
    pdf.set_font('helvetica', 'B', 9)
    pdf.cell(70, 8, multi, 1, 1, 'C')
    pdf.set_font('helvetica', '', 9)

pdf.ln(10)

# Descritivo Técnico Detalhado
pdf.set_font('helvetica', 'B', 11)
pdf.cell(0, 10, 'DETALHES DO MODELO SUGERIDO: MULTI MS850 (MO401)', 0, 1, 'L')
pdf.set_font('helvetica', '', 10)
desc = (
    "O mouse Multi MS850 é a escolha ideal para o ambiente executivo que busca versatilidade. "
    "Sua tecnologia multidisciplinar permite que ele seja conectado simultaneamente a até três dispositivos "
    "diferentes (ex: Notebook, Tablet e PC), alternando entre eles com um simples toque. "
    "Sua construção robusta de tamanho padrão oferece ergonomia total, enquanto os botões silenciosos "
    "garantem um ambiente de trabalho mais produtivo."
)
pdf.multi_cell(0, 5, desc)

pdf_output_path = r'c:\projetos\prospect-mult\teste\Proposta_Mouse_Bluetooth_MS850.pdf'
pdf.output(pdf_output_path)
print(f"Sucesso: {pdf_output_path}")
