from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'ESPECIFICAÇÕES TÉCNICAS DE PRODUTOS', 0, 1, 'C')
        self.set_font('Arial', '', 10)
        self.cell(0, 5, 'Portfólio de Periféricos Multi (Multilaser)', 0, 1, 'C')
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Página {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(240, 240, 240)
        self.cell(0, 8, title, 0, 1, 'L', True)
        self.ln(4)

    def chapter_body(self, data):
        self.set_font('Arial', '', 10)
        for key, value in data.items():
            self.set_font('Arial', 'B', 10)
            self.write(5, f"{key}: ")
            self.set_font('Arial', '', 10)
            self.write(5, f"{value}\n")
        self.ln(8)

pdf = PDF()
pdf.add_page()

# 1. Teclado com Fio TF100
pdf.chapter_title('1. TECLADO COM FIO USB COMPACTO TF100')
specs_tf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Comprimento do Cabo': '1,20 metro',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Compatibilidade': 'Windows, Linux, MacOS',
    'Características': 'Resistente a respingos, teclas macias e silenciosas, ajuste de altura',
    'Design': 'Compacto com teclado numérico (otimização de espaço)',
    'Cor': 'Preto'
}
pdf.chapter_body(specs_tf100)

# 2. Teclado Sem Fio TS10
pdf.chapter_title('2. TECLADO SEM FIO BÁSICO TS10')
specs_ts10 = {
    'Conexão': 'Sem fio 2.4GHz (com receptor Nano USB)',
    'Alcance': 'Até 10 metros de distância',
    'Padrão': 'ABNT2 (Padrão brasileiro)',
    'Alimentação': 'Pilha (inclusa ou baixo consumo)',
    'Design': 'Slim / Compacto (Ideal para estações modernas)',
    'Compatibilidade': 'Universal (Plug & Play)'
}
pdf.chapter_body(specs_ts10)

# 3. Mouse com Fio MF100
pdf.chapter_title('3. MOUSE COM FIO USB 1200DPI MF100')
specs_mf100 = {
    'Conexão': 'USB com fio (Plug & Play)',
    'Comprimento do Cabo': '1,20 metro',
    'Resolução': '1200 DPI (Alta precisão e agilidade)',
    'Botões': '3 botões com scroll scroll emborrachado',
    'Design': 'Ergonômico e ambidestro',
    'Tecnologia': 'Sensor Óptico de alta sensibilidade'
}
pdf.chapter_body(specs_mf100)

# 4. Mouse Sem Fio MS100
pdf.chapter_title('4. MOUSE SEM FIO USB 1200DPI MS100')
specs_ms100 = {
    'Conexão': 'Sem fio 2.4GHz (Nano Receptor USB)',
    'Alcance': 'Até 10 metros',
    'Resolução': '1200 DPI',
    'Design': 'Slim / Ergonômico (Uso prolongado sem fadiga)',
    'Gerenciamento de Energia': 'Desligamento automático inteligente (Economia de pilha)',
    'Alimentação': 'Pilha AA'
}
pdf.chapter_body(specs_ms100)

pdf_output_path = "C:/projetos/prospect-mult/Especificacoes_Tecnicas_Multi.pdf"
pdf.output(pdf_output_path)
print(f"PDF gerado com sucesso em: {pdf_output_path}")
