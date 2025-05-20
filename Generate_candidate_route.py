import gurobipy as gp
from gurobipy import GRB

# Dati di input
Ss = [1, 2, 3, 4, 5, 6, 7]  # tutte le stazioni
Sc = [1, 7]                 # stazioni terminali
Sm = [2, 3, 5, 6]           # stazioni minori
M = [1, 4, 7]               # stazioni maggiori
S = list(set(Ss + Sc + Sm))
L = len(Ss)
Vs_value = {s: 1 for s in S}  # Costo fittizio (può essere personalizzato)

# Inizializzazione del modello
m = gp.Model("routeGeneration")

# Un solo percorso per ora
R = ["1_7"]
Ro = {"1_7": 1}
Rd = {"1_7": 7}

# Variabili decisionali
x = m.addVars(R, S, vtype=GRB.BINARY, name="x")  # Se si ferma a s su r
y_plus = m.addVars(R, S, vtype=GRB.BINARY, name="y_plus")   # Inizio percorso
y_minus = m.addVars(R, S, vtype=GRB.BINARY, name="y_minus") # Fine percorso

# Vr = gp.quicksum(Vs_value[s] * x["1_7", s] for s in S)

# Funzione obiettivo (1a)
m.setObjective(gp.quicksum(Vs_value[s] * x["1_7", s] for s in S), GRB.MINIMIZE)

# Vincolo (1b): una sola stazione iniziale tra quelle terminali
m.addConstr(gp.quicksum(y_plus["1_7", s] for s in Sc) == 1, "start_terminal")

# Vincolo (1c): una sola stazione finale tra quelle terminali
m.addConstr(gp.quicksum(y_minus["1_7", s] for s in Sc) == 1, "end_terminal")

# Vincolo (1d): inizio + fine = 2
m.addConstr(gp.quicksum(y_plus["1_7", s] + y_minus["1_7", s] for s in S) == 2, "start_end_unique")

# Vincolo (1e): almeno una tra 1 e 7 deve essere selezionata
m.addConstr(y_plus["1_7", 1] + y_minus["1_7", 7] >= 1, "terminal_presence")

# Vincolo (1f): x_s ≤ sum(y⁺_i) - sum(y⁻_i)
for s in Ss:
    m.addConstr(
        x["1_7", s] <= gp.quicksum(y_plus["1_7", i] for i in Ss if i <= s) -
                       gp.quicksum(y_minus["1_7", i] for i in Ss if i < s),
        f"visit_if_between_{s}")

# Vincolo (1g): x_s ≥ y⁺_s + y⁻_s
for s in S:
    m.addConstr(x["1_7", s] >= y_plus["1_7", s] + y_minus["1_7", s], f"must_visit_terminal_{s}")

# Vincolo (1h): x_s ≤ x_m
for m_station in M:
    for s in Sm:
        m.addConstr(x["1_7", s] <= x["1_7", m_station], f"skip_if_major_skipped_{m_station}_{s}")

# Vincolo (1i): x_s ≤ x_{m+1} (solo se m+1 ∈ M)
for i in range(len(M) - 1):
    m_station = M[i]
    next_station = M[i + 1]
    for s in Sm:
        m.addConstr(x["1_7", s] <= x["1_7", next_station], f"skip_if_next_major_skipped_{m_station}_{s}")

# Vincolo (1j): x_s ≤ x_u per tutti s, u ∈ Sm
for s in Sm:
    for u in Sm:
        m.addConstr(x["1_7", s] <= x["1_7", u], f"all_skipped_or_all_selected_{s}_{u}")

# Ottimizzazione
m.optimize()

# Risolvi il modello
m.optimize()

# Dopo l'ottimizzazione, stampa i valori delle variabili
for s in S:
    val = x["1_7", s].X
    print(f'x["1_7", {s}] = {val}')


print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
for s in S:
    if x["1_7", s].X > 1e-6:  # evita valori molto vicini a 0 per modelli LP
        print(f'x["1_7", {s}] = {x["1_7", s].X}')


