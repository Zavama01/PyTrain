import itertools
from typing import Dict, Tuple, List
from gurobipy import *
import random

# il budget serve solo a limitare la scelta ad un percorso che rispetta il vincolo di budget dato che si può scegliere un solo percorso
# capMax è uguale per tutti

# ===================
# === INPUT DATA ====
# ===================

# Percorsi (insiemi di archi consecutivi)
paths = {
    'A': [(1, 2), (2, 4), (4, 5), (5, 6), (6, 7)],
    'B': [(1, 3), (3, 4), (4, 5), (5, 6), (6, 7)],
    'C': [(1, 4), (4, 5), (5, 6), (6, 7)],
    'D': [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
}

# costo del percorso (in termini di budget)
paths_cost = {
    'A': 200,
    'B': 220,
    'C': 190,
    'D': 700
}

capMax = 20

budget = 500

# Lista di nodi
nodi: List[int] = list(
    range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1))  # da 1 a ultima stazione inclusi
# Crea tutti gli archi i < j
archi: List[Tuple[int, int]] = list(itertools.combinations(nodi, 2))

# Tempo di percorrenza degli archi
# Dizionario dei pesi associati agli archi
w: Dict[Tuple[int, int], int] = {}

# Assegna un valore randomico (es: tra 5 e 15 minuti) a ogni arco
for arco in archi:
    w[arco] = random.randint(5, 7)

# Timetable prevista per ogni stazione (in minuti)
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
num_passengers = 100

passenger_arcs = [random.choice(list(w.keys())) for _ in range(num_passengers)]

Ps = {s: sum(1 for arc in passenger_arcs if arc[0] == s) for s in
      range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1)}

# ======================
# === MODELLO GUROBI ===
# ======================

model = Model("Path_Selection")

# Variabile binaria: 1 se scelgo il percorso P, 0 altrimenti
Z = model.addVars(paths.keys(), vtype=GRB.BINARY, name="Z")

# Orari di arrivo alle stazioni
arrival_time = model.addVars(range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1),
                             vtype=GRB.CONTINUOUS, name="arrival_time")

# Passeggeri serviti
passeggeri_serviti = model.addVar(vtype=GRB.INTEGER, name="pax_served")  # todo
x = model.addVars(num_passengers, vtype=GRB.BINARY, name="x")  # 1 se pax i è servito

# ======================
# === VINCOLI =====
# ======================

# Pre-calcola i nodi presenti in ogni percorso
path_nodes = {p: set(n for arc in paths[p] for n in arc) for p in paths}

# Vincolo per ogni passeggero: può essere servito solo se arco è nel percorso e orario è ok
M = 1e4  # Big M per disattivare vincoli se non necessario

for i, arc in enumerate(passenger_arcs):
    u, v = arc
    relevant_paths = [p for p in paths if u in path_nodes[p] and v in path_nodes[p]]
    for p in paths:
        # Controlla se u e v sono nel percorso p
        if relevant_paths:
            window_start, window_end = pickup_window.get(u, (0, 1e4))

            # Vincoli sulla finestra temporale per l'origine u (soft con Big-M)
            model.addConstr(arrival_time[u] >= window_start - (1 - Z[p]) * M, name=f"window_start_{i}_{p}")
            model.addConstr(arrival_time[u] <= window_end + (1 - Z[p]) * M, name=f"window_end_{i}_{p}")

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

# Genera una lista ordinata di stazioni per ogni percorso
# Per ogni passeggero calcoliamo origine e destinazione
# Origin: min tra i due nodi dell'arco; Destination: max (ipotesi che i passeggeri vadano "avanti")
origin = [min(u, v) for u, v in passenger_arcs]
destination = [max(u, v) for u, v in passenger_arcs]
station_lists = {}

for p, arcs in paths.items():
    # Costruzione della lista stazioni per ogni percorso p
    station_list = [arcs[0][0]]
    for (u, v) in arcs:
        if station_list[-1] == u:
            station_list.append(v)
        elif station_list[-1] == v:
            station_list.append(u)
        else:
            raise ValueError(f"Inconsistenza negli archi del percorso {p}: ({u}, {v})")
    station_lists[p] = station_list

    # Per ogni tratta consecutiva nel percorso p
    for idx in range(len(station_list) - 1):
        u = station_list[idx]
        v = station_list[idx + 1]

        # Passeggeri a bordo tra u e v
        pax_on_segment = [
            i for i in range(num_passengers)
            if min(origin[i], destination[i]) <= u < max(origin[i], destination[i])
        ]

        # Vincolo di capacità sulla tratta (u, v) per percorso p
        model.addConstr(
            quicksum(x[i] for i in pax_on_segment) <= capMax,
            name=f"capacity_segment_{p}_{u}_{v}"
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

# serve solo a semplificare la leggibilità della funzione obbiettivo
model.addConstr(passeggeri_serviti == quicksum(x[i] for i in range(num_passengers)), name="pax_served_sum")

# Numero minimo di passeggeri che vanno serviti (70% del totale)
model.addConstr(passeggeri_serviti >= 0.7 * num_passengers, name="min_pax_served")

# vincolo di budget sui percorsi scelti
model.addConstr(
    quicksum(paths_cost[p] * Z[p] for p in paths_cost) <= budget,
    name="budget_constraint"
)



# Solo uno dei percorsi può essere scelto
model.addConstr(quicksum(Z[p] for p in paths) <= 1, name="max_one_path")
# ======================
# === FUNZIONE OBIETTIVO ===
# ======================

# Minimizzare ritardo + massimizzare passeggeri serviti
ritardi = []
for p, arcs in paths.items():
    visited = []
    for (u, v) in arcs:
        if u not in visited:
            visited.append(u)
        if v not in visited:
            visited.append(v)

    for u in visited:
        ritardi.append((arrival_time[u] - timetable[u]) * Z[p])

model.setObjective(passeggeri_serviti, GRB.MAXIMIZE)

# ======================
# === RISOLUZIONE ===
# ======================

model.optimize()

# ======================
# === OUTPUT ===========
# ======================

print("======================")
print(passenger_arcs)
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

    # Tabella con orari e ritardi per ciascun percorso selezionato
    print("\nOrari e ritardi alle fermate per ciascun percorso selezionato:")
    print(f"{'Percorso':<10} {'Stazione':<10} {'Timetable':<12} {'Arrivo Calcolato':<18} {'Ritardo (min)'}")

    for p in paths:
        if Z[p].X > 0.5:
            nodes_in_path = set(n for arc in paths[p] for n in arc)
            for s in sorted(nodes_in_path):
                if s in timetable:
                    t_input = timetable[s]
                    t_arrival = arrival_time[s].X
                    ritardo = t_arrival - t_input
                    print(f"{p:<10} {s:<10} {t_input:<12.1f} {t_arrival:<18.1f} {ritardo:.1f}")

    print("\nPasseggeri serviti (indice e arco):")
    for i, xi in enumerate(x.values()):
        if xi.X > 0.5:
            print(f"Passeggero {i} su arco {passenger_arcs[i]}")
else:

    print("\n❌ Modello INFEASIBILE. Calcolo dell'IIS per identificare i vincoli responsabili...\n")
    model.computeIIS()

    print("Vincoli che causano l'infeasibilità:\n")
    for c in model.getConstrs():
        if c.IISConstr:
            print(f" - {c.ConstrName}")

    print("\nVariabili coinvolte:\n")
    for v in model.getVars():
        if v.IISLB or v.IISUB:
            bounds = []
            if v.IISLB:
                bounds.append("LB")
            if v.IISUB:
                bounds.append("UB")
            if v.IISFixed:
                bounds.append("Fixed")
            print(f" - {v.VarName} (bounds: {', '.join(bounds)})")

    # Scrivi il modello IIS su file per ispezione manuale
    model.write("model.ilp")  # Puoi aprirlo con un editor di testo
    print("File LP e ILP scritti con successo.")
