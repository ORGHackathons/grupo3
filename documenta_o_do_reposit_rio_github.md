# 📦 Marketplace Priority Sorter (MPS) — VelozMart

> **Projeto Final – Coding Tank (Ordenação e Prioridade)**  
> Solução de priorização dinâmica em tempo real para expedição logística do VelozMart.

---

## 🎯 1. O Problema

Os centros de distribuição do **VelozMart** enfrentam atrasos críticos de SLA e gargalos físicos nas docas de embalagem ao utilizarem filas tradicionais baseadas apenas na ordem de chegada (FIFO) ou prazo simples. Essa abordagem ignora o valor estratégico do pedido (`priorityScore`), a janela restante até o vencimento (`dispatchWindow`) e o impacto físico nas bancadas (`sizeCategory`: P, M, G). Como resultado, pedidos VIP sofrem atrasos evitáveis enquanto caixas grandes ("G") travam a vazão da expedição, exigindo um motor que ordene e re-enfileire pedidos em tempo real.

---

## ⚙️ 2. Algoritmo e Estrutura de Dados

### Arquitetura Escolhida: **Dual-Heap (Fast-Track + Fila Normal) com Peso Composto Dinâmico**

Unificamos os múltiplos critérios em um **Índice de Urgência ($U$)** contínuo e estruturamos o armazenamento em **duas Max-Heaps (Filas de Prioridade)**:

$$\text{Urgência } (U) = \left( \frac{\text{priorityScore}}{\max(\text{dispatchWindow}, 1)} \right) \times 10 + \text{BônusTamanho}$$

* **Bônus de Tamanho (`sizeCategory`):** `P = +15 pts` | `M = +5 pts` | `G = 0 pts` (prioriza o giro rápido na doca para liberar espaço físico e aumentar o *throughput*).
* **Fila 1 — Heap Crítica (`Fast-Track`):** Recebe automaticamente qualquer pedido com `dispatchWindow <= 15 min`. Sempre é esvaziada primeiro, garantindo **Zero Starvation** (nenhum pedido expira esquecido na fila).
* **Fila 2 — Heap Normal:** Armazena pedidos com `dispatchWindow > 15 min` ordenados pela Urgência ($U$). Quando o tempo avança e um pedido atinge $\le 15\text{ min}$, ele é promovido para a Fila 1.

---

## 📊 3. Diagrama da Arquitetura (Alto Contraste)

```mermaid
flowchart LR
    classDef entrada fill:#0f172a,stroke:#fb923c,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef critica fill:#7f1d1d,stroke:#f87171,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef normal fill:#1e3a8a,stroke:#60a5fa,stroke-width:2px,color:#ffffff,font-weight:bold;
    classDef doca fill:#064e3b,stroke:#34d399,stroke-width:2px,color:#ffffff,font-weight:bold;

    A["1. NOVO PEDIDO / MUDANÇA SLA<br/>Calcula Urgência U"]:::entrada --> B{"dispatchWindow<br/> <= 15 min?"}:::entrada
    B -- "SIM" --> C["FILA 1: HEAP CRÍTICA<br/>Inserção O(log N)"]:::critica
    B -- "NÃO" --> D["FILA 2: HEAP NORMAL<br/>Inserção O(log N)"]:::normal
    D -. "Promove quando <= 15m" .-> C
    C -- "1º Prioridade Máxima" --> E["3. DOCA DE EMBALAGEM<br/>Extrai Topo O(log N)"]:::doca
    D -. "2º Se Fila 1 vazia" .-> E
```

---

## ⚖️ 4. Mapa de Trade-offs e Métricas

| Tipo | Ponto Analisado | Impacto na Operação VelozMart |
| :--- | :--- | :--- |
| ✅ **PRÓ 1** | **Desempenho $O(\log N)$** | Inserir ou remover entre 100.000 pedidos exige apenas ~17 operações, contra ~1.6 milhão de um `Array.sort()` ($O(N \log N)$). |
| ✅ **PRÓ 2** | **Prevenção de *Starvation*** | A promoção automática aos 15 minutos impede que pacotes `G` ou de score baixo fiquem presos eternamente. |
| ✅ **PRÓ 3** | **Manutenibilidade Simples** | Utiliza a biblioteca nativa `heapq` sem necessidade de estruturas manuais complexas. |
| ⚠️ **CONTRA 1** | **Calibração dos Bônus** | Exige ajuste empírico dos bônus (`+15`/`+5`/`0`) para equilibrar vazão de doca vs. SLA. |
| ⚠️ **CONTRA 2** | **Rotina de Promoção (Tick)** | Requer verificação periódica (a cada 1 minuto) para promover pedidos que atingiram 15 minutos restantes. |
| ⚠️ **CONTRA 3** | **Memória Dupla** | Manter duas Heaps consome levemente mais memória RAM — embora continue $O(N)$ — do que uma fila única. |

### Métricas de Comprovação (vs. Ordenação Simples por Tempo)
1. **Redução do Custo Ponderado de SLA Violado:** Protege pedidos de alto `priorityScore` durante picos de saturação.
2. **Aumento de Throughput (Pedidos/Hora):** O bônus para pacotes `P` evita o bloqueio físico das bancadas.
3. **Validação por Teste A/B:** Comparação direta entre duas linhas de embalagem durante 14 dias.

---

## 🚀 5. Próximos Passos & Bônus de UI

* **Acessibilidade na UI da Doca:** Uso de ícones geométricos + texto (`[!] CRÍTICO`, `[▲] ALTA`, `[●] NORMAL`) para operadores daltônicos e congelamento visual dos **Top 5 pedidos por 30 segundos** (*Anti-Jitter*) para evitar cliques errados.
* **Aprendizagem Online (*Reinforcement Learning*):** Ajuste dinâmico do bônus de tamanho conforme o sensor de ocupação física da doca em tempo real.
* **Batching Logístico:** Bônus adicional para pedidos que pertencem ao mesmo caminhão/CEP prestes a fechar manifesto.

---

## 💻 Como Executar a Simulação em Python

```bash
python mps_velozmart.py
```