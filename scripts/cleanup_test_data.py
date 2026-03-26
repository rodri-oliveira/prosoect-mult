import sqlite3
import os

DB_PATH = 'database.db'

def cleanup():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    
    # Deletar o lead de teste
    c.execute("DELETE FROM leads WHERE nome_loja = 'LOJA TECH GEEK TESTE'")
    deleted = c.rowcount
    
    conn.commit()
    conn.close()
    print(f"Limpeza concluída. {deleted} registros removidos.")

if __name__ == "__main__":
    cleanup()
