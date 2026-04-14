from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        logo_path = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090681266.png'
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=190)
        self.ln(60)
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'PROPOSTA COMERCIAL: SOLUÇÕES EM PERIFÉRICOS BLUETOOTH', 0, 1, 'L')
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

pdf.set_font('helvetica', '', 10)
pdf.multi_cell(0, 5, 'Prezado,\n\nApresentamos abaixo duas opções de alta performance que atendem aos requisitos técnicos solicitados (Tamanho Padrão + Conectividade Bluetooth), com diferentes perfis de carregamento e uso.\n')
pdf.ln(5)

# Tabela Comparativa de 3 Colunas
pdf.set_font('helvetica', 'B', 9)
pdf.set_fill_color(230, 230, 230)
pdf.cell(40, 8, 'CARACTERÍSTICA', 1, 0, 'C', True)
pdf.cell(75, 8, 'OPÇÃO 01: MS850 (MO401)', 1, 0, 'C', True)
pdf.cell(75, 8, 'OPÇÃO 02: WARRIOR (MO421)', 1, 1, 'C', True)

pdf.set_font('helvetica', '', 8.5)
items = [
    ('Tamanho', 'Padrão / Ergonômico', 'Padrão / Gamer Premium'),
    ('Conexão Principal', 'Bluetooth 3.0/5.0 + Wireless', 'Tri-Mode (BT + Wireless + Cabo)'),
    ('Energia', 'Alimentação via Pilhas AA (Inclusas)', 'Recarregável via Base USB-C'),
    ('DPI (Precisão)', '800 a 3200 DPI', 'Até 10.000 DPI (Ajustável)'),
    ('Botões', 'Silenciosos (Ideal para Escritório)', 'Alta Resposta Tátil'),
    ('Diferencial', 'Multidispositivo (3 Conexões)', 'Base de Carregamento Inclusa')
]

for req, opt1, opt2 in items:
    pdf.cell(40, 8, req, 1, 0, 'L', True)
    pdf.cell(75, 8, opt1, 1, 0, 'C')
    pdf.cell(75, 8, opt2, 1, 1, 'C')

pdf.ln(10)

# Resumo MO401
pdf.set_font('helvetica', 'B', 10)
pdf.cell(0, 8, 'Destaque Opção 01 - Multi MS850:', 0, 1, 'L')
pdf.set_font('helvetica', '', 9.5)
pdf.multi_cell(0, 5, 'Focada em produtividade extrema. Permite alternar entre seu notebook pessoal, tablet e computador da empresa com um único botão. Tecnologia silenciosa para não incomodar em ambientes de trabalho.')
pdf.ln(3)

# Resumo MO421
pdf.set_font('helvetica', 'B', 10)
pdf.cell(0, 8, 'Destaque Opção 02 - Warrior Magnus:', 0, 1, 'L')
pdf.set_font('helvetica', '', 9.5)
pdf.multi_cell(0, 5, 'Focada em tecnologia e conveniência. Elimina a necessidade de troca de pilhas através da sua base de carregamento rápido. Oferece o tempo de resposta mais baixo do mercado devido à tripla conectividade.')

# Pasta Final
dest = r'C:\projetos\prospect-mult\teste\Geverton'
if not os.path.exists(dest):
    os.makedirs(dest)

pdf_output_path = os.path.join(dest, "Proposta_Comparativa_Premium.pdf")
pdf.output(pdf_output_path)
print(f"Sucesso: {pdf_output_path}")
