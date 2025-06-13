import itertools
from typing import Dict, Tuple, List
from gurobipy import *
import random

# ogni percorso ha un valore preimpostato (budget del percorso)
# Variabile budget = valore
# Vincolo su passeggeri num_pax_served >= valore minimo
# Funzione Obbiettivo - calcolo ritardi

# 70% passeggeri totali o 70% passwggeri dei percorsi scelti?

# ===================
# === INPUT DATA ====
# ===================

# Percorsi (insiemi di archi consecutivi)
paths = {
    'C': [(1, 4), (4, 5), (5, 6), (6, 7)],
    'D': [(1, 2), (2, 3), (3, 4), (4, 5), (5, 6), (6, 7)]
}

# costo del percorso (in termini di budget)
paths_cost = {
    'C': 200,
    'D': 200
}

budget = 220


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
    w[arco] = random.randint(1, 3)

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
num_passengers = 1
# passenger_arcs = [random.choice(list(w.keys())) for _ in range(num_passengers)]
passenger_arcs = [(2, 5)]
Ps = {s: sum(1 for arc in passenger_arcs if arc[0] == s) for s in
      range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1)}

# Capacità massima per arco
capMax = 10

# ======================
# === MODELLO GUROBI ===
# ======================

model = Model("Path_Selection")

# Variabile binaria: 1 se scelgo il percorso P, 0 altrimenti
Z = model.addVars(paths.keys(), vtype=GRB.BINARY, name="Z")

# Orari di arrivo alle stazioni
arrival_time = model.addVars(range(1, max(n for arcs in paths.values() for arc in arcs for n in arc) + 1),
                             vtype=GRB.CONTINUOUS, name="arrival_time")

# ========================
# === VARIABILI PASSEGGERI SERVITI ===
# ========================

# Passeggeri serviti
passeggeri_serviti = model.addVar(vtype=GRB.INTEGER, name="pax_served")
x = model.addVars(num_passengers, vtype=GRB.BINARY, name="x")  # 1 se pax i è servito

# ======================
# === VINCOLI =====
# ======================

model.addConstr(Z['D'] == 1) # todo da rimuovere

# Vincolo per ogni passeggero: può essere servito solo se arco è nel percorso e orario è ok
M = 1e4  # Big M per disattivare vincoli se non necessario

for i, arc in enumerate(passenger_arcs):
    u, v = arc
    for p in paths:
        # Ottieni la lista ordinata dei nodi nel percorso p
        path_nodes = [paths[p][0][0]] + [v_ for (_, v_) in paths[p]]

        # Controlla se u e v sono nel percorso, e se u viene prima di v
        if u in path_nodes and v in path_nodes and path_nodes.index(u) < path_nodes.index(v):
            window_start, window_end = pickup_window.get(u, (0, 1e5))

            # Vincoli sulla finestra temporale per l'origine u (soft con Big-M)
            model.addConstr(arrival_time[u] >= window_start - (1 - Z[p]) * M, name=f"window_start_{i}_{p}")
            model.addConstr(arrival_time[u] <= window_end + (1 - Z[p]) * M, name=f"window_end_{i}_{p}")

            # Il passeggero può essere servito solo se il percorso p è attivo
            model.addConstr(x[i] <= Z[p], name=f"x_vs_Z_{i}_{p}")

# todo vincolo disattivato perchè è stato aggiunto il vincolo del budget che limita i percorsi selezionabili
# Solo uno dei percorsi può essere scelto
# model.addConstr(quicksum(Z[p] for p in paths) <= 2, name="max_one_path")


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

# Mappa arco -> lista di passeggeri che lo usano
arc_to_passengers = {arc: [] for arc in w}
for i, arc in enumerate(passenger_arcs):
    arc_to_passengers[arc].append(i)

# Pre-calcola i nodi presenti in ogni percorso
path_nodes = {p: set(n for arc in paths[p] for n in arc) for p in paths}

# VINCOLI DI CAPACITÀ
# Capacità su ogni tratta: passeggeri che passano non devono superare capMax
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

# Numero minimo di passeggeri che vanno serviti (70% del totale)
model.addConstr(passeggeri_serviti >= 0.7 * num_passengers, name="min_pax_served")

# vincolo di budget sui percorsi scelti
model.addConstr(
    quicksum(paths_cost[p] * Z[p] for p in paths_cost) <= budget,
    name="budget_constraint"
)

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
    print("Nessuna soluzione ottimale trovata.")

# Supponiamo che Z[p].X > 0.5 solo per il percorso attivo
active_path = [p for p in Z if Z[p].X > 0.5][0]
active_arcs = set(paths[active_path])  # contiene tuple (u, v)
for i, (u, v) in enumerate(passenger_arcs):
    if x[i].X < 0.5:
        if (u, v) not in active_arcs:
            print(f"❌ Passeggero {i} su arco ({u}, {v}) – direzione NON compatibile con percorso {active_path}")
        else:
            print(f"✅ Passeggero {i} su arco ({u}, {v}) – direzione compatibile")



