import sys
sys.stdout.reconfigure(encoding="utf-8")

# ************************************************************
# GRAFO - MAPA DA ESPANHA


CIDADES = [
    "Coruña", "Oviedo", "Vigo", "Valladolid", "Bilbao",
    "Zaragoza", "Gerona", "Barcelona", "Madrid", "Valencia",
    "Albacete", "Murcia", "Granada", "Jaen", "Sevilla",
    "Cadiz", "Badajoz",
]

# (peso_km, cidade_a, cidade_b)
ARESTAS = [
    (171, "Coruña",   "Vigo"),
    (304, "Oviedo",     "Bilbao"),
    (356, "Vigo",       "Valladolid"),
    (455, "Coruña",   "Valladolid"),
    (280, "Valladolid", "Bilbao"),
    (395, "Bilbao",     "Madrid"),
    (193, "Valladolid", "Madrid"),
    (324, "Bilbao",     "Zaragoza"),
    (325, "Zaragoza",   "Madrid"),
    (296, "Zaragoza",   "Barcelona"),
    (100, "Barcelona",  "Gerona"),
    (349, "Barcelona",  "Valencia"),
    (251, "Madrid",     "Albacete"),
    (335, "Madrid",     "Jaen"),
    (403, "Madrid",     "Badajoz"),
    (191, "Valencia",   "Albacete"),
    (241, "Valencia",   "Murcia"),
    (150, "Albacete",   "Murcia"),
    (278, "Murcia",     "Granada"),
    ( 98, "Granada",    "Jaen"),
    (242, "Jaen",       "Sevilla"),
    (125, "Sevilla",    "Cadiz"),
    (256, "Sevilla",    "Granada"),
]

# Madrid suporta até 4 conexões; demais cidades até 3
GRAU_MAX = {c: 3 for c in CIDADES}
GRAU_MAX["Madrid"] = 4


# ************************************************************************
# UNION-FIND (manual)


class UnionFind:
    def __init__(self, nos):
        self._pai  = {n: n for n in nos}
        self._rank = {n: 0 for n in nos}

    def find(self, x):
        while self._pai[x] != x:
            self._pai[x] = self._pai[self._pai[x]]   
            x = self._pai[x]
        return x

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return False
        if self._rank[rx] < self._rank[ry]:
            rx, ry = ry, rx
        self._pai[ry] = rx
        if self._rank[rx] == self._rank[ry]:
            self._rank[rx] += 1
        return True

    def same(self, x, y):
        return self.find(x) == self.find(y)

    def todos_conectados(self, nos):
        raiz = self.find(nos[0])
        return all(self.find(n) == raiz for n in nos)


#************************************************************************
# KRUSKAL COM RESTRIÇÃO DE GRAU


def kruskal_restrito(arestas, nos, grau_max):
    """
    Heurística greedy: ordena aresta por peso e adiciona cada uma se não
    forma ciclo (UnionFind) e nenhum vértice ultrapassa seu grau máximo.
    Não garante o ótimo global (DC-MST é NP-hard), mas é eficiente e correto
    para instâncias moderadas com restrições não muito severas.
    """
    ordenadas = sorted(arestas)            # ordena por (peso, u, v)
    uf    = UnionFind(nos)
    grau  = {n: 0 for n in nos}
    arvore = []

    for peso, u, v in ordenadas:
        if uf.same(u, v):
            continue                       
        if grau[u] >= grau_max.get(u, 3) or grau[v] >= grau_max.get(v, 3):
            continue                       
        uf.union(u, v)
        grau[u] += 1
        grau[v] += 1
        arvore.append((peso, u, v))

    return arvore, grau, uf


# ************************************************************************
# ANÁLISE DE RESILIÊNCIA


def _bfs_componente(arvore, excluir_u, excluir_v, inicio, nos):
    """Retorna o conjunto de nos alcançáveis a partir de 'início' na árvore
    sem a aresta (excluir_u, excluir_v  )."""
    adj = {n: [] for n in nos}
    for _, u, v in arvore:
        if (u == excluir_u and v == excluir_v) or (u == excluir_v and v == excluir_u):
            continue
        adj[u].append(v)
        adj[v].append(u)

    visitados = {inicio}
    fila = [inicio]
    while fila:
        atual = fila.pop(0)
        for viz in adj[atual]:
            if viz not in visitados:
                visitados.add(viz)
                fila.append(viz)
    return visitados


def analisar_resiliencia(arvore, todas_arestas, nos, grau, grau_max):
    """
    Para cada aresta da árvore
      1. Remove-a -> dois componentes Cu e Cv.
      2. Busca a aresta fora da árvore de menor custo que cruza o corte
         e cujo backup não viola o limite de grau de nenhuma ponta.
         (Após a falha, as pontas da aresta removida perdem 1 conexão;
          as pontas do backup ganham 1 conexão.)
      3. Calcula custo adicional = peso_backup - peso_mst.

    A aresta mais crítica é a de maior custo adicional (inf se sem backup válido).
    """
    arvore_set = {(min(u, v), max(u, v)) for _, u, v in arvore}
    nos_set    = set(nos)
    resultados = []

    for peso_mst, u_rem, v_rem in arvore:
        comp_u = _bfs_componente(arvore, u_rem, v_rem, u_rem, nos)
        comp_v = nos_set - comp_u

        melhor = None
        for peso, u, v in todas_arestas:
            if (min(u, v), max(u, v)) in arvore_set:
                continue
            cruza = (u in comp_u and v in comp_v) or (u in comp_v and v in comp_u)
            if not cruza:
                continue

            # Grau efetivo de cada ponta do backup após a falha: se a ponta dá com u_rem ou v_rem, ela já perdeu 1 conexão.
            grau_u = grau[u] - (1 if u in (u_rem, v_rem) else 0)
            grau_v = grau[v] - (1 if v in (u_rem, v_rem) else 0)

            if grau_u + 1 > grau_max.get(u, 3) or grau_v + 1 > grau_max.get(v, 3):
                continue   # backup violarie restrição de grau

            if melhor is None or peso < melhor[0]:
                melhor = (peso, u, v)

        custo_extra = (melhor[0] - peso_mst) if melhor else float('inf')
        resultados.append({
            "aresta":      (peso_mst, u_rem, v_rem),
            "backup":      melhor,
            "custo_extra": custo_extra,
        })

    # Ordena por custo_extra decrescente (inf = mais crítico)
    resultados.sort(key=lambda r: -r["custo_extra"])
    return resultados


#*************************************************************************
# IMPRESSÃO


def imprimir_mst(arvore, grau, uf):
    print("=" * 58)
    print("  ÁRVORE DE EXPANSÃO MÍNIMA  (restrição de grau)")
    print("=" * 58)

    conectada = uf.todos_conectados(CIDADES)
    n_seg     = len(arvore)
    n_esp     = len(CIDADES) - 1

    print(f"Rede totalmente conectada : {'SIM' if conectada else 'NAO'}")
    print(f"Segmentos selecionados    : {n_seg}  (esperado: {n_esp})")
    print()
    print(f"  {'#':<3} {'Segmento':<36} {'km':>5}")
    print("  " + "-" * 46)
    for i, (peso, u, v) in enumerate(arvore, 1):
        print(f"  {i:<3} {u:<18} -- {v:<16} {peso:>5}")
    print("  " + "-" * 46)
    total = sum(p for p, *_ in arvore)
    print(f"  {'Custo total':>39} {total:>5} km")

    print()
    print("Grau por cidade:")
    for c in CIDADES:
        limite = GRAU_MAX.get(c, 3)
        barra  = "*" * grau[c] + "." * (limite - grau[c])
        print(f"  {c:<14}: {grau[c]}/{limite}  [{barra}]")


def imprimir_resiliencia(resultados, custo_mst):
    print()
    print("=" * 58)
    print("  ANALISE DE RESILIÊNCIA")
    print("=" * 58)

    # Tabela completa
    print(f"  {'Aresta removida':<30} {'Backup disponivel':<28} {'Delta':>7}")
    print("  " + "-" * 67)
    for r in resultados:
        p, u, v = r["aresta"]
        seg = f"{u} -- {v} ({p})"
        if r["backup"]:
            pb, ub, vb = r["backup"]
            bk    = f"{ub} -- {vb} ({pb})"
            delta = f"+{r['custo_extra']}"
        else:
            bk    = "--- sem backup ---"
            delta = "INF"
        print(f"  {seg:<30} {bk:<28} {delta:>7}")

    # Destaque da mais critica com backup
    com_backup = [r for r in resultados if r["backup"] is not None]
    sem_backup = [r for r in resultados if r["backup"] is None]

    print()
    if sem_backup:
        print("Arestas críticas SEM backup (O rompimento isola cidades):")
        for r in sem_backup:
            p, u, v = r["aresta"]
            print(f"  - {u} -- {v} ({p} km)")

    if com_backup:
        mais = com_backup[0]
        p, u, v    = mais["aresta"]
        pb, ub, vb = mais["backup"]
        novo_custo = custo_mst - p + pb

        print()
        print("Aresta mais crítica (Que teria o maior custo de substituicao):")
        print(f"  Aresta    : {u} -- {v}  ({p} km)")
        print(f"  Backup    : {ub} -- {vb}  ({pb} km)")
        print(f"  Custo MST : {custo_mst} km")
        print(f"  Novo custo: {novo_custo} km  (delta +{mais['custo_extra']} km)")



# EXECUÇÃO
arvore, grau, uf = kruskal_restrito(ARESTAS, CIDADES, GRAU_MAX)
custo_mst        = sum(p for p, *_ in arvore)

imprimir_mst(arvore, grau, uf)

resultados = analisar_resiliencia(arvore, ARESTAS, CIDADES, grau, GRAU_MAX)
imprimir_resiliencia(resultados, custo_mst)
