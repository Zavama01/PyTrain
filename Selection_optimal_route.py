# 1) La mia funzione obbiettivo calcola il percorso migliore minimizzando
# i tempi di attesa dei passeggeri (aka ritardo dei treni)

# 2) Il mio input sarà dunque una serie di percorsi validi per
# raggiungere la destinazione (indipendentemene che siano tramite bus o treni)

# IO GENERO UNA NUOVA TIMETABLE DI ARCHI SULLA BASE DEI PERCORSI
# FATTIBILI, CHE MINIMIZZA I TEMPI DI ATTESA

# 3) Penalità per passeggeri non serviti?
# vuol dire che inserirò una certa capienza massima X


import gurobipy as gp
from gurobipy import GRB
import random
import networkx as nx
S = [1,2,3,4,5,6,7]
R = [3,4,5,6,7] #rotte possibili
T = 24  # Tempo in ore
R_max = 2 #Massimo numero di rotte selezionabili
W = 0.5 #Tempo attesa massimo
Te = list(range(T + W + 1))
U = 3 # bus disponibili
G = 50 # posti disponibili bus

v_s = {s: random.randint(1, 7) for s in S} #tempo di viaggio archi
kappa_s = {s: random.randint(1, 7) for s in S} #tempo di sosta
J = 5 # tempo di ripartenza da stazione finale
P = 150 # penalità passeggeri non serviti
F_max = 5
F_min = 2

# Variabile binaria: x[r,s] = 1 se la rotta r si ferma alla stazione s, 0 altrimenti
model = gp.Model("BusRouteOptimization")

x = model.addVars(R, S, vtype=GRB.BINARY, name="x")

# Creazione grafo orientato pesato (tempi di viaggio + sosta)

G = nx.DiGraph()
G.add_nodes_from(S)

# Aggiungiamo archi tra stazioni consecutive con peso tempo totale (viaggio + sosta)

for s in S[:-1]:
    travel_time = v_s[s]
    stop_time = kappa_s[s]
    total_time = travel_time + stop_time
    G.add_edge(s, s+1, weight=total_time)
