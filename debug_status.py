import sqlite3

conn = sqlite3.connect('database.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

# Ver registros atrasados (data_retorno < hoje)
c.execute("""
    SELECT id, nome_loja, status_prospeccao, observacao, data_retorno
    FROM prospeccao_temp
    WHERE data_retorno < '2026-05-04'
    AND (arquivado = 0 OR arquivado IS NULL)
    AND status_prospeccao IN ('Pediu para retornar', 'Agendamento', 'Em negociação')
    ORDER BY data_retorno
    LIMIT 5
""")

print("Registros atrasados:")
rows = c.fetchall()
if not rows:
    print("Nenhum registro atrasado encontrado")
else:
    for row in rows:
        r = dict(row)
        print(f"ID: {r['id']}, Nome: {r['nome_loja']}, Status: {r['status_prospeccao']}, Observacao: {r['observacao']}, Data: {r['data_retorno']}")
