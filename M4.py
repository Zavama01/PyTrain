from gurobipy import *
from datetime import datetime, timedelta
import random
import itertools

# Percorsi in input
fermate_1 = [1, 4, 5, 6]
fermate_2 = [1, 3, 4, 6, 7]
fermate_3 = [1, 2, 3, 4, 5, 6, 7]
percorsi_validi = [fermate_1, fermate_2, fermate_3]

N = random.choice(percorsi_validi)  # Nodi ordinati

# Archi diretti consecutivi (da nodo i a nodo i+1)
A = [(N[i], N[i + 1]) for i in range(len(N) - 1)]

# Tempo di percorrenza per ogni arco
w = {}
for (i, j) in A:
    w[(i, j)] = random.randint(10, 30)  # tra 10 e 30 minuti

# Generazione orari ideali coerenti
start_time = 7 * 60  # 7:00 in minuti
r = {}
current_time = start_time
r[N[0]] = current_time
for i in range(len(N) - 1):
    current_time += w[(N[i], N[i + 1])]
    r[N[i + 1]] = current_time


# Funzione per stampare orari hh:mm
def minutes_to_time(m):
    h = int(m) // 60
    mm = int(m) % 60
    return f"{h:02d}:{mm:02d}"


# Passeggeri in ogni nodo
P = {i: random.randint(50, 200) for i in N}
C = 120
rho = 2

# Modello
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
    m.addConstr(x[j] >= x[i] + w[(i, j)], name=f"tempo_{i}_{j}")

for i in N:
    m.addConstr(x[i] >= r[i], name=f"no_anticipo_{i}")


# Orario fissato al nodo iniziale
m.addConstr(x[N[0]] == r[N[0]], name="orario_fisso_partenza")

# Obiettivo
m.setObjective(quicksum(d[i] for i in N) + rho * quicksum(u[i] for i in N), GRB.MINIMIZE)
m.optimize()

# Output
print("\n=== Timetable Comparativa ===")
print(f"{'Nodo':<6}{'Orario ideale':<15}{'Orario assegnato':<20}{'Ritardo':<10}{'Non serviti':<15}{'Passeggeri'}")
for i in N:
    orario_ideale = minutes_to_time(r[i])
    orario_output = minutes_to_time(x[i].X)
    ritardo = f"{d[i].X:.1f}"
    non_serviti = f"{u[i].X:.1f}"
    print(f"{i:<6}{orario_ideale:<15}{orario_output:<20}{ritardo:<10}{non_serviti:<15}{P[i]}")

print("\n=== Passeggeri sugli archi ===")
for (i, j) in A:
    print(f"{i}->{j}: {y[i, j].X:.1f} passeggeri")
