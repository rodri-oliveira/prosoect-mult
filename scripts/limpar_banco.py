#!/usr/bin/env python3
"""
Script para limpar dados de teste do banco de dados.
Mantém a estrutura das tabelas, remove todos os dados.
"""
import sqlite3
import os
import sys

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import DB_PATH


def limpar_banco(confirmar: bool = False) -> dict:
    """
    Limpa todos os dados do banco.
    
    Args:
        confirmar: Se True, executa a limpeza. Se False, apenas mostra o que seria removido.
    
    Returns:
        Dict com contagem de registros removidos por tabela.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Ordem de exclusão (respeitando foreign keys)
    tabelas = [
        ('prospeccao_eventos', 'prospeccao_id'),
        ('contatos', 'lead_id'),
        ('segmentos_loja', 'lead_id'),
        ('prospeccao_temp', None),
        ('leads', None),
    ]
    
    resultado = {}
    
    print("\n" + "="*50)
    print("LIMPEZA DO BANCO DE DADOS")
    print("="*50)
    
    # Mostrar contagem atual
    print("\nRegistros atuais:")
    for tabela, _ in tabelas:
        c.execute(f"SELECT COUNT(*) FROM {tabela}")
        count = c.fetchone()[0]
        resultado[tabela] = count
        print(f"   {tabela}: {count} registros")
    
    if not confirmar:
        print("\n[!] MODO PREVIEW - Nenhum dado foi removido")
        print("   Execute com --confirmar para limpar realmente")
        conn.close()
        return resultado
    
    # Executar limpeza
    print("\nLimpando dados...")
    for tabela, _ in tabelas:
        c.execute(f"DELETE FROM {tabela}")
        print(f"   [OK] {tabela} limpa")
    
    # Resetar autoincrement
    c.execute("DELETE FROM sqlite_sequence")
    
    conn.commit()
    conn.close()
    
    print("\n[OK] Banco de dados limpo com sucesso!")
    print("="*50)
    
    return resultado


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Limpar dados de teste do banco')
    parser.add_argument('--confirmar', action='store_true', 
                        help='Confirma a limpeza (sem esta flag, apenas preview)')
    
    args = parser.parse_args()
    
    limpar_banco(confirmar=args.confirmar)
