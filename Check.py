import itertools
from typing import Dict, Tuple, List
from gurobipy import *
import random

# ===================
# === INPUT DATA ====
# ===================

# Percorsi (insiemi di archi consecutivi) - TODO rendi randomico
paths = {
    'A': [(1, 2), (2, 4)],
    'B': [(1, 3), (3, 4)]
}

# Tempo di percorrenza degli archi
# Lista di nodi
nodi: List[int] = list(range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1))  # da 1 a ultima stazione inclusi
# Crea tutti gli archi i < j
archi: List[Tuple[int, int]] = list(itertools.combinations(nodi, 2))
# Dizionario dei pesi associati agli archi
w: Dict[Tuple[int, int], int] = {}

# Assegna un valore randomico (es: tra 10 e 120 minuti) a ogni arco
for arco in archi:
    w[arco] = random.randint(5, 15)

# TODO inserire controllo che verifica che i tempi di percorrenza w siano >= all'intervallo di tempo che c'è fra 2 stazioni della timetable
# TODO questo perchè attualmente è possibile arrivare in anticipo

# Timetable prevista per ogni stazione (in minuti) - TODO rendi randomico
timetable = {
    1: 100,
    2: 110,
    3: 120,
    4: 130,
    5: 140,
    6: 150,
    7: 160,
}

# Intervallo accettabile per il prelievo passeggeri (+10 minuti)
pickup_window = {s: (timetable[s], timetable[s] + 10) for s in timetable}

# Passeggeri associati a stazioni di partenza
num_passengers = 10
passenger_arcs = [random.choice(list(w.keys())) for _ in range(num_passengers)]
Ps = {s: sum(1 for arc in passenger_arcs if arc[0] == s) for s in range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1)}

# Capacità massima per arco
capMax = 2

# ======================
# === MODELLO GUROBI ===
# ======================

model = Model("Path_Selection")

# Variabile binaria: 1 se scelgo il percorso P, 0 altrimenti
Z = model.addVars(paths.keys(), vtype=GRB.BINARY, name="Z")

# Orari di arrivo alle stazioni
arrival_time = model.addVars(range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1), vtype=GRB.CONTINUOUS, name="arrival_time")

# ========================
# === VARIABILI PASSEGGERI SERVITI ===
# ========================

# Passeggeri serviti
passeggeri_serviti = model.addVar(vtype=GRB.INTEGER, name="pax_served")
x = model.addVars(num_passengers, vtype=GRB.BINARY, name="x")  # 1 se pax i è servito

# ======================
# === VINCOLI =====
# ======================

# Vincolo per ogni passeggero: può essere servito solo se arco è nel percorso e orario è ok
M = 1e4  # Big M per disattivare vincoli se non necessario

for i, arc in enumerate(passenger_arcs):
    u, v = arc
    for p in paths:
        if arc in paths[p]:
            window_start, window_end = pickup_window.get(u, (0, 1e5))
            # Orario all’origine entro finestra (soft enforcement con Big-M)
            model.addConstr(arrival_time[u] >= window_start - (1 - Z[p]) * M, name=f"window_start_{i}_{p}")
            model.addConstr(arrival_time[u] <= window_end + (1 - Z[p]) * M, name=f"window_end_{i}_{p}")
            # Il passeggero può essere servito solo se percorso p è scelto
            model.addConstr(x[i] <= Z[p], name=f"x_vs_Z_{i}_{p}")

# Solo uno dei percorsi può essere scelto
model.addConstr(quicksum(Z[p] for p in paths) <= 1, name="max_one_path")

# Orari di arrivo nei nodi (solo se il percorso è scelto)
for p, arcs in paths.items():
    for i, (u, v) in enumerate(arcs):
        if i == 0:
            model.addConstr(
                arrival_time[u] >= timetable[u] * Z[p], name=f"start_time_{p}_{u}"
            )
        model.addConstr(
            arrival_time[v] >= arrival_time[u] + w[(u, v)] + 5 - (1 - Z[p]) * 1e5,
            name=f"time_progression_{p}_{u}_{v}"
        )


# ========================
# === VINCOLI PASSEGGERI & CAPACITÀ ===
# ========================
# Capacità su ogni tratta: passeggeri che passano non devono superare capMax

# Mappa arco -> lista di passeggeri che lo usano
arc_to_passengers = {arc: [] for arc in w}
for i, arc in enumerate(passenger_arcs):
    arc_to_passengers[arc].append(i)

# Pre-calcola i nodi presenti in ogni percorso
path_nodes = {p: set(n for arc in paths[p] for n in arc) for p in paths}

# VINCOLI DI CAPACITÀ
for arc, pax_ids in arc_to_passengers.items():
    u, v = arc
    # Trova i percorsi che contengono entrambi i nodi u e v (anche indirettamente)
    relevant_paths = [p for p in paths if u in path_nodes[p] and v in path_nodes[p]]

    if relevant_paths:
        model.addConstr(
            quicksum(x[i] for i in pax_ids) <= capMax * quicksum(Z[p] for p in relevant_paths),
            name=f"cap_{arc}"
        )

# VINCOLI DI SERVIZIO PASSEGGERI
for i, arc in enumerate(passenger_arcs):
    u, v = arc
    relevant_paths = [p for p in paths if u in path_nodes[p] and v in path_nodes[p]]

    if relevant_paths:
        window_start, window_end = pickup_window.get(u, (0, 1e5))

        for p in relevant_paths:
            model.addConstr(
                arrival_time[u] >= window_start - (1 - Z[p]) * M,
                name=f"pax_{i}_window_start_{p}"
            )
            model.addConstr(
                arrival_time[u] <= window_end + (1 - Z[p]) * M,
                name=f"pax_{i}_window_end_{p}"
            )

        # Il passeggero può essere servito solo se almeno uno dei percorsi validi è attivo
        model.addConstr(
            x[i] <= quicksum(Z[p] for p in relevant_paths),
            name=f"x_path_check_{i}"
        )
    else:
        # Se l'arco non è compatibile con alcun percorso, il passeggero non può essere servito
        model.addConstr(x[i] == 0, name=f"x_invalid_arc_{i}")

model.addConstr(passeggeri_serviti == quicksum(x[i] for i in range(num_passengers)), name="pax_served_sum")

# ======================
# === FUNZIONE OBIETTIVO ===
# ======================

# Minimizzare ritardo + massimizzare passeggeri serviti
ritardi = []
for p, arcs in paths.items():
    for (u, _) in arcs:
        ritardi.append((arrival_time[u] - timetable[u]) * Z[p])

model.setObjective(
    quicksum(ritardi) * 0.5 - passeggeri_serviti,  # Peso ritardo e peso pax possono essere tarati
    GRB.MINIMIZE
)

# ======================
# === RISOLUZIONE ===
# ======================

model.optimize()

# ======================
# === OUTPUT ===========
# ======================

print("======================")
print(arc_to_passengers.items())
print("======================")

if model.status == GRB.OPTIMAL:
    print("\n=== RISULTATO OTTIMALE ===")
    print("Valore della funzione obiettivo:", model.ObjVal)

    # Percorso scelto
    selected_path = None
    for p in paths:
        if Z[p].X > 0.5:
            selected_path = p
            print(f"\nPercorso scelto: {p} -> {paths[p]}")

    # Passeggeri serviti
    print(f"\nPasseggeri serviti: {int(passeggeri_serviti.X)}")

    # Tabella con orari e ritardi
    print("\nOrari e ritardi alle fermate:")
    print(f"{'Stazione':<10} {'Timetable':<12} {'Arrivo Calcolato':<18} {'Ritardo (min)'}")

    for s in sorted(timetable):
        if selected_path and any(s in arc for arc in paths[selected_path]):
            t_input = timetable[s]
            t_arrival = arrival_time[s].X
            ritardo = max(0, t_arrival - t_input)
            print(f"{s:<10} {t_input:<12.1f} {t_arrival:<18.1f} {ritardo:.1f}")
else:
    print("Nessuna soluzione ottimale trovata.")

print("\nPasseggeri serviti (indice e arco):")
for i, xi in enumerate(x.values()):
    if xi.X > 0.5:
        print(f"Passeggero {i} su arco {passenger_arcs[i]}")
