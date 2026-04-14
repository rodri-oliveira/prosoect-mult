import fitz
import os

def limpar_apenas_primeira_pagina():
    input_pdf = "orcamento_Geverton.pdf"
    output_pdf = "orcamento_PAG1_LIMPA.pdf"
    
    if not os.path.exists(input_pdf):
        print(f"Erro: {input_pdf} nao encontrado.")
        return

    doc = fitz.open(input_pdf)
    
    # TRABALHAMOS APENAS NA PAGINA 1 (Indice 0)
    page = doc[0] 
    
    print(f"--- Iniciando limpeza EXCLUSIVA na Pagina 1 ---")
    
    # Busca as ancoras do bloco apenas na primeira pagina
    r_cliente = page.search_for("Cliente:")
    r_br = page.search_for(".BR")
    
    if r_cliente and r_br:
        # Cria o retangulo de limpeza baseado no texto encontrado
        bloco = r_cliente[0] | r_br[-1]
        bloco.x0 -= 30  # Margem para icones
        bloco.y0 -= 10
        bloco.x1 += 15
        bloco.y1 += 15
        
        # Sombra branca e Redaçao oficial
        page.draw_rect(bloco, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.add_redact_annot(bloco, fill=(1, 1, 1))
        page.apply_redactions()
        print("Pagina 1: Bloco do cliente removido com sucesso.")
    else:
        # Fallback de segurança se nao achar os textos
        area_manual = fitz.Rect(180, 130, 480, 430)
        page.draw_rect(area_manual, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.add_redact_annot(area_manual, fill=(1, 1, 1))
        page.apply_redactions()
        print("Pagina 1: Limpeza realizada via area de segurança manual.")

    # A partir daqui, o script nao mexe em mais nenhuma pagina.
    
    doc.save(output_pdf)
    print(f"\n[OK] Segunda pagina preservada. Arquivo gerado: {output_pdf}")

if __name__ == "__main__":
    limpar_apenas_primeira_pagina()
