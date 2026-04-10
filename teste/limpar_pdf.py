import fitz
import os

def limpar_bloco_com_deteccao():
    input_pdf = "orcamento_Geverton.pdf"
    output_pdf = "orcamento_DEFINITIVO_MESMO.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"Erro: {input_pdf} nao encontrado.")
        return

    doc = fitz.open(input_pdf)
    
    for page in doc:
        # Busca as ancoras do bloco
        r_cliente = page.search_for("Cliente:")
        r_br = page.search_for(".BR")
        
        if r_cliente and r_br:
            # Cria um retangulo que une o inicio (Cliente:) ao fim (.BR)
            # Pegamos o primeiro "Cliente:" e o ultimo ".BR" da pagina
            bloco = r_cliente[0] | r_br[-1]
            
            # Adicionamos uma margem de folga de 25 pontos para cada lado
            # para garantir que pegue icones e bordas
            bloco.x0 -= 30
            bloco.y0 -= 10
            bloco.x1 += 15
            bloco.y1 += 15
            
            # Pinta de branco
            page.draw_rect(bloco, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
            # Redaçao oficial
            page.add_redact_annot(bloco, fill=(1, 1, 1))
            page.apply_redactions()
            print(f"Bloco detectado e limpo na pagina {page.number + 1}")
        else:
            # Fallback se a deteçao falhar: usa uma area manual gigante
            area_manual = fitz.Rect(180, 130, 480, 400)
            page.draw_rect(area_manual, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
            page.add_redact_annot(area_manual, fill=(1, 1, 1))
            page.apply_redactions()
            print(f"Limpando via area de segurança na pagina {page.number + 1}")

    doc.save(output_pdf)
    print(f"\n[OK] Arquivo gerado: {output_pdf}")

if __name__ == "__main__":
    limpar_bloco_com_deteccao()
