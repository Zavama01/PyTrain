from gurobipy import *
from datetime import datetime, timedelta
import random
import itertools

# Parametri di esempio
# Percorsi in input, (stazioni ordinate per cui passano i mezzi di trasporto)
fermate_1 = [1, 4, 5, 6]
fermate_2 = [1, 3, 4, 6, 7]
fermate_3 = [1, 2, 3, 4, 5, 6, 7]
percorsi_validi = [fermate_1, fermate_2, fermate_3]

# Sceglie un percorso casuale - ovviamente non dovrebbe essere così, ma dovrebbe essere deciso dipendentemente dall'output
N = random.choice(percorsi_validi)  # Nodi

y = len(N)  # numero di stazioni - presupposizione

# Supponiamo di chiamare le stazioni "S1", "S2", ..., "S7"
#TODO stazioni = [f"S{N[j]}" for j in range(y)]

# Genera tutte le combinazioni non ordinate di 2 nodi
A = list(itertools.combinations(N, 2))  # Archi (grafo diretto)

# Genera un tempo random per ciascuna coppia
w = {}  # Tempi di percorrenza
for (nodo1, nodo2) in A:
    # ore = 0
    minuti = random.randint(10, 30)  # da 0 a 20 minuti
    w[(nodo1, nodo2)] = minuti

r = {i: random.randint(0, 60) for i in N}

# Funzione per formattare in hh:mm
def minutes_to_time(m):
    h = m // 60
    mm = m % 60
    return f"{h:02d}:{mm:02d}"

# Stampa
print("Orari ideali generati:")
for i in N:
    print(f"Nodo {i}: orario ideale = {minutes_to_time(r[i])} ({r[i]} min)")


# Passenger demand (cioè il quantitativo di passeggeri ad ogni stazione)
# Genera valori random tra 0 e 200 per ogni stazione - presupposizione
P = {s: random.randint(0, 200) for s in N}  # Passeggeri al nodo

C = 120  # Capacità massima

rho = 2  # Penalità per passeggero non servito

m = Model("Minimize_Ritardo")

# Variabili
x = {i: m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"x_{i}") for i in N}
d = {i: m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"d_{i}") for i in N}
u = {i: m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f"u_{i}") for i in N}
y = {(i, j): m.addVar(lb=0, ub=C, vtype=GRB.CONTINUOUS, name=f"y_{i}_{j}") for (i, j) in A}

# Vincoli
for i in N:
    m.addConstr(d[i] >= x[i] - r[i], name=f"ritardo_{i}")
    m.addConstr(quicksum(y[i, j] for j in N if (i, j) in A) + u[i] == P[i], name=f"passeggeri_serviti_{i}")

for (i, j) in A:
    m.addConstr(x[j] >= x[i] + w[i, j], name=f"tempo_{i}_{j}")

# Obiettivo: minimizzare somma ritardi + penalità passeggeri non serviti
m.setObjective(
    quicksum(d[i] for i in N) + rho * quicksum(u[i] for i in N),
    GRB.MINIMIZE
)

m.optimize()

# Output
for i in N:
    print(f"Nodo {i}: orario = {x[i].X:.1f}, ritardo = {d[i].X:.1f}, non serviti = {u[i].X:.1f}")
for (i, j) in A:
    print(f"Arco {i}->{j}: passeggeri = {y[i, j].X:.1f}")
