from gurobipy import Model, GRB

# Dati di input
N = 4
treni = range(N)  # N treni totali
direzione = {0: 'A', 1: 'B', 2: 'A', 3: 'B'}  # dict: direzione[i] = 'A' or 'B'
T = {0: 5, 1: 6, 2: 4, 3: 5}  # durata attraversamento per ogni treno
H = 120  # orizzonte temporale massimo
B = 10000  # Big-B (sufficientemente grande)

# Crea il modello
m = Model("schedulazione_treni")

# Variabili
x = {}  # tempo di inizio attraversamento
for i in treni:
    x[i] = m.addVar(lb=0, ub=H, vtype=GRB.CONTINUOUS, name=f"x_{i}")

# Variabili binarie per l’ordine tra treni opposti
o = {}
for i in treni:
    for j in treni:
        if i < j and direzione[i] != direzione[j]:
            o[i, j] = m.addVar(vtype=GRB.BINARY, name=f"o_{i}_{j}")

# Variabile ausiliaria per makespan (opzionale)
z = m.addVar(lb=0, ub=H + max(T.values()), vtype=GRB.CONTINUOUS, name="z")

# Vincoli di non sovrapposizione tra treni di direzione opposta
for i in treni:
    for j in treni:
        if i < j and direzione[i] != direzione[j]:
            m.addConstr(x[i] + T[i] <= x[j] + B * (1 - o[i, j]), name=f"disj_{i}_{j}_1")
            m.addConstr(x[j] + T[j] <= x[i] + B * o[i, j], name=f"disj_{i}_{j}_2")

# Vincoli per makespan
for i in treni:
    m.addConstr(z >= x[i] + T[i], name=f"makespan_{i}")

# Funzione obiettivo: minimizza il tempo totale (makespan)
# più chiaramente: viene ridotto il tempo totale impiegato a far passare tutti i treni,
# cioè il servizio viene completato in meno tempo possibile in quanto viene ridotto l'attraversamento che dura di più
m.setObjective(z, GRB.MINIMIZE)

# Risolvi
m.optimize()

# Output dei risultati
for i in treni:
    print(f"Treno {i}: inizio attraversamento = {x[i].X:.2f} min")
print(f"Makespan totale = {z.X:.2f} min")
