import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'database.db')

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Verifica backup
backups = sorted([f for f in os.listdir(os.path.dirname(DB_PATH)) if f.startswith('database_backup_')])
if not backups:
    print("ERRO: Nenhum backup encontrado. Abortando.")
    exit(1)

print(f"Backup detectado: {backups[-1]}")
print("\nIniciando limpeza...")

# Verifica counts antes
tabelas = [
    'prospeccao_eventos',
    'prospeccao_temp',
    'segmentos_loja',
    'contatos',
    'pedido_itens',
    'pedidos',
    'leads',
    'maps_place_details_cache'
]

print("\nContagens ANTES:")
for t in tabelas:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"  {t:<30} {count:>6}")

# Executa deleções na ordem correta (filhos -> pais)
deletes = [
    ("prospeccao_eventos", "DELETE FROM prospeccao_eventos"),
    ("prospeccao_temp", "DELETE FROM prospeccao_temp"),
    ("segmentos_loja", "DELETE FROM segmentos_loja"),
    ("contatos", "DELETE FROM contatos"),
    ("pedido_itens", "DELETE FROM pedido_itens"),
    ("pedidos", "DELETE FROM pedidos"),
    ("leads", "DELETE FROM leads"),
    ("maps_place_details_cache", "DELETE FROM maps_place_details_cache"),
]

for nome, sql in deletes:
    try:
        c.execute(sql)
        print(f"  [OK] {nome}: {c.rowcount} registros removidos")
    except Exception as e:
        print(f"  [FALHA] {nome}: {e}")
        conn.rollback()
        raise

conn.commit()

# Reseta sequências para começar do 1
print("\nResetando sequências (sqlite_sequence)...")
for t in ['prospeccao_temp', 'prospeccao_eventos', 'leads', 'contatos', 'segmentos_loja']:
    c.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = ?", (t,))

conn.commit()

print("\nContagens DEPOIS:")
for t in tabelas:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"  {t:<30} {count:>6}")

conn.close()
print("\nLimpeza concluída com sucesso!")
print(f"Backup disponível em: {backups[-1]}")
