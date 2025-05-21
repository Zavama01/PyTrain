from gurobipy import Model, GRB, quicksum

# Esempio di input
# Percorsi
P = [0, 1, 2]  # percorsi
C = {0: 2, 1: 2, 2: 2}  # capienza per percorso

# Passeggeri
U = [0, 1, 2, 3, 4]  # passeggeri
r = {0: 10, 1: 12, 2: 14, 3: 16, 4: 18}  # orario ideale
t = {
    (0, 0): 11, (0, 1): 13, (0, 2): 15,
    (1, 0): 12, (1, 1): 14, (1, 2): 16,
    (2, 0): 15, (2, 1): 16, (2, 2): 17,
    (3, 0): 16, (3, 1): 17, (3, 2): 19,
    (4, 0): 20, (4, 1): 21, (4, 2): 23
}  # orario di arrivo se il passeggero u prende percorso p

# Parametri
alpha = 1  # peso ritardo
beta = 5   # penalità passeggeri non serviti
k = 2      # massimo percorsi attivabili
M = 1000   # Big-M

# Modello
m = Model("Percorsi_min_ritardo")

# Variabili
y = {p: m.addVar(vtype=GRB.BINARY, name=f"y_{p}") for p in P}
x = {(u, p): m.addVar(vtype=GRB.BINARY, name=f"x_{u}_{p}") for u in U for p in P}
z = {u: m.addVar(vtype=GRB.BINARY, name=f"z_{u}") for u in U}
d = {u: m.addVar(lb=0.0, vtype=GRB.CONTINUOUS, name=f"d_{u}") for u in U}

# Vincoli
# 1. Ogni passeggero su un solo percorso o non servito
for u in U:
    m.addConstr(quicksum(x[u, p] for p in P) + z[u] == 1)

# 2. Capienza massima
for p in P:
    m.addConstr(quicksum(x[u, p] for u in U) <= C[p] * y[p])

# 3. Numero massimo di percorsi attivabili
m.addConstr(quicksum(y[p] for p in P) <= k)

# 4. Assegnazione solo su percorsi attivi
for u in U:
    for p in P:
        m.addConstr(x[u, p] <= y[p])

# 5. Definizione del ritardo
for u in U:
    for p in P:
        m.addConstr(d[u] >= t[u, p] - r[u] - M * (1 - x[u, p]))

# Obiettivo: minimizzare ritardi + penalità passeggeri non serviti
m.setObjective(quicksum(alpha * d[u] for u in U) + quicksum(beta * z[u] for u in U), GRB.MINIMIZE)

m.optimize()

# Output risultati
output = []
for p in P:
    if y[p].X > 0.5:
        assigned = [u for u in U if x[u, p].X > 0.5]
        output.append((f"Percorso {p} attivo", assigned))
not_served = [u for u in U if z[u].X > 0.5]
output.append(("Passeggeri non serviti", not_served))

output.append(("Ritardi", {u: d[u].X for u in U}))
output
