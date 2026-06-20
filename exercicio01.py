import sys
sys.stdout.reconfigure(encoding="utf-8")


# ************************************
# HEAP MINIMA MANUAL (heapq proibido)

class MinHeap:
    """
    Heap minima sobre lista de tuplas (prioridade, id_tarefa, tempo, tecnologia).
    Ordenada pelo primeiro campo; os demais são usados para desempate.
    """ 

    def __init__(self):
        self._data = []

    def push(self, prioridade, id_tarefa, tempo, tecnologia):
        data = self._data
        data.append((prioridade, id_tarefa, tempo, tecnologia))
        i = len(data) - 1
        while i > 0:
            pai = (i - 1) >> 1
            if data[pai][0] > data[i][0]:
                data[pai], data[i] = data[i], data[pai]
                i = pai
            else:
                break

    def pop(self):
        data = self._data
        if not data:
            raise IndexError("heap vazia")
        data[0], data[-1] = data[-1], data[0]
        item = data.pop()
        if data:
            i, n = 0, len(data)
            while True:
                menor = i
                esq = 2 * i + 1
                dir = esq + 1
                if esq < n and data[esq][0] < data[menor][0]:
                    menor = esq
                if dir < n and data[dir][0] < data[menor][0]:
                    menor = dir
                if menor == i:
                    break
                data[i], data[menor] = data[menor], data[i]
                i = menor
        return item

    def peek(self):
        if not self._data:
            raise IndexError("heap vazia")
        return self._data[0]

    def _sift_up(self, i):
        """Sobe o elemento em i enquanto menor que o pai."""
        data = self._data
        while i > 0:
            pai = (i - 1) >> 1
            if data[pai][0] > data[i][0]:
                data[pai], data[i] = data[i], data[pai]
                i = pai
            else:
                break

    def _sift_down(self, i):
        """Desce o elemento em i enquanto maior que algum filho."""
        data = self._data
        n = len(data)
        while True:
            menor = i
            esq = 2 * i + 1
            dir = esq + 1
            if esq < n and data[esq][0] < data[menor][0]:
                menor = esq
            if dir < n and data[dir][0] < data[menor][0]:
                menor = dir
            if menor == i:
                break
            data[i], data[menor] = data[menor], data[i]
            i = menor

    def _swap(self, i, j):
        self._data[i], self._data[j] = self._data[j], self._data[i]

    def __len__(self):
        return len(self._data)

    def __bool__(self):
        return bool(self._data)


# *****************************************
# AGENDADOR OTIMIZADO


class AgendadorOtimizado:
    """
    Escolhe sempre o próxima tarefa com menor Tempo virtual de conclusão:

        mesma tecnologia : prioridade = tempo
        tech diferente   : prioridade = tempo + penalidade_setup

    Como a tecnologia ativa muda a cada execução, as prioridades ficam
    desatualizadas. Em vez de reconstrui a heap inteira (caro), usa-se
    Lazy Evaluation:

      - Inserir com prioridade mínima possível (tempo, sem penalidade).
      - Ao fazer pop(), recalcular a prioridade correta para o contexto atual.
      - Se divergiu: reinsere com o valor correto e tenta o próximo elemento.
      - Se bateu: executa a tarefa,

    Custo amortizado: cada elemento é corrigido no máximo uma vez por mudança
    de contexto, mantendo o comportamento O(n log n) na prática.
    """

    def __init__(self, track_history: bool = True):
        self._heap = MinHeap()
        self._historico = []
        self._track = track_history
        self.ultima_tech: str | None = None

    def adicionar_tarefa(self, id_tarefa: str, tempo: int, tecnologia: str):
        """Insere com prioridade otimista = tempo ( sem penalidade)."""
        self._heap.push(tempo, id_tarefa, tempo, sys.intern(tecnologia))

    def executar_proxima(self, tecnologia_atual: str, penalidade: int,
                         verbose: bool = False) -> str:
        """
        Remove e retorna o id da melhor tarefa para o contexto atual.

        tecnologia_atual : tecnologia em execução no servidor neste momento (None para o primeiro turno, sem penalidade).
        penalidade: custo fixo de troca de tecnologia (minutos).
        verbose : se True vai imprimir cada correção lazy.

        Atualiza o estado interno após a execução.
        Retorna None se a heap estiver vazia.
        """
        # Acesso direto ao array interno para eliminar overhead de chamada de método no loop crítico. A corretude do MinHeap não é afetada.
        data = self._heap._data
        heap = self._heap

        while data:
            # --- pop inline ---
            data[0], data[-1] = data[-1], data[0]
            prio_stored, id_tarefa, tempo, tecnologia = data.pop()
            if data:
                i, n = 0, len(data)
                while True:
                    menor = i
                    esq = 2 * i + 1
                    dir = esq + 1
                    if esq < n and data[esq][0] < data[menor][0]:
                        menor = esq
                    if dir < n and data[dir][0] < data[menor][0]:
                        menor = dir
                    if menor == i:
                        break
                    data[i], data[menor] = data[menor], data[i]
                    i = menor
            # ---

            # Prioridade correta para o contexto atual
            if tecnologia_atual is None or tecnologia is tecnologia_atual:
                prio_correta = tempo
            else:
                prio_correta = tempo + penalidade

            if prio_stored != prio_correta:
                # Entrada desatualizada: reinsere com prioridade corrigida
                if verbose:
                    print(
                        f"    [lazy] {id_tarefa}: stored={prio_stored} "
                        f"!= correto={prio_correta} -> reinsere"
                    )
                # --- push inline ---
                data.append((prio_correta, id_tarefa, tempo, tecnologia))
                j = len(data) - 1
                while j > 0:
                    pai = (j - 1) >> 1
                    if data[pai][0] > data[j][0]:
                        data[pai], data[j] = data[j], data[pai]
                        j = pai
                    else:
                        break
                # ---
                continue

            # Prioridade valida:   registra e retorna
            houve_setup = tecnologia_atual is not None and tecnologia is not tecnologia_atual
            self.ultima_tech = tecnologia
            if self._track:
                self._historico.append({
                    "id":         id_tarefa,
                    "tempo":      tempo,
                    "tecnologia": tecnologia,
                    "setup":      houve_setup,
                    "penalidade": penalidade if houve_setup else 0,
                })
            return id_tarefa

        return None

    def relatorio(self):
        if not self._historico:
            print("Nenhuma tarefa executada.")
            return

        print("================= RELATORIO FINAL ================-=======")
        print(f"{'#':<4} {'ID':<6} {'Tecnologia':<12} {'Exec':>5} {'Setup':>5} {'Penal':>6}")
        print("-" * 44)

        tech_ant = None
        for i, h in enumerate(self._historico, 1):
            sep = "  -- troca" if h["setup"] else ""
            print(
                f"{i:<4} {h['id']:<6} {h['tecnologia']:<12} "
                f"{h['tempo']:>5} {'SIM' if h['setup'] else 'não':>5} "
                f"{h['penalidade']:>6}{sep}"
            )
            tech_ant = h["tecnologia"]

        trocas  = sum(1 for h in self._historico if h["setup"])
        t_exec  = sum(h["tempo"] for h in self._historico)
        t_penal = sum(h["penalidade"] for h in self._historico)

        print("-" * 44)
        print(f"Trocas de tecnologia : {trocas}")
        print(f"Tempo de execução    : {t_exec} min")
        print(f"Penalidades totais   : {t_penal} min")
        print(f"Tempo total          : {t_exec + t_penal} min")


# ***********************************************
# TESTE E VALIDACAO


tarefas_iniciais = [
    ("T1", 15, "Python"),
    ("T2",  8, "Java"),
    ("T3", 22, "Docker"),
    ("T4",  5, "Java"),
    ("T5", 12, "Python"),
    ("T6", 18, "Docker"),
    ("T7",  4, "C++"),
]

PENALIDADE = 10

agendador = AgendadorOtimizado()
for id_t, tempo, tech in tarefas_iniciais:
    agendador.adicionar_tarefa(id_t, tempo, tech)

print("=========================-== EXECUCAO PASSO A PASSO =============================")
print(f"Penalidade de setup: {PENALIDADE} min\n")

tech_atual = None
for passo in range(len(tarefas_iniciais)):
    print(f"Passo {passo + 1}  (tech_atual={tech_atual})")
    id_t = agendador.executar_proxima(tech_atual, PENALIDADE, verbose=True)
    if id_t is None:
        break
    ult = agendador._historico[-1]
    status = f"SETUP +{ult['penalidade']} min" if ult["setup"] else "sem setup"
    print(f"    => {id_t}  tech={ult['tecnologia']}  exec={ult['tempo']} min  [{status}]")
    tech_atual = ult["tecnologia"]
    print()

agendador.relatorio()


# ***********************************************
# TESTE DE PERFORMANCE — 50 000 itens em < 0,5 s


import time
import random

def teste_performance(n=50_000, limite=0.5):
    print(f"\n=== TESTE DE PERFORMANCE ({n} itens, limite={limite}s) ===")

    techs = ["Python", "Java", "Docker", "C++"]
    random.seed(42)

    tarefas = [(f"T{i}", random.randint(1, 300), random.choice(techs)) for i in range(n)]

    ag = AgendadorOtimizado(track_history=False)
    for id_t, tempo, tech in tarefas:
        ag.adicionar_tarefa(id_t, tempo, tech)

    inicio = time.perf_counter()

    tech_atual = None
    executadas = 0
    for _ in range(n):
        id_t = ag.executar_proxima(tech_atual, 10)
        if id_t is None:
            break
        tech_atual = ag.ultima_tech  
        executadas += 1

    elapsed = time.perf_counter() - inicio

    print(f"Tempo decorrido  : {elapsed:.4f}s")
    print(f"Tarefas exec.    : {executadas}/{n}")

    if elapsed < limite:
        print(f"PASSOU: {elapsed:.4f}s < {limite}s")
    else:
        print(f"FALHOU: {elapsed:.4f}s >= {limite}s")

    return elapsed < limite

teste_performance()
