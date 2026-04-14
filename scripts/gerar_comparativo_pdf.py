from fpdf import FPDF
import os

class ProposalPDF(FPDF):
    def header(self):
        # Logo ou Título
        self.set_font('Arial', 'B', 15)
        self.set_text_color(23, 37, 84) # Dark Blue
        self.cell(0, 10, 'Comparativo Tecnico de Solucoes - Multi', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_proposal():
    pdf = ProposalPDF()
    pdf.add_page()
    pdf.set_font('Arial', '', 10)

    # Introdução
    pdf.set_font('Arial', '', 11)
    pdf.multi_cell(0, 7, 'Este documento apresenta uma comparacao tecnica entre produtos de mercado e as solucoes equivalentes da marca Multi (ex-Multilaser), focando em especificacoes tecnicas e desempenho para ambientes corporativos e B2B.')
    pdf.ln(10)

    # Tabela Headers
    pdf.set_fill_color(240, 240, 245)
    pdf.set_font('Arial', 'B', 10)
    
    col_widths = [35, 55, 55, 45]
    headers = ['Categoria', 'Marca Referencia', 'Equivalente Multi', 'Principais Specs']
    
    for i in range(len(headers)):
        pdf.cell(col_widths[i], 10, headers[i], 1, 0, 'C', 1)
    pdf.ln()

    # Dados
    data = [
        ['Mouse USB', 'C3Tech MS-35', 'Multi MO300', '1200 DPI, Plug & Play'],
        ['Mouse USB', 'Chinamate CM10 Black', 'Multi MO255', 'Sensor Optico, Ergonomico'],
        ['Mouse Wireless', 'Logitech M170', 'Multi MO251', '2.4GHz stable, Nano Rec.'],
        ['Kit Wireless', 'Dell KM3322W', 'Multi TC270', 'Combo Slim, ABNT2, 2.4G'],
        ['Ergonomia', 'Mousepad Gel', 'Multi AC021', 'Apoio Confortavel, Antid.'],
        ['Audio BT', 'GraSep D-S4153', 'Multi SP336', '10W RMS, FM, USB, SD'],
        ['Headset Gamer', 'Redragon Ares RGB', 'Warrior PH225', 'Audio Imersivo, RGB, Mic']
    ]

    pdf.set_font('Arial', '', 10)
    for row in data:
        # Calcular altura necessária para a linha (baseado na célula que pode ter mais texto)
        max_height = 10
        for i in range(len(row)):
            # Simplificação: se o texto for muito longo, aumenta a altura
            if len(row[i]) > 25:
                max_height = 15
        
        for i in range(len(row)):
            # Cell(w, h, txt, border, ln, align, fill)
            # Usando multicell se precisar, mas aqui vamos manter simples
            pdf.cell(col_widths[i], max_height, row[i], 1, 0, 'L')
        pdf.ln()

    output_path = r'c:\projetos\prospect-mult\teste\propostas\comparativo_multi_b2b.pdf'
    pdf.output(output_path)
    print(f"PDF gerado com sucesso em: {output_path}")

if __name__ == '__main__':
    create_proposal()
