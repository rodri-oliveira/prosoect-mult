import fitz
import os

def limpar_pdf_padrao(input_path, output_path):
    if not os.path.exists(input_path):
        print(f"Erro: {input_path} nao encontrado.")
        return

    doc = fitz.open(input_path)
    page = doc[0] 
    
    print(f"--- Iniciando limpeza em: {os.path.basename(input_path)} ---")
    
    # Definindo a área de limpeza PADRÃO para o bloco do cliente (centro)
    # x0=250 (evita o bloco Pedido na esquerda)
    # x1=550 (evita o bloco Multilaser na direita)
    # y0=120, y1=250 (cobre todas as linhas do cliente e ícones)
    area_cliente = fitz.Rect(250, 120, 550, 250)
    
    # Aplica a limpeza (máscara branca e redação permanente)
    page.draw_rect(area_cliente, color=(1, 1, 1), fill=(1, 1, 1), overlay=True)
    page.add_redact_annot(area_cliente, fill=(1, 1, 1))
    page.apply_redactions()
    
    doc.save(output_path)
    print(f"Sucesso: Bloco do cliente removido mantendo as laterais intactas.")
    print(f"[OK] Arquivo gerado: {output_path}")

if __name__ == "__main__":
    import sys
    # Se passar argumentos via linha de comando, usa eles, senão usa o padrão do Renan
    origem = r"C:\projetos\prospect-mult\teste\Geverton\ORÇAMENTO REANAN.pdf"
    destino = r"C:\projetos\prospect-mult\teste\Geverton\ORÇAMENTO REANAN_LIMPO.pdf"
    
    if len(sys.argv) > 1:
        origem = sys.argv[1]
        if len(sys.argv) > 2:
            destino = sys.argv[2]
            
    limpar_pdf_padrao(origem, destino)
