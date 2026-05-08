import sqlite3

conn = sqlite3.connect('database.db')
c = conn.cursor()

c.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tabelas = [row[0] for row in c.fetchall()]

print(f"{'Tabela':<30} {'Registros':>10}")
print("="*50)
for t in tabelas:
    c.execute(f"SELECT COUNT(*) FROM {t}")
    count = c.fetchone()[0]
    print(f"{t:<30} {count:>10}")

print("\n" + "="*80)
print("RELACIONAMENTOS (Foreign Keys):")
for t in tabelas:
    c.execute(f"PRAGMA foreign_key_list({t})")
    fks = c.fetchall()
    for fk in fks:
        print(f"  {t}.{fk[3]} -> {fk[2]}.{fk[4]}")

conn.close()
