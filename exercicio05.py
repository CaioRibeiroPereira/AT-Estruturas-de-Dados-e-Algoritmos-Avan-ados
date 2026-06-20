import heapq
import math
import sys

sys.stdout.reconfigure(encoding="utf-8")

# ********************************************************
# DADOS DO PROBLEMA


TURN_START = 0  # 09:00 como t = 0 minutos

DELIVERIES = [
    ("Copacabana", 10, 45, 4),
    ("Ipanema",    25, 75, 5),
    ("Tijuca",     15, 60, 3),
    ("Madureira",  60, 130, 3),
    ("Jacarepagua", 80, 150, 2),
    ("Botafogo",   20, 70, 2),
]

HUBS = ["Centro", "Barra"]

URGENCIA_K    = 60   # folga abaixo desse  começa a penalizar
URGENCIA_PESO = 4    # quanto cada minuto de urgência desconta no score


# ***************************************************************
# UTILITÁRIOS


def minutos_para_hora(t):
    """Converte minutos desde 09:00 para HH:MM."""
    return f"{9 + t // 60:02d}:{t % 60:02d}"


def formatar_caminho(path):
    return " -> ".join(path) if path else "sem caminho"


# ***************************************************************
# GRAFO DIRECIONADO PONDERADO


def construir_grafo():
    """Constrói o grafo como lista de adjacencia ponderada."""
    vertices = [
        "Centro", "Barra", "Botafogo", "Copacabana",
        "Ipanema", "Tijuca", "Madureira", "Jacarepagua",
    ]
    grafo = {v: [] for v in vertices}
    arestas = [
        ("Centro",      "Botafogo",    18),
        ("Centro",      "Tijuca",      16),
        ("Centro",      "Madureira",   34),
        ("Botafogo",    "Copacabana",  10),
        ("Botafogo",    "Ipanema",     14),
        ("Botafogo",    "Centro",      20),
        ("Copacabana",  "Ipanema",      9),
        ("Copacabana",  "Botafogo",    12),
        ("Copacabana",  "Centro",      28),
        ("Ipanema",     "Copacabana",  10),
        ("Ipanema",     "Botafogo",    16),
        ("Ipanema",     "Barra",       30),
        ("Tijuca",      "Centro",      18),
        ("Tijuca",      "Madureira",   26),
        ("Tijuca",      "Botafogo",    22),
        ("Madureira",   "Tijuca",      30),
        ("Madureira",   "Centro",      35),
        ("Madureira",   "Jacarepagua", 28),
        ("Jacarepagua", "Barra",       18),
        ("Jacarepagua", "Madureira",   26),
        ("Barra",       "Jacarepagua", 16),
        ("Barra",       "Ipanema",     32),
        ("Barra",       "Centro",      40),
    ]
    for u, v, w in arestas:
        grafo[u].append((v, w))
    return grafo


# ***************************************************************
# DIJKSTRA


def dijkstra(grafo, origem):
    """
    Dijkstra para pesos positivos.
    Retorna (dist, prev):
      dist[ v ] = menor custo de origem até v
      prev[v] = predecessor de v no menor caminho
    """
    dist = {v: math.inf for v in grafo}
    prev = {v: None for v in grafo}
    dist[origem] = 0
    heap = [(0, origem)]

    while heap:
        custo, u = heapq.heappop(heap)
        if custo > dist[u]:
            continue
        for v, peso in grafo[u]:
            novo = custo + peso
            if novo < dist[v]:
                dist[v] = novo
                prev[v] = u
                heapq.heappush(heap, (novo, v))

    return dist, prev


def reconstruir_caminho(prev, origem, destino):
    """Retorna lista de vértices do caminho, ou none se não existe."""
    if origem == destino:
        return [origem]
    caminho, atual = [], destino
    while atual is not None:
        caminho.append(atual)
        if atual == origem:
            break
        atual = prev[atual]
    caminho.reverse()
    return caminho if caminho and caminho[0] == origem else None


# ****************************************************************
# PRÉ-PROCESSAMENTO DOS MENORES CAMINHOS


def preprocessar(grafo, pontos):
    """Executa Dijkstra a partir de cada ponto"""
    all_dist, all_prev = {}, {}
    for origem in pontos:
        all_dist[origem], all_prev[origem] = dijkstra(grafo, origem)
    return all_dist, all_prev


def travel_cost(u, v, all_dist, all_prev):
    """
    Retorna (custo, caminho) entre u e v.
    Se não houve caminho, retorna (math.inf, None).
    """
    custo = all_dist.get(u, {}).get(v, math.inf)
    if math.isinf(custo):
        return math.inf, None
    return custo, reconstruir_caminho(all_prev[u], u, v)


# ***************************************************************
# ESCOLHA DO HUB INICIAL


def escolher_hub(grafo, deliveries):
    """
    Escolhe o hub com menor soma de menores custos até todos os bairros.
    Retorna (hub_escolhido, hub: soma).
    """
    bairros = [b for b, *_ in deliveries]
    somas = {}
    for hub in HUBS:
        dist, _ = dijkstra(grafo, hub)
        somas[hub] = sum(dist[b] for b in bairros)
    return min(somas, key=somas.get), somas


# *********************************************************************
# HEURÍSTICA GULOSA COM HEAP


def _score(t, local, entrega, all_dist, all_prev):
    """
    Calcula score e detalhes de uma entrega a partir do local em t.
    Retorna none se inalcançável.

    Fórmula:
      score = 100*atraso + 4*custo - 15*prioridade + espera

    Chave de desempate (heap mínima):
      (score, atraso, custo, -prioridade, janela_fim, bairro)
    Garante ordem única: menor atraso > menor custo > maior prio >
    menor janela_fim > ordem alfabética do bairro.
    """
    bairro, j_ini, j_fim, prio = entrega
    custo, caminho = travel_cost(local, bairro, all_dist, all_prev)
    if math.isinf(custo):
        return None

    chegada_bruta = t + custo
    espera    = max(0, j_ini - chegada_bruta)
    t_entrega = chegada_bruta + espera
    atraso    = max(0, t_entrega - j_fim)
    folga     = j_fim - chegada_bruta          # negativo se já vai chegar tarde
    urgencia  = max(0, URGENCIA_K - folga) * URGENCIA_PESO
    score     = 100 * atraso + 4 * custo - 15 * prio + espera - urgencia

    return {
        "chave":         (score, atraso, custo, -prio, j_fim, bairro),
        "bairro":        bairro,
        "j_ini":         j_ini,
        "j_fim":         j_fim,
        "prio":          prio,
        "custo":         custo,
        "caminho":       caminho,
        "chegada_bruta": chegada_bruta,
        "espera":        espera,
        "t_entrega":     t_entrega,
        "atraso":        atraso,
    }


def executar_rota_gulosa(grafo, hub_inicial, deliveries, all_dist, all_prev):
    """
    Heurística gulosa: a cada passo seleciona via heap a entrega com
    melhor score, atualiza t com deslocamento + espera e repete.
    Ao final retorna ao hub mais barato.
    """
    t        = TURN_START
    local    = hub_inicial
    pendentes = list(deliveries)
    rota     = [hub_inicial]
    log      = []

    while pendentes:
        # Monta heap com todas as entregas pendentes 
        heap = []
        for entrega in pendentes:
            info = _score(t, local, entrega, all_dist, all_prev)
            if info:
                heapq.heappush(heap, (info["chave"], info, entrega))

        if not heap:
            raise RuntimeError(f"Entregas pendentes inalcançáveis a partir de {local}.")

        _, info, entrega_sel = heapq.heappop(heap)

        t_antes = t
        t       = info["t_entrega"]
        status  = "NO PRAZO" if info["atraso"] == 0 else f"FORA DA JANELA (+{info['atraso']} min)"

        if info["caminho"] and len(info["caminho"]) > 1:
            rota.extend(info["caminho"][1:])
        elif local != info["bairro"]:
            rota.append(info["bairro"])

        log.append({**info, "t_antes": t_antes, "t_depois": t,
                    "status": status, "origem": local})
        local = info["bairro"]
        pendentes.remove(entrega_sel)

    # Retorno ao hub mais barato
    hub_final, custo_ret, cam_ret = None, math.inf, None
    for hub in HUBS:
        c, cam = travel_cost(local, hub, all_dist, all_prev)
        if c < custo_ret:
            custo_ret, hub_final, cam_ret = c, hub, cam

    if math.isinf(custo_ret):
        raise RuntimeError("Sem caminho de retorno a nenhum hub.")

    t_ret = t
    t    += custo_ret
    if cam_ret and len(cam_ret) > 1:
        rota.extend(cam_ret[1:])
    elif local != hub_final:
        rota.append(hub_final)

    return {
        "hub_inicial":  hub_inicial,
        "hub_final":    hub_final,
        "rota":         rota,
        "tempo_total":  t,
        "log":          log,
        "retorno": {
            "origem":   local,
            "hub":      hub_final,
            "custo":    custo_ret,
            "caminho":  cam_ret,
            "t_antes":  t_ret,
            "t_depois": t,
        },
    }


# **************************************************************
# IMPRESSÃO
#

def imprimir_adjacencia(grafo):
    print("=== CONSULTAS DE ADJACÊNCIA ===")
    for no in ("Centro", "Madureira"):
        print(f'\nVizinhos de "{no}":')
        for v, w in grafo[no]:
            print(f"  {no} -> {v} ({w})")
    print()


def imprimir_hub(hub, somas):
    print("=== ESCOLHA DO HUB INICIAL ===")
    print("Soma dos menores custos até os bairros de entrega:")
    for h, s in somas.items():
        tag = "  <-- escolhido" if h == hub else ""
        print(f"  {h}: {s if not math.isinf(s) else 'INF'}{tag}")
    print(f"\nHub inicial: {hub}")
    print("Critério: menor soma de custos mínimos para todos os destinos.\n")


def imprimir_abordagem_caminhos(pontos):
    """
    Tarefa 2b: justificativa impressa para a escolha de Dijkstra
    em vez de Floyd-Warshall.
    """
    k = len(pontos)
    V, E = 8, 23
    custo_dijkstra   = k * (V + E) * (V.bit_length())   # k × O((V+E) log V)
    custo_floyd      = V ** 3    # O(V^3)
    print("=== ABORDAGEM: MENORES CAMINHOS ===")
    print(f"Pontos relevantes ({k}): {', '.join(pontos)}")
    print(
        f"\nEscolha: {k} execuções de Dijkstra (uma por ponto relevante)."
        f"\n"
        f"\nComparativo de custo estimado:"
        f"\n  Dijkstra x{k}:     {k} x O((V+E) log V) = {k} x O(({V}+{E}) x {V.bit_length()}) ~ {custo_dijkstra} ops"
        f"\n  Floyd-Warshall: O(V^3) = {custo_floyd} ops"
        f"\n"
        f"\nJustificativa:"
        f"\n  - Custos similares para este grafo pequeno."
        f"\n  - Dijkstra é preferido por trabalhar naturalmente com grafos"
        f"\n    esparsos (E={E} << V^2={V**2}) e por dispensar uma matriz V×V"
        f"\n    auxiliar: apenas os {k} pares realmente consultados são"
        f"\n    pré-computados, tornando a solução facilmente escalável."
        f"\n  - Número de consultas necessárias: até {k}^2={k**2} pares,"
        f"\n    todos cobertos pelo pré-processamento."
    )
    print()


def imprimir_matriz(pontos, all_dist):
    print("=== CUSTOS ENTRE PONTOS RELEVANTES ===")
    cab = ["Orig\\Dest"] + pontos
    print(" | ".join(f"{c:>13}" for c in cab))
    for u in pontos:
        linha = [f"{u:>13}"]
        for v in pontos:
            c = all_dist[u][v]
            linha.append(f"{'INF':>13}" if math.isinf(c) else f"{int(c):>13}")
        print(" | ".join(linha))
    print()


def imprimir_score_formula():
    """Tarefa 3a: documenta a fórmula do score e a regra de desempate."""
    print("=== FÓRMULA DO SCORE (heurística gulosa) ===")
    print(
        "Para cada entrega pendente no instante t a partir do local atual:"
        "\n"
        "\n  chegada_bruta = t + custo_viagem"
        "\n  espera        = max(0, janela_inicio - chegada_bruta)"
        "\n  t_entrega     = chegada_bruta + espera"
        "\n  atraso        = max(0, t_entrega - janela_fim)"
        "\n  folga         = janela_fim - chegada_bruta        # negativo se já vai atrasar"
        f"\n  urgência      = max(0, {URGENCIA_K} - folga) x {URGENCIA_PESO}  # alto quando a janela é curta"
        "\n"
        "\n  score = 100 * atraso          # penaliza atraso já confirmado"
        "\n        +   4 * custo_viagem    # penaliza deslocamento longo"
        "\n        -  15 * prioridade      # bonifica entregas urgentes"
        "\n        +   1 * espera          # penaliza espera desnecessária"
        "\n        -   urgência            # antecipa urgência antes do atraso acontecer"
        "\n"
        "\n  Menor score => melhor decisão (heap mínima)."
        "\n"
        "\nRegra de desempate determinisca (tupla ordenável):"
        "\n  (score, atraso, custo, -prioridade, janela_fim, bairro)"
        "\n  Critérios em ordem: menor atraso > menor custo >"
        "\n  maior prioridade > menor janela_fim > ordem alfabética do bairro."
    )
    print()


def imprimir_log(relatorio):
    print("=== LOG DE EXECUÇÃO ===")
    for i, item in enumerate(relatorio["log"], 1):
        print(
            f"[{i}] {item['bairro']:<13} | "
            f"de {item['origem']:<13} -> {item['bairro']:<13} | "
            f"rota: {formatar_caminho(item['caminho']):<40} | "
            f"janela=[{item['j_ini']:>3},{item['j_fim']:>3}] | "
            f"t_antes={item['t_antes']:>3} ({minutos_para_hora(item['t_antes'])}) | "
            f"viagem={item['custo']:>3} | espera={item['espera']:>3} | "
            f"t_depois={item['t_depois']:>3} ({minutos_para_hora(item['t_depois'])}) | "
            f"{item['status']}"
        )
    r = relatorio["retorno"]
    print(
        f"\n[RET] {r['hub']:<13} | "
        f"de {r['origem']:<13} -> {r['hub']:<13} | "
        f"rota: {formatar_caminho(r['caminho']):<40} | "
        f"viagem={r['custo']:>3} | "
        f"t_antes={r['t_antes']:>3} ({minutos_para_hora(r['t_antes'])}) | "
        f"t_depois={r['t_depois']:>3} ({minutos_para_hora(r['t_depois'])})"
    )
    print()


def imprimir_relatorio(relatorio):
    print("=== RELATÓRIO FINAL ===")
    print(f"Hub inicial : {relatorio['hub_inicial']}")
    print(f"Hub final   : {relatorio['hub_final']}")
    print(f"Rota        : {' -> '.join(relatorio['rota'])}")
    print(
        f"Tempo total : {relatorio['tempo_total']} min "
        f"(término {minutos_para_hora(relatorio['tempo_total'])})"
    )

    print("\nEntregas realizadas:")
    fora = []
    for item in relatorio["log"]:
        s = "NO PRAZO" if item["atraso"] == 0 else f"ATRASO +{item['atraso']} min"
        print(
            f"  {item['bairro']:<13}: chegada {item['t_depois']:>3} min "
            f"({minutos_para_hora(item['t_depois'])}), "
            f"janela=[{item['j_ini']},{item['j_fim']}], "
            f"prio={item['prio']} -> {s}"
        )
        if item["atraso"] > 0:
            fora.append(item)

    print("\nEntregas fora da janela:")
    if not fora:
        print("  Nenhuma.")
    else:
        for item in fora:
            print(
                f"  {item['bairro']}: chegada {item['t_depois']} min "
                f"({minutos_para_hora(item['t_depois'])}), "
                f"janela_fim={item['j_fim']}, atraso={item['atraso']} min"
            )
    print()


def imprimir_justificativa():
    print("=== JUSTIFICATIVA TÉCNICA ===")
    print(
        "1) NP-difícil:\n"
        "   O problema é uma variante do VRPTW / TSP com janelas de tempo.\n"
        "   Decidir a ordem ótima de n entregas exige explorar n! permutações\n"
        "   no pior caso, crescimento fatorial impossível de resolver em tempo\n"
        "   polinomial (a menos que P = NP).\n"
    )
    print(
        "2) Heurística aceitável:\n"
        "   A escolha gulosa usa critérios locais relevantes (prioridade, custo\n"
        "   de deslocamento, risco de janela) e produz soluções viáveis em\n"
        "   O(n^2 log n), adequado para decisão em tempo real na logística.\n"
    )
    print(
        "3) Determinismo em empates:\n"
        "   A chave da heap é a tupla\n"
        "       (score, atraso, custo, -prioridade, janela_fim, bairro)\n"
        "   Como 'bairro' é único por entrega, nenhum comparador de desempate\n"
        "   chegará ao dicionário de detalhes, garantindo reprodutibilidade total.\n"
    )


#******************************************************************
# MAIN

def main():
    grafo = construir_grafo()
    imprimir_adjacencia(grafo)

    hub_inicial, somas = escolher_hub(grafo, DELIVERIES)
    imprimir_hub(hub_inicial, somas)

    pontos = sorted({hub_inicial, "Centro", "Barra"} | {b for b, *_ in DELIVERIES})
    all_dist, all_prev = preprocessar(grafo, pontos)
    imprimir_abordagem_caminhos(pontos)
    imprimir_matriz(pontos, all_dist)

    imprimir_score_formula()
    relatorio = executar_rota_gulosa(grafo, hub_inicial, DELIVERIES, all_dist, all_prev)

    imprimir_log(relatorio)
    imprimir_relatorio(relatorio)
    imprimir_justificativa()


if __name__ == "__main__":
    main()
