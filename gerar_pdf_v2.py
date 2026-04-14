from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Logo e Dados do Vendedor
        logo_path = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090681266.png'
        if os.path.exists(logo_path):
            self.image(logo_path, x=10, y=8, w=190)
        
        # Aumentamos muito o ln para descer abaixo do e-mail do vendedor
        self.ln(45) 
        
        # Linha decorativa fina abaixo do cabeçalho (opcional, mas profissional)
        self.set_draw_color(200, 200, 200)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)
        
        self.set_font('helvetica', 'B', 14)
        self.cell(0, 10, 'FICHA TÉCNICA DE PRODUTOS', 0, 1, 'L')
        self.ln(5)

    def footer(self):
        footer_img = r'C:\Users\rodrigo.deoliveira\.gemini\antigravity\brain\bb1eaa72-5329-4cca-a77c-271f5d70815f\media__1776090697124.png'
        if os.path.exists(footer_img):
            self.image(footer_img, x=10, y=self.h - 35, w=110)
        
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'R')

    def chapter_title(self, title):
        self.set_font('helvetica', 'B', 11)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, 0, 1, 'L', True)
        self.ln(3)

    def chapter_body(self, data):
        self.set_font('helvetica', '', 9)
        for key, value in data.items():
            self.set_font('helvetica', 'B', 9)
            self.write(5, f"{key}: ")
            self.set_font('helvetica', '', 9)
            self.write(5, f"{value}\n")
        self.ln(10)

pdf = PDF()
pdf.add_page()

# 1. Teclado com Fio TF100
pdf.chapter_title('TECLADO COM FIO MULTI TF100 (USB COMPACTO)')
specs_tf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Comprimento do Cabo': '1,20 metro',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Compatibilidade': 'Windows, Linux, MacOS',
    'Diferenciais': 'Resistente a respingos, teclas macias e silenciosas, ajuste de altura'
}
pdf.chapter_body(specs_tf100)

# 2. Teclado Sem Fio TS10
pdf.chapter_title('TECLADO SEM FIO MULTI TS10 (BÁSICO USB)')
specs_ts10 = {
    'Conexão': 'Sem fio 2.4GHz (com receptor Nano USB)',
    'Alcance': 'Conectividade estável em até 10 metros',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Design': 'Perfil Slim / Compacto (Otimização de espaço na estação)',
    'Praticidade': 'Instalação automática (Plug & Play)'
}
pdf.chapter_body(specs_ts10)

# 3. Mouse com Fio MF100
pdf.chapter_title('MOUSE COM FIO MULTI MF100 (1200DPI 3BOT)')
specs_mf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Resolução': '1200 DPI (Alta precisão para tarefas corporativas)',
    'Botões': '3 botões (incluindo Scroll Emborrachado)',
    'Design': 'Ergonômico e ambidestro (Conforto para uso prolongado)'
}
pdf.chapter_body(specs_mf100)

# 4. Mouse Sem Fio MS100
pdf.chapter_title('MOUSE SEM FIO MULTI MS100 (1200DPI 3BOT SLIM)')
specs_ms100 = {
    'Conexão': 'Sem fio 2.4GHz (Nano Receptor USB)',
    'Resolução': '1200 DPI',
    'Design': 'Slim / Ergonômico',
    'Economia': 'Sistema de desligamento automático para preservação da bateria'
}
pdf.chapter_body(specs_ms100)

pdf_output_path = r'c:\projetos\prospect-mult\teste\Ficha_Tecnica_Oficial_Multi.pdf'
pdf.output(pdf_output_path)
print(f"Sucesso: {pdf_output_path}")
