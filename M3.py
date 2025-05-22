from gurobipy import *

# Parametri di esempio
N = [0, 1, 2]  # Nodi
A = [(0, 1), (1, 2)]  # Archi (grafo diretto)

w = {(0, 1): 5, (1, 2): 6}  # Tempi di percorrenza
r = {0: 0, 1: 10, 2: 20}    # Orari ideali
P = {0: 100, 1: 80, 2: 0}   # Passeggeri al nodo
C = 120                     # Capacità massima
rho = 2                    # Penalità per passeggero non servito

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
    print(f"Arco {i}->{j}: passeggeri = {y[i,j].X:.1f}")
