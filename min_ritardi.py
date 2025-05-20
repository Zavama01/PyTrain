from gurobipy import Model, GRB

# Esempio input
T = {0: 5, 1: 6, 2: 4, 3: 5}
r = {0: 10, 1: 12, 2: 14, 3: 16}  # orari ideali
direzione = {0: 'A', 1: 'B', 2: 'A', 3: 'B'}
treni = T.keys()
H = 120
B = 10000

# Modello
m = Model("ritardi_treni")

x = {i: m.addVar(lb=0, ub=H, vtype=GRB.CONTINUOUS, name=f"x_{i}") for i in treni}
d = {i: m.addVar(lb=0, ub=H, vtype=GRB.CONTINUOUS, name=f"d_{i}") for i in treni}
o = {(i, j): m.addVar(vtype=GRB.BINARY, name=f"o_{i}_{j}")
     for i in treni for j in treni if i < j and direzione[i] != direzione[j]}

delta = {i: m.addVar(vtype=GRB.BINARY, name=f"delta_{i}") for i in treni}
M = 10000  # Costante grand

# Vincoli: ritardo ≥ x_i - r_i
for i in treni:
    m.addConstr(d[i] >= x[i] - r[i])
    m.addConstr(d[i] <= M * delta[i])  # Attiva d[i] solo se c'è ritardo
    m.addConstr(x[i] - r[i] <= M * delta[i])  # delta[i] = 0 forza x[i] <= r[i]
    m.addConstr(x[i] >= r[i])  # Vincolo: un treno non può partire prima dell'orario previsto

# Vincoli: conflitti tra treni opposti
for i in treni:
    for j in treni:
        if i < j and direzione[i] != direzione[j]:
            m.addConstr(x[i] + T[i] <= x[j] + B * (1 - o[i, j]))
            m.addConstr(x[j] + T[j] <= x[i] + B * o[i, j])

# Obiettivo: minimizzare somma dei ritardi
m.setObjective(sum(d[i] for i in treni), GRB.MINIMIZE)
m.optimize()

dTot = 0
for i in treni:
    dTot = d[i].X + dTot

print(f"ritardoTotale = {dTot:.2f}")

# Output
for i in treni:
    print(f"Treno {i}: ritardo = {d[i].X:.2f}, inizio = {x[i].X:.2f}, orario ideale = {r[i]}")

