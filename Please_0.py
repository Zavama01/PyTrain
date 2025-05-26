from gurobipy import *
import random

# ===================
# === INPUT DATA ====
# ===================

# Percorsi (insiemi di archi consecutivi) - TODO rendi randomico
paths = {
    'A': [(0, 1), (1, 2)],
    'B': [(3, 5), (5, 7)]
}

# Tempo di percorrenza degli archi - TODO rendi randomico
w = {
    (0, 1): 5,
    (1, 2): 6,
    (3, 5): 7,
    (5, 7): 8
}

# Timetable prevista per ogni stazione (in minuti) - TODO rendi randomico
timetable = {
    0: 100,
    1: 110,
    2: 120,
    3: 130,
    5: 140,
    7: 150
}

# Intervallo accettabile per il prelievo passeggeri (+10 minuti)
pickup_window = {s: (timetable[s], timetable[s] + 10) for s in timetable}

# Passeggeri associati a stazioni di partenza

num_passengers = 50
passenger_arcs = [random.choice(list(w.keys())) for _ in range(num_passengers)]
Ps = {s: sum(1 for arc in passenger_arcs if arc[0] == s) for s in range(8)}

# Capacità massima per arco
capMax = 120

# ======================
# === MODELLO GUROBI ===
# ======================

model = Model("Path_Selection")

# Variabile binaria: 1 se scelgo il percorso P
Z = model.addVars(paths.keys(), vtype=GRB.BINARY, name="Z")

# Orari di arrivo alle stazioni
arrival_time = model.addVars(range(8), vtype=GRB.CONTINUOUS, name="arrival_time")

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

# Capacità su ogni tratta: passeggeri che passano non devono superare capMax
# ========================
# === VINCOLI DI CAPACITÀ ===
# ========================

# Mappa arco -> lista di passeggeri che lo usano
arc_to_passengers = {arc: [] for arc in w}
for i, arc in enumerate(passenger_arcs):
    arc_to_passengers[arc].append(i)

# Per ogni arco, somma dei passeggeri che lo usano non supera capMax
for arc, pax_ids in arc_to_passengers.items():
    # Controlla se l’arco è in qualche percorso (altrimenti salta)
    relevant_paths = [p for p in paths if arc in paths[p]]
    if relevant_paths:
        # Se l'arco è presente in un percorso p e Z[p] = 1, vincolo attivo
        model.addConstr(
            quicksum(x[i] for i in pax_ids) <= capMax * quicksum(Z[p] for p in relevant_paths),
            name=f"cap_{arc}"
        )
# Qui andrebbe verificato quanti passeggeri prendono quella tratta

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

if model.status == GRB.OPTIMAL:
    print("\n=== RISULTATO OTTIMALE ===")

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
