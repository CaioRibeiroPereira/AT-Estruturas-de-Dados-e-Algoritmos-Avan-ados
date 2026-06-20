import sys
sys.stdout.reconfigure(encoding="utf-8")


#*********************************************************************************
# AUXILIAR: string com comparação lexicográfica invertida


class _InvStr:
    """
    Wrapper de string cujo < é o inverso do lexicográfico.

    Necessário para que o MinHeap de Top-K identifique como 'mínimo'
    o par (menor_peso, maior_palavra_lex), que é o candidato mais fraco
    do conjunto atual — correto para o critério de desempate pedido.

    Sem isso o heap apontaria como 'pior' a palavra lex menor (errado).
    """
    __slots__ = ("s",)
    def __init__(self, s): self.s = s
    def __lt__(self, o):   return self.s > o.s
    def __le__(self, o):   return self.s >= o.s
    def __gt__(self, o):   return self.s < o.s
    def __ge__(self, o):   return self.s <= o.s
    def __eq__(self, o):   return self.s == o.s


# **********************************************************************
# MIN-HEAP MANUAL (heapq proibido)


class MinHeap:
    def __init__(self):
        self.dados = []

    def tamanho(self):
        return len(self.dados)

    def minimo(self):
        return self.dados[0] if self.dados else None

    def inserir(self, item):
        self.dados.append(item)
        self._subir(len(self.dados) - 1)

    def remover_minimo(self):
        if not self.dados:
            return None
        self.dados[0], self.dados[-1] = self.dados[-1], self.dados[0]
        item = self.dados.pop()
        if self.dados:
            self._descer(0)
        return item

    def _subir(self, i):
        while i > 0:
            pai = (i - 1) // 2
            if self.dados[i] < self.dados[pai]:
                self.dados[i], self.dados[pai] = self.dados[pai], self.dados[i]
                i = pai
            else:
                break

    def _descer(self, i):
        n = len(self.dados)
        while True:
            menor = i
            esq, dir = 2 * i + 1, 2 * i + 2
            if esq < n and self.dados[esq] < self.dados[menor]:
                menor = esq
            if dir < n and self.dados[dir] < self.dados[menor]:
                menor = dir
            if menor == i:
                break
            self.dados[i], self.dados[menor] = self.dados[menor], self.dados[i]
            i = menor


# *************************************************************************
# TRIE


class NoTrie:
    def __init__(self):
        self.filhos      = {}
        self.fim_palavra = False
        self.peso        = 0


class BuscadorPrefixo:
    def __init__(self):
        self.raiz = NoTrie()

    def inserir_termo(self, termo: str, peso: int):
        """Percorre/cria nós para cada letra e marca o final com o peso. Custo: O(L)."""
        atual = self.raiz
        for letra in termo:
            if letra not in atual.filhos:
                atual.filhos[letra] = NoTrie()
            atual = atual.filhos[letra]

        if not atual.fim_palavra:
            atual.fim_palavra = True
            atual.peso = peso
        else:
            atual.peso = max(atual.peso, peso)

    def sugerir_top_k(self, prefixo: str, k: int) -> list:
        """
        Retorna ate K termos com o préfixo dado, ordenados por peso desc;
        empates resolvidos por ordem lexicográfica asc.

        - Localização do prefixo: O(L).
        - Seleção Top-K: DFS + MinHeap de tamanho fixo K.
          Chave no heap: ( peso, _InvStr(palavra))
          mínimo do heap = candidato mais fraco = menor peso, lex-maior em empate.
        """
        if k <= 0:
            return []

        # 1. Localiza o nó do prefixo em  O(L)
        atual = self.raiz
        for letra in prefixo:
            if letra not in atual.filhos:
                return []
            atual = atual.filhos[letra]

        # 2. DFS com min-heap de tamanho fixo K
        heap = MinHeap()

        def dfs(no, palavra):
            if no.fim_palavra:
                chave = (no.peso, _InvStr(palavra))
                if heap.tamanho() < k:
                    heap.inserir(chave)
                elif chave > heap.minimo():   # melhor que o mais fraco atual
                    heap.remover_minimo()
                    heap.inserir(chave)

            for letra, filho in no.filhos.items():
                dfs(filho, palavra + letra)

        dfs(atual, prefixo)

        # 3. Extrai, ordena e retorna só as palavras
        resultado = []
        while heap.tamanho() > 0:
            peso, inv = heap.remover_minimo()
            resultado.append((peso, inv.s))

        resultado.sort(key=lambda x: (-x[0], x[1]))
        return [palavra for _, palavra in resultado]


# ************************************************************************
# TESTE E VALIDACAO

banco_de_palavras = [
    ("teclado",      45),
    ("tecnologia",   90),
    ("tecnico",      75),
    ("tecido",       30),
    ("computacao",  100),
    ("computador",  100),   # empate intencional de peso com 'computacao'
    ("compilador",   85),
    ("complexo",     85),   # empate intencional de peso com 'compilador'
    ("componente",   60),
    ("compartilhar", 95),
    ("comunidade",   70),
    ("comunismo",    10),
    ("copo",         40),
    ("carro",        55),
]

buscador = BuscadorPrefixo()
for termo, peso in banco_de_palavras:
    buscador.inserir_termo(termo, peso)

print(buscador.sugerir_top_k("tec",  3))
print(buscador.sugerir_top_k("comp", 5))
print(buscador.sugerir_top_k("com", 10))
