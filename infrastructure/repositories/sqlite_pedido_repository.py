from __future__ import annotations
import sqlite3
from typing import List, Optional
from domain.repositories.pedido_repository import Pedido, PedidoItem, PedidoRepository
from database import DB_PATH

class SqlitePedidoRepository(PedidoRepository):
    def registrar(self, pedido: Pedido) -> int:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            # Inserir cabeçalho
            c.execute(
                """
                INSERT INTO pedidos (
                    lead_id, data_pedido, numero_pedido, valor_total, 
                    status_faturamento, data_proximo_contato, observacoes
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pedido.lead_id, pedido.data_pedido, pedido.numero_pedido,
                    pedido.valor_total, pedido.status_faturamento,
                    pedido.data_proximo_contato, pedido.observacoes
                )
            )
            venda_id = c.lastrowid

            # Inserir itens
            for item in pedido.itens:
                c.execute(
                    """
                    INSERT INTO pedido_itens (
                        pedido_id, familia, codigo_produto, descricao, 
                        quantidade, preco_unitario, preco_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        venda_id, item.familia, item.codigo_produto, item.descricao,
                        item.quantidade, item.preco_unitario, item.preco_total
                    )
                )

            # Se houver data de próximo contato, registrar no histórico de contatos como agendamento
            if pedido.data_proximo_contato:
                c.execute(
                    """
                    INSERT INTO contatos (
                        lead_id, tipo_contato, resultado, observacao, data_retorno
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        pedido.lead_id, 'Venda / Pós-Venda', 'Agendado após venda',
                        f'Retorno agendado do pedido #{venda_id}', pedido.data_proximo_contato
                    )
                )

            # Atualizar status do lead para 'Cliente Ativo'
            c.execute("UPDATE leads SET status = 'Cliente Ativo' WHERE id = ?", (pedido.lead_id,))
            
            conn.commit()
            return venda_id
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def get_by_id(self, pedido_id: int) -> Optional[Pedido]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        row = c.execute("SELECT p.*, l.nome_loja FROM pedidos p JOIN leads l ON p.lead_id = l.id WHERE p.id = ?", (pedido_id,)).fetchone()
        if not row:
            conn.close()
            return None
        
        itens_rows = c.execute("SELECT * FROM pedido_itens WHERE pedido_id = ?", (pedido_id,)).fetchall()
        itens = [
            PedidoItem(
                familia=i['familia'], 
                codigo_produto=i['codigo_produto'], 
                descricao=i['descricao'],
                quantidade=i['quantidade'], 
                preco_unitario=i['preco_unitario'], 
                preco_total=i['preco_total'],
                id=i['id']
            ) for i in itens_rows
        ]
        
        pedido = Pedido(
            id=row['id'],
            lead_id=row['lead_id'],
            data_pedido=row['data_pedido'],
            numero_pedido=row['numero_pedido'],
            valor_total=row['valor_total'],
            status_faturamento=row['status_faturamento'],
            data_proximo_contato=row['data_proximo_contato'],
            observacoes=row['observacoes'],
            itens=itens,
            nome_loja=row['nome_loja']
        )
        conn.close()
        return pedido

    def list_by_lead(self, lead_id: int) -> List[Pedido]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        rows = c.execute("SELECT * FROM pedidos WHERE lead_id = ? ORDER BY data_pedido DESC", (lead_id,)).fetchall()
        
        pedidos = []
        for row in rows:
            pedidos.append(Pedido(
                id=row['id'],
                lead_id=row['lead_id'],
                data_pedido=row['data_pedido'],
                numero_pedido=row['numero_pedido'],
                valor_total=row['valor_total'],
                status_faturamento=row['status_faturamento'],
                data_proximo_contato=row['data_proximo_contato'],
                observacoes=row['observacoes'],
                itens=[] # Por performance, não carrega itens na listagem geral
            ))
        conn.close()
        return pedidos

    def list_all_active_clients(self) -> List[dict]:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Clientes ativos com estatísticas rápidas
        query = """
            SELECT 
                l.id, 
                l.nome_loja, 
                l.cidade, 
                l.estado, 
                l.telefone,
                COUNT(p.id) as total_pedidos,
                SUM(p.valor_total) as faturado_total,
                MAX(p.data_pedido) as ultima_compra
            FROM leads l
            JOIN pedidos p ON l.id = p.lead_id
            WHERE l.status = 'Cliente Ativo'
            GROUP BY l.id
            ORDER BY ultima_compra DESC
        """
        rows = c.execute(query).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def get_faturamento_total(self, lead_id: int) -> float:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        val = c.execute("SELECT SUM(valor_total) FROM pedidos WHERE lead_id = ?", (lead_id,)).fetchone()[0]
        conn.close()
        return val if val else 0.0
