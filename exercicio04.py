from collections import deque



# GRAFO DE DEPENDÊNCIA DE MICROSSERVIÇOS
# Formato: 'Serviço': ['Serviços downstream afetados pela falha']

rede_microsservicos = {
    "Auth": ["Gateway", "Billing"],
    "Gateway": ["Frontend", "MobileApp"],
    "Billing": ["Notification", "Analytics"],
    "Frontend": ["CacheUI"],
    "MobileApp": ["CacheUI", "Logger"],
    "Notification": ["Logger"],
    "Analytics": [],
    "CacheUI": [],
    "Logger": []
}


#*****************************************************
# BFS - MAPEAR RAIO DE FALHA


def mapear_raio_falha_bfs(grafo, no_inicial):
    """
    Realiza  busca em largura (BFS) a partir do nó inicial
    e retorna a ordem de visitação dos serviços afetados.

    A BFS visita os nós por camadas:
     distância 0: nó inicial
     distância 1: dependentes diretos
     distância 2: dependentes dos dependentes
     etc.
    """
    if no_inicial not in grafo:
        return []

    visitados = set()
    fila = deque()
    ordem_visita = []

    visitados.add(no_inicial)
    fila.append(no_inicial)

    while fila:
        atual = fila.popleft()
        ordem_visita.append(atual)

        for vizinho in grafo[atual]:
            if vizinho not in visitados:
                visitados.add(vizinho)
                fila.append(vizinho)

    return ordem_visita


# ****************************************************************
# DFS - ENCONTRAR CADEIA PROFUNDA ANTES DO PRIMEIRO BACKTRACK


def encontrar_cadeia_profunda_dfs(grafo, no_inicial):
    """
    Retorna o caminho linear contínuo mais longo seguido por uma DFS
    antes de acontecer o primeiro backtrack.

    Estratégia:
     começa no no_inicial
     sempre segue o primeiro vizinho ainda não visitado
     para quando não houver mais vizinhos não visitado

    Isso representa a cadeia profunda inicial da DFS.
    """
    if no_inicial not in grafo:
        return []

    visitados = set()
    caminho = []

    atual = no_inicial

    while True:
        visitados.add(atual)
        caminho.append(atual)

        proximo = None
        for vizinho in grafo[atual]:
            if vizinho not in visitados:
                proximo = vizinho
                break

        if proximo is None:
            break

        atual = proximo

    return caminho


#************************************************************************
# FUNÇÕES AUXILIARES PARA EXIBIÇÃO

def imprimir_grafo(grafo):
    print("=== GRAFO DE MICROSSERVICOS ===")
    for servico, dependentes in grafo.items():
        print(f"{servico} -> {dependentes}")
    print()


def imprimir_resultado_bfs(grafo, no_inicial):
    ordem_bfs = mapear_raio_falha_bfs(grafo, no_inicial)

    print("=== ORDEM DE MITIGAÇÃO IMEDIATA (BFS) ===")
    print(f"Microsserviço afetado inicialmente: {no_inicial}")
    print("Ordem de visitação BFS:")
    print(" -> ".join(ordem_bfs))
    print()

    print("Explicação por raio de falha:")
    distancias = calcular_niveis_bfs(grafo, no_inicial)

    niveis = {}
    for no, dist in distancias.items():
        niveis.setdefault(dist, []).append(no)

    for nivel in sorted(niveis.keys()):
        print(f"Distância {nivel}: {niveis[nivel]}")
    print()


def imprimir_resultado_dfs(grafo, no_inicial):
    cadeia_dfs = encontrar_cadeia_profunda_dfs(grafo, no_inicial)

    print("=== CAMINHO CRÍTICO DE DEPENDÊNCIA (DFS) ===")
    print(f"Microsserviço afetado inicialmente: {no_inicial}")
    print("Cadeia profunda antes do primeiro backtrack:")
    print(" -> ".join(cadeia_dfs))
    print()


def calcular_niveis_bfs(grafo, no_inicial):
    """
    Função auxiliar para mostrar as distâncias/níveis da BFS.
    """
    distancias = {}
    fila = deque()

    distancias[no_inicial] = 0
    fila.append(no_inicial)

    while fila:
        atual = fila.popleft()

        for vizinho in grafo[atual]:
            if vizinho not in distancias:
                distancias[vizinho] = distancias[atual] + 1
                fila.append(vizinho)

    return distancias


# ****************************************************************

def main():
    no_inicial = "Auth"

    imprimir_grafo(rede_microsservicos)
    imprimir_resultado_bfs(rede_microsservicos, no_inicial)
    imprimir_resultado_dfs(rede_microsservicos, no_inicial)


if __name__ == "__main__":
    main()