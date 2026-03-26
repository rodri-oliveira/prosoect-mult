from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

@dataclass
class PedidoItem:
    familia: str
    codigo_produto: str
    descricao: str
    quantidade: int
    preco_unitario: float
    preco_total: float
    id: Optional[int] = None

@dataclass
class Pedido:
    id: Optional[int]
    lead_id: int
    data_pedido: str
    numero_pedido: Optional[str]
    valor_total: float
    status_faturamento: str
    data_proximo_contato: Optional[str]
    observacoes: Optional[str]
    itens: List[PedidoItem]
    nome_loja: Optional[str] = None # Para conveniência em listagens

class PedidoRepository(ABC):
    @abstractmethod
    def registrar(self, pedido: Pedido) -> int:
        pass

    @abstractmethod
    def get_by_id(self, pedido_id: int) -> Optional[Pedido]:
        pass

    @abstractmethod
    def list_by_lead(self, lead_id: int) -> List[Pedido]:
        pass

    @abstractmethod
    def list_all_active_clients(self) -> List[dict]:
        pass

    @abstractmethod
    def get_faturamento_total(self, lead_id: int) -> float:
        pass
