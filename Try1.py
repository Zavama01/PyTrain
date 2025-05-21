from gurobipy import Model, GRB, quicksum

# ------------------------------
# SET
# ------------------------------
R = [0, 1]              # Candidate routes
T = list(range(10))     # Time points
Te = list(range(10))    # Extended time points
S = [0, 1, 2]           # Stations

# ------------------------------
# PARAMETRI
# ------------------------------
W = 3
R_max = 1
μ = 4
ζ = 40
f_min = 1
f_max = 3
M = 10
ρ = 10

# Domanda passeggeri
φ = {(t, s, u): 2 for t in Te for s in S for u in S if s != u}
ν = {(r, s, u): 1 for r in R for s in S for u in S}
κ = {s: 1 for s in S}
x = {(r, s): 1 for r in R for s in S}  # fixed stop pattern

# ------------------------------
# MODELLO
# ------------------------------
model = Model("RST_Model")

# ------------------------------
# VARIABILI
# ------------------------------
z = model.addVars(R, vtype=GRB.BINARY, name="z")
d_plus = model.addVars(R, T, vtype=GRB.BINARY, name="d_plus")
d_minus = model.addVars(R, T, vtype=GRB.BINARY, name="d_minus")
e_plus = model.addVars(R, vtype=GRB.INTEGER, lb=0, name="e_plus")
e_minus = model.addVars(R, vtype=GRB.INTEGER, lb=0, name="e_minus")
b = model.addVars(R, Te, S, S, vtype=GRB.CONTINUOUS, name="b")
w = model.addVars(Te, S, S, vtype=GRB.CONTINUOUS, name="w")
l = model.addVars(Te, S, S, vtype=GRB.CONTINUOUS, name="l")

# ------------------------------
# FUNZIONE OBIETTIVO (2a)
# ------------------------------
model.setObjective(
    quicksum(w[t, s, u] for t in Te for s in S for u in S if s != u) +
    quicksum(b[r, t, s, u] * ν[r, s, u] for r in R for t in Te for s in S for u in S if s != u) +
    quicksum(ρ * l[t, s, u] for t in Te for s in S for u in S if s != u),
    GRB.MINIMIZE
)

# ------------------------------
# VINCOLI
# ------------------------------

# (2b) Numero massimo di rotte
model.addConstr(quicksum(z[r] for r in R) <= R_max, "2b")

# (2c) Esattamente una rotta selezionata
model.addConstr(quicksum(z[r] for r in R) == 1, "2c")

# (2d)
model.addConstr(quicksum(e_plus[r] + e_minus[r] for r in R) <= μ, "2d")

# (2e)
for r in R:
    model.addConstr(e_plus[r] + e_minus[r] <= M * z[r], f"2e_{r}")

# (2h, 2i)
for r in R:
    model.addConstr(quicksum(d_plus[r, t] for t in T) <= f_max, f"2h_{r}_max")
    model.addConstr(quicksum(d_plus[r, t] for t in T) >= f_min, f"2h_{r}_min")
    model.addConstr(quicksum(d_minus[r, t] for t in T) <= f_max, f"2i_{r}_max")
    model.addConstr(quicksum(d_minus[r, t] for t in T) >= f_min, f"2i_{r}_min")

# (2j, 2k)
for r in R:
    for t in Te:
        for s in S:
            for u in S:
                if s != u:
                    model.addConstr(b[r, t, s, u] <= x[r, s] * ζ, f"2j_{r}_{t}_{s}_{u}")
                    model.addConstr(b[r, t, s, u] <= x[r, u] * ζ, f"2k_{r}_{t}_{s}_{u}")


# Correttivo per metodo addConstr
if t - 1 in Te:
    lhs = φ.get((t, s, u), 0) + w[t - 1, s, u]
else:
    lhs = 0  # oppure gp.LinExpr(0) se vuoi essere esplicito

#  model.addConstr(
#                     φ.get((t, s, u), 0) + w[t - 1, s, u] if t - 1 in Te else 0 ==
#                     quicksum(b[r, t, s, u] for r in R) + w[t, s, u] + l[t, s, u],
#                     f"2n_{t}_{s}_{u}"
#                 )

# (2n)
for t in Te:
    for s in S:
        for u in S:
            if s != u:
                model.addConstr(
                    lhs == quicksum(b[r, t, s, u] for r in R) + w[t, s, u] + l[t, s, u],
                    f"2n_{t}_{s}_{u}"
                )

# (2o)
for t in Te:
    for s in S:
        for u in S:
            if s != u:
                model.addConstr(
                    w[t, s, u] <= quicksum(φ[i, s, u] for i in range(max(0, t - W + 1), t + 1)),
                    f"2o_{t}_{s}_{u}"
                )

# (2p, 2q): Già rispettati tramite i domini delle variabili

# ------------------------------
# RISOLUZIONE
# ------------------------------
model.optimize()

# ------------------------------
# RISULTATI
# ------------------------------
if model.status == GRB.OPTIMAL:
    print(f"\nSoluzione Ottimale = {model.ObjVal}\n")
    for r in R:
        if z[r].x > 0.5:
            print(f"Rotta {r} selezionata:")
            for t in T:
                print(f"  t={t}: d_plus={d_plus[r, t].x}, d_minus={d_minus[r, t].x}")
else:
    print("Nessuna soluzione ottimale trovata.")
