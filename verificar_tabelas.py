import sqlite3
import json

conn = sqlite3.connect('database.db')
c = conn.cursor()

# Lista todas as tabelas
c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tabelas = [row[0] for row in c.fetchall()]
print("Tabelas encontradas:")
for t in tabelas:
    print(f"  - {t}")

# Para cada tabela: schema + row count + sample de dados
print("\n" + "="*80)
for t in tabelas:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"\nTabela: {t} | Registros: {count}")
    
    # Schema
    c.execute(f"PRAGMA table_info({t})")
    cols = c.fetchall()
    for col in cols:
        print(f"  Coluna: {col[1]} ({col[2]}) PK={col[5]}")
    
    # Verificar FKs
    c.execute(f"PRAGMA foreign_key_list({t})")
    fks = c.fetchall()
    for fk in fks:
        print(f"  FK: {fk[3]} -> {fk[2]}.{fk[4]}")
    
    # Sample de dados (primeiras 2 linhas)
    if count > 0:
        c.execute(f"SELECT * FROM {t} LIMIT 2")
        rows = c.fetchall()
        col_names = [col[1] for col in cols]
        for row in rows:
            row_dict = dict(zip(col_names, row))
            print(f"  Exemplo: {row_dict}")

conn.close()
