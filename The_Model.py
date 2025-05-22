from datetime import datetime, timedelta

from gurobipy import Model, GRB, quicksum
import random
import itertools

# todo - RICORDA CHE ATTUALMENTE STAI LAVORANDO SU ITERAZIONE SINGOLA DEL MODELLO IL CHE VUOL DIRE CHE C'E' SOLO
# todo  IL VIAGGIO D'ANDATA

# sezione INPUT ________________________
# Percorsi in input, (stazioni ordinate per cui passano i mezzi di trasporto)
fermate_1 = [1, 4, 5, 6]
fermate_2 = [1, 3, 4, 6, 7]
fermate_3 = [1, 2, 3, 4, 5, 6, 7]
percorsi_validi = [fermate_1, fermate_2, fermate_3]

# Sceglie un percorso casuale - ovviamente non dovrebbe essere così, ma dovrebbe essere deciso dipendentemente dall'output
p_selezionato = random.choice(percorsi_validi)
y = len(p_selezionato)  # numero di stazioni - presupposizione

# Supponiamo di chiamare le stazioni "S1", "S2", ..., "S7"
stazioni = [f"S{p_selezionato[j]}" for j in range(y)]

# Orario di partenza dalla prima stazione
orario_partenza = datetime.strptime("08:00", "%H:%M")

# Dizionario per la tabella oraria
tabella_oraria = {}
orario_corrente = orario_partenza

for nodo in p_selezionato:
    # Assegna orario attuale al nodo
    tabella_oraria[nodo] = orario_corrente.strftime("%H:%M")

    # Aggiungi tempo randomico di percorrenza (3–10 minuti) per la prossima stazione
    minuti_percorrenza = random.randint(10, 20)
    orario_corrente += timedelta(minutes=minuti_percorrenza)

#  in teoria dovresti avere in input la timetable originale senza interruzione ferroviaria in modo
#  tale che il modello la prenda come confronto e possa stabilire se ci sonon stati ritardi

# ______________________________________

# PARAMETRI

R_max = 1  # numero massimo di percorsi (route) scelti

# Capienza/capacità (fissa) di ogni percorso (cioè capienza dei mezzi) - Presuppozione
cap = 120

# todo la capienza è un valore con un cap massimo e minimo, ma va resa dinamica in quanto
# todo i passeggeri possono scendere e salire tra una stazione e l'altra

# ogni stazione avrà un tot di passeggeri che devono usare quella tratta - presupposizione
# Genera un numero casuale di passeggeri in ogni stazione
passeggeri_per_stazione = {
    nodo: random.randint(0, 200) for nodo in p_selezionato
}

# non prendo in considerazione i passeggeri che non usano la tratta prefissata, tantomeno quelli che arrivano prima o dopo

# Passenger demand (cioè il quantitativo di passeggeri ad ogni stazione)
p_dem = {s: random.randint(0, 200) for s in
         stazioni}  # Genera valori random tra 0 e 200 per ogni stazione - presupposizione

# tempo di percorrenza dell'arco - in realtà lo ricevi in input - presupposizione
peso_archi = list(itertools.combinations(stazioni, 2))  # Genera tutte le combinazioni non ordinate di 2 nodi

# Genera un tempo random per ciascuna coppia
archi = {}
for (nodo1, nodo2) in peso_archi:
    ore = 0
    minuti = random.randint(10, 30)  # da 0 a 20 minuti
    archi[(nodo1, nodo2)] = (ore, minuti)

# tempo di penalità per passeggero non servito
p = 0.01

# ------------------------------
# ZONA DI STAMPA DI RISULTATI PER CONTROLLO - NON SERVE AI FINI DEL MODELLO - DA RIMUOVERE
# ------------------------------
for (n1, n2), (h, m) in archi.items():
    print(f"Arco {n1} - {n2}: {h}h {m}min")

print(p_selezionato)
print(percorsi_validi.index(
    p_selezionato) + 1)  # ho messo la somma perchè altrimenti sull'array la posizione 0 è # uguale a 1
print(passeggeri_per_stazione)
# Stampa la tabella
print("Stazione | Orario Ideale")
for nodo in p_selezionato:
    print(f"   {nodo}     | {tabella_oraria[nodo]}")

# ------------------------------
# MODELLO
# ------------------------------
model = Model("RST_Model")

# VARIABILI DECISIONALI ----------------------------------------
# totale passeggeri non serviti a fine iterazione
not_served = 0

# variabile binaria che indica se il percorso p è selezionato o meno
z = model.addVars(percorsi_validi.index(p_selezionato), vtype=GRB.BINARY, name="z")

# variabile binaria che indica se il bus parte all'orario prefissato (t) nella tratta corrente - todo ancora non ho nulla con l'orario t
d = model.addVars(percorsi_validi.index(p_selezionato), vtype=GRB.BINARY, name="d")

# Variabili per tenere traccia della salita e discesa dei passeggeri nelle varie stazioni
p_up = model.addVars(percorsi_validi.index(p_selezionato), vtype=GRB.INTEGER, name="salgono")  # passeggeri che salgono
p_down = model.addVars(percorsi_validi.index(p_selezionato), vtype=GRB.INTEGER,
                       name="scendono")  # passeggeri che scendono
p_on = model.addVars(percorsi_validi.index(p_selezionato), vtype=GRB.INTEGER, name="capacita")  # passeggeri a bordo

# VINCOLI -------------------------------------------------------
# vincolo 2b - si assicura che vengano selezionate non più di R_max rotte - ???
model.addConstr(quicksum(z[r] for r in percorsi_validi) <= R_max, "2b")

# vincoli sulla capacità dei mezzi sulle varie tratte (bus e/o treni)
model.addConstr(p_on[0] == p_up[0] - p_down[0], "cap_init")

for t in p_selezionato[1:]:
    model.addConstr(p_on[t] == p_on[t - 1] + p_up[t] - p_down[t], f"cap_evol_{t}")

for t in p_selezionato:
    model.addConstr(p_on[t] <= cap, f"cap_max_{t}")
    model.addConstr(p_on[t] >= 0, f"cap_min_{t}")
