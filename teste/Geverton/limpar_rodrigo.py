import fitz
import os

def limpar_pdf_especifico(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Erro: {input_path} nao encontrado.")
        return

    doc = fitz.open(input_path)
    
    # TRABALHAMOS APENAS NA PAGINA 1 (Indice 0)
    page = doc[0] 
    
    print(f"--- Iniciando limpeza em: {os.path.basename(input_path)} ---")
    
    # Busca as ancoras do bloco do cliente
    r_cliente = page.search_for("Cliente:")
    r_br = page.search_for(".BR")
    
    if r_cliente and r_br:
        # Cria o retangulo de limpeza baseado no texto encontrado
        bloco = r_cliente[0] | r_br[-1]
        # Ajuste de margens para nado sobrar nada (icones, etc)
        bloco.x0 -= 35  
        bloco.y0 -= 10
        bloco.x1 += 20
        bloco.y1 += 20
        
        # Mascara branca e Redaçao permanente
        page.draw_rect(bloco, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.add_redact_annot(bloco, fill=(1, 1, 1))
        page.apply_redactions()
        print("Sucesso: Bloco do cliente removido da primeira pagina.")
    else:
        print("Aviso: Ancoras nao encontradas. Tentando area de segurança padrao...")
        # Area padrao caso os textos variem levemente
        area_manual = fitz.Rect(180, 130, 480, 410)
        page.draw_rect(area_manual, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
        page.add_redact_annot(area_manual, fill=(1, 1, 1))
        page.apply_redactions()

    doc.save(output_path)
    print(f"[OK] Arquivo gerado: {output_path}")

if __name__ == "__main__":
    origem = r"C:\projetos\prospect-mult\teste\Geverton\rodrigo.pdf"
    destino = r"C:\projetos\prospect-mult\teste\Geverton\rodrigo_LIMPO.pdf"
    limpar_pdf_especifico(origem, destino)
