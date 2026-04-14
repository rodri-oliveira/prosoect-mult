from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Logo e Dados do Vendedor (Imagem Superior 1)
        # media__1776090681266.png
        logo_path = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090681266.png'
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=190)
        self.ln(35)
        
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'ESPECIFICAÇÕES TÉCNICAS DE PRODUTOS', 0, 1, 'L')
        self.ln(2)

    def footer(self):
        # Dados da Fábrica (Imagem Inferior)
        # media__1776090697124.png
        footer_img = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090697124.png'
        if os.path.exists(footer_img):
            self.image(footer_img, x=10, y=self.h - 30, w=100)
        
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 11)
        self.set_fill_color(245, 245, 245)
        self.cell(0, 7, title, 0, 1, 'L', True)
        self.ln(2)

    def chapter_body(self, data):
        self.set_font('helvetica', '', 9)
        for key, value in data.items():
            self.set_font('helvetica', 'B', 9)
            self.write(4, f"{key}: ")
            self.set_font('helvetica', '', 9)
            self.write(4, f"{value}\n")
        self.ln(5)

pdf = PDF()
pdf.add_page()

# 1. Teclado com Fio TF100
pdf.chapter_title('TECLADO COM FIO USB COMPACTO TF100')
specs_tf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Comprimento do Cabo': '1,20 metro',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Compatibilidade': 'Windows, Linux, MacOS',
    'Características': 'Resistente a respingos, teclas macias e silenciosas, ajuste de altura',
    'Design': 'Compacto com teclado numérico (otimização de espaço)'
}
pdf.chapter_body(specs_tf100)

# 2. Teclado Sem Fio TS10
pdf.chapter_title('TECLADO SEM FIO BÁSICO TS10')
specs_ts10 = {
    'Conexão': 'Sem fio 2.4GHz (com receptor Nano USB)',
    'Alcance': 'Até 10 metros de distância',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Design': 'Slim / Compacto (Ideal para estações modernas)',
    'Compatibilidade': 'Universal (Plug & Play)'
}
pdf.chapter_body(specs_ts10)

# 3. Mouse com Fio MF100
pdf.chapter_title('MOUSE COM FIO USB 1200DPI MF100')
specs_mf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Comprimento do Cabo': '1,20 metro',
    'Resolução': '1200 DPI (Alta precisão e agilidade)',
    'Botões': '3 botões com scroll scroll emborrachado',
    'Tecnologia': 'Sensor Óptico de alta sensibilidade'
}
pdf.chapter_body(specs_mf100)

# 4. Mouse Sem Fio MS100
pdf.chapter_title('MOUSE SEM FIO USB 1200DPI MS100')
specs_ms100 = {
    'Conexão': 'Sem fio 2.4GHz (Nano Receptor USB)',
    'Alcance': 'Até 10 metros',
    'Resolução': '1200 DPI',
    'Design': 'Slim / Ergonômico (Uso prolongado sem fadiga)',
    'Gerenciamento de Energia': 'Desligamento automático inteligente'
}
pdf.chapter_body(specs_ms100)

dest_folder = r'c:\projetos\prospect-mult\teste'
if not os.path.exists(dest_folder):
    os.makedirs(dest_folder)

pdf_output_path = os.path.join(dest_folder, "Especificacoes_Tecnicas_Multi_Oficial.pdf")
pdf.output(pdf_output_path)
print(f"PDF gerado com sucesso em: {pdf_output_path}")
