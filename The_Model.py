from gurobipy import Model, GRB, quicksum
import random
import itertools

# sezione INPUT ________________________
# Percorsi in input, (stazioni ordinate per cui passano i mezzi di trasporto)
nodi_percorso_1 = [1, 4, 5, 6]
nodi_percorso_2 = [1, 3, 4, 6, 7]
nodi_percorso_3 = [1, 2, 3, 4, 5, 6, 7]
percorsi_validi = [nodi_percorso_1, nodi_percorso_2, nodi_percorso_3]
# ______________________________________

S = [1, 2, 3, 4, 5, 6, 7]  # Stazioni


# Sceglie un percorso casuale
percorso_scelto = random.choice(percorsi_validi)
Y = len(percorso_scelto)

# PARAMETRI
X = len(S)  # numero di stazioni - presupposizione

# Supponiamo di chiamare le stazioni "S1", "S2", ..., "S7"
stazioni = [f"S{i + 1}" for i in range(X)]

# Capienza (fissa) di ogni percorso (cioè capienza dei mezzi) - Presuppozione
Cap = 120

# Passenger demand (cioè il quantitativo di passeggeri ad ogni stazione)
P_dem = {s: random.randint(0, 200) for s in
         stazioni}  # Genera valori random tra 0 e 200 per ogni stazione - presupposizione

# tempo di percorrenza dell'arco
peso_archi = list(itertools.combinations(stazioni, 2))  # Genera tutte le combinazioni non ordinate di 2 nodi

# Genera un tempo random per ciascuna coppia
archi = {}
for (nodo1, nodo2) in peso_archi:
    ore = random.randint(0, 5)  # da 0 a 5 ore
    minuti = random.randint(0, 59)  # da 0 a 59 minuti
    archi[(nodo1, nodo2)] = (ore, minuti)

# tempo di penalità per passeggero non servito
p = 0.01

# Stampa i risultati
for (n1, n2), (h, m) in archi.items():
    print(f"Arco {n1} - {n2}: {h}h {m}min")

# ------------------------------
# MODELLO
# ------------------------------
model = Model("RST_Model")

# VARIABILI DECISIONALI
# totale passeggeri non serviti a fine iterazione
not_served = 0

# variabile binaria che indica se il percorso p è selezionato o meno
z = model.addVars(percorsi_validi, vtype=GRB.BINARY, name="z")

# variabile binaria che indica se il bus parte all'orario prefissato (t) nella tratta corrente
d = model.addVars(percorsi_validi, vtype=GRB.BINARY, name="d")
