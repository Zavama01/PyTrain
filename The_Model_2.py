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
# stazioni = [f"S{N[j]}" for j in range(y)]

# Todo i passeggeri nelle stazioni devono salire tutti fino ad occupare più posti possibile e svuotare la stazione

# todo orario arrivo + tempo percorrenza (w) + (opzionale) tempo di sosta (5 min)

# orario ideale calcolo : orario randomico + sosta + percorrenza ideale (nuova variabile)
# un solo  (o più) arco (scelto a caso) avrà la percorrenza ideale incrementata per simulare la disruption e quindi sarà una percorrenza non ideale

# Genera tutte le combinazioni non ordinate di 2 nodi
A = [(N[i], N[i + 1]) for i in range(len(N) - 1)]  # Archi diretti consecutivi (da nodo i a nodo i+1)

# Genera un tempo random per ciascuna coppia
w = {}  # Tempi di percorrenza
for (nodo1, nodo2) in A:
    # ore = 0
    minuti = random.randint(10, 30)  # da 0 a 20 minuti
    w[(nodo1, nodo2)] = minuti

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

for i in N:
    m.addConstr(x[i] >= r[i], name=f"no_anticipo_{i}")

m.optimize()

# try stampa
print("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
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
