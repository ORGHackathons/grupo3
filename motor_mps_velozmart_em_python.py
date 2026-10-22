"""
Projeto Final - Coding Tank: Marketplace Priority Sorter (MPS) - VelozMart
Arquitetura: Dupla Fila de Prioridade (Dual-Heap) com Peso Composto Dinâmico
"""

import heapq
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Pedido:
    id_pedido: str
    priority_score: float    # 0 a 100 (calculado por IA)
    dispatch_window: int     # Minutos restantes até o prazo expirar (SLA)
    size_category: str       # 'P', 'M' ou 'G' (espaço físico na doca)
    urgencia: float = field(init=False, default=0.0)

    def __post_init__(self):
        self.recalcular_urgencia()

    def recalcular_urgencia(self) -> float:
        """
        Calcula o Peso Composto Dinâmico:
        Urgência = (priorityScore / max(dispatchWindow, 1)) * 10 + BônusTamanho
        """
        bonus_tamanho = {"P": 15.0, "M": 5.0, "G": 0.0}
        bonus = bonus_tamanho.get(self.size_category.upper(), 0.0)

        # Evita divisão por zero caso o prazo chegue a 0 ou fique negativo
        janela_segura = max(self.dispatch_window, 1)

        self.urgencia = round((self.priority_score / janela_segura) * 10.0 + bonus, 2)
        return self.urgencia


class MarketplacePrioritySorter:
    """
    Motor de priorização em tempo real baseado em Duas Heaps (Filas de Prioridade):
    - fila_critica (Fast-Track): pedidos com dispatch_window <= 15 min
    - fila_normal (Geral): pedidos com dispatch_window > 15 min
    """

    LIMITE_CRITICO_MINUTOS = 15

    def __init__(self):
        self.fila_critica: List[tuple] = []
        self.fila_normal: List[tuple] = []
        self._contador_desempate = 0  # Garante estabilidade caso dois pedidos empatem na urgência

    def inserir_pedido(self, pedido: Pedido) -> None:
        """
        Insere um novo pedido na Heap apropriada em complexidade O(log N).
        Nota: O módulo heapq do Python é uma Min-Heap por padrão;
        multiplicamos a urgência por -1 para funcionar como Max-Heap.
        """
        pedido.recalcular_urgencia()
        self._contador_desempate += 1
        entrada_heap = (-pedido.urgencia, self._contador_desempate, pedido)

        if pedido.dispatch_window <= self.LIMITE_CRITICO_MINUTOS:
            heapq.heappush(self.fila_critica, entrada_heap)
        else:
            heapq.heappush(self.fila_normal, entrada_heap)

    def atualizar_tempo_e_repriorizar(self, minutos_decorridos: int = 5) -> int:
        """
        Simula a passagem do tempo ou mudança de SLA, recalculando a urgência
        e promovendo automaticamente pedidos da Fila Normal para a Fila Crítica.
        Retorna a quantidade de pedidos promovidos para a Fast-Track.
        """
        promovidos = 0
        nova_fila_normal = []

        # Atualiza os pedidos que já estão na Fila Crítica
        pedidos_criticos = [item[2] for item in self.fila_critica]
        self.fila_critica.clear()
        for ped in pedidos_criticos:
            ped.dispatch_window = max(0, ped.dispatch_window - minutos_decorridos)
            self.inserir_pedido(ped)

        # Atualiza a Fila Normal e promove quem entrou na zona crítica (<= 15 min)
        while self.fila_normal:
            _, _, ped = heapq.heappop(self.fila_normal)
            ped.dispatch_window = max(0, ped.dispatch_window - minutos_decorridos)
            ped.recalcular_urgencia()

            if ped.dispatch_window <= self.LIMITE_CRITICO_MINUTOS:
                promovidos += 1
                self.inserir_pedido(ped)  # Vai direto para a fila_critica
            else:
                self._contador_desempate += 1
                heapq.heappush(nova_fila_normal, (-ped.urgencia, self._contador_desempate, ped))

        self.fila_normal = nova_fila_normal
        return promovidos

    def expedir_proximo(self) -> Optional[Pedido]:
        """
        Remove e retorna o pedido de maior prioridade em O(log N).
        Sempre esvazia a Fila Crítica antes de puxar da Fila Normal.
        """
        if self.fila_critica:
            _, _, pedido = heapq.heappop(self.fila_critica)
            return pedido
        if self.fila_normal:
            _, _, pedido = heapq.heappop(self.fila_normal)
            return pedido
        return None

    def exibir_painel_doca(self, top_n: int = 5) -> None:
        """
        Exibe os Top N pedidos na tela da doca com indicadores acessíveis
        (ícones geométricos + texto, sem depender apenas de cor).
        """
        todos_criticos = sorted(self.fila_critica)
        todos_normais = sorted(self.fila_normal)
        visao_geral = todos_criticos + todos_normais

        print("=" * 78)
        print(f"{'POS':<4} | {'STATUS (ACESSÍVEL)':<18} | {'PEDIDO':<8} | {'SCORE':<6} | {'PRAZO':<8} | {'TAM':<4} | {'URGÊNCIA (U)'}")
        print("-" * 78)

        for idx, (_, _, ped) in enumerate(visao_geral[:top_n], start=1):
            if ped.dispatch_window <= self.LIMITE_CRITICO_MINUTOS:
                badge = "[!] CRÍTICO (F1)"
            elif ped.urgencia >= 40:
                badge = "[▲] ALTA (F2)"
            else:
                badge = "[●] NORMAL (F2)"

            print(
                f"#{idx:<3} | {badge:<18} | {ped.id_pedido:<8} | "
                f"{ped.priority_score:<6.0f} | {ped.dispatch_window:>3} min  | "
                f" {ped.size_category:<3} | {ped.urgencia:>8.2f} pts"
            )
        print("=" * 78 + "\n")


# =====================================================================
# SIMULAÇÃO PRÁTICA (PODE RODAR AO VIVO NA APRESENTAÇÃO!)
# =====================================================================
if __name__ == "__main__":
    mps = MarketplacePrioritySorter()

    print("\n>>> 1. CHEGADA INICIAL DE PEDIDOS NO CENTRO DE DISTRIBUIÇÃO VELOZLART:")
    lote_inicial = [
        Pedido("PED-101", priority_score=50, dispatch_window=60, size_category="G"),  # Comum, Grande, Prazo longo
        Pedido("PED-102", priority_score=95, dispatch_window=30, size_category="M"),  # VIP, Médio, Prazo médio
        Pedido("PED-103", priority_score=70, dispatch_window=25, size_category="P"),  # Bom score, Pequeno (Bônus Doca)
        Pedido("PED-104", priority_score=60, dispatch_window=10, size_category="G"),  # Prazo estourando (<=15m -> Fila Crítica!)
        Pedido("PED-105", priority_score=85, dispatch_window=18, size_category="M"),  # Quase entrando na zona crítica
    ]

    for p in lote_inicial:
        mps.inserir_pedido(p)

    mps.exibir_painel_doca(top_n=5)

    print(">>> 2. PASSARAM-SE 10 MINUTOS (RE-PRIORIZAÇÃO E PROMOÇÃO AUTOMÁTICA):")
    qtd_promovidos = mps.atualizar_tempo_e_repriorizar(minutos_decorridos=10)
    print(f"    [Evento]: {qtd_promovidos} pedido(s) atingiram <= 15 min e subiram para a Fila Crítica!\n")
    mps.exibir_painel_doca(top_n=5)

    print(">>> 3. DOCA LIVRE! CHAMANDO OS 2 PRIMEIROS PEDIDOS PARA EMBALAGEM:")
    for Ordem in range(1, 3):
        expedido = mps.expedir_proximo()
        print(f"    -> Expedido {Ordem}º: {expedido.id_pedido} (Prazo: {expedido.dispatch_window} min | Tam: {expedido.size_category} | Urgência: {expedido.urgencia} pts)")