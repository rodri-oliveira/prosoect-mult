import sys
import os

# Ajustar path para importar módulos da raiz ANTES dos outros imports
sys.path.append(r'c:\projetos\prospect-mult')

from infrastructure.repositories.sqlite_prospeccao_repository import SqliteProspeccaoRepository

def fix_contact():
    repo = SqliteProspeccaoRepository()
    prospeccao_id = 294
    
    print(f"Tentando converter ID {prospeccao_id} (IF Informática)...")
    lead_id = repo.converter_para_lead(prospeccao_id)
    
    if lead_id:
        print(f"SUCESSO! Convertido para Lead ID: {lead_id}")
    else:
        print("FALHA na conversão.")

if __name__ == "__main__":
    fix_contact()
