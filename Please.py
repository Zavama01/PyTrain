# RICORDA CHE IL MODELLO CALCOLA PER SINGOLA ITERAZIONE (CIOE' SOLO ANDATA)


# INPUT - Insieme di Archi consecutivi con peso (aka : percorsi validi già ottimi)
# il peso sarebbe il tempo di percorrenza dell'arco
# INPUT - timetable originale (senza disruption)

# nota bene. ci sono solo 7 stazioni

# - Passeggeri per stazione, ad ogni passeggero assegno un arco che deve percorrere (tratta)
# i passeggeri saranno in totale 500

# passeggeri_serviti - variabile che indica i passeggeri serviti nel percorso scelto: se il nodo di partenza e di
# arrivo sono presenti nell'insieme di nodi scelti e il mezzo passa nell'intervallo prestabilito allora si incrementa
# il velore della variabile

# l'orario viene calcolato con tempo di partenza stazione precedente + tempo percorrenza arco a-b + sosta fissa (5 min)

# ad ogni stazione è assegnato un intervallo di tempo (orario) per cui è possibile prendere i passeggeri (attesa
# passeggeri) se l'orario calcolato rientra nell'intervallo di tempo allora i passeggeri salgono sul mezzo,
# altrimenti no

# l'intervallo di tempo viene calcolato per singola stazione (nodo) e corrisponde alla timetable + 10 minuti

# ogni tratta (il/i mezzo/i di trasporto) ha una capienza massima (capMax = 120) che va riempita sempre il più possibile

# FUNZIONE OBBIETTIVO - minimizzare il ritardo dei mezzi rispetto alla timetable normale
# e massimizzare il numero di passeggeri serviti

# Zi è una variabile binaria che mi dice se è stato scelto l'insieme di archi i
# i = 1 se si
# i = 0 se no

# max R = 1 - indica che posso scegliere solo un insieme di archi (cioè percorso)

# TODO AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA
# riscrittura
#
# ho bisogno di creare un modello che:
#
# prenda in input più insiemi di archi consecutivi (percorso) con peso tipo
# A = [(0, 1), (1, 2)]
# B = [(3, 5), (5, 7)]
# w = {(0, 1): 5, (1, 2): 6}  # Tempi di percorrenza
# il peso associato agli archi è il tempo di percorrenza degli archi.
# inoltre deve prendere in input una timetable
#
# nota bene: ci sono solo 7 stazioni
#
# FUNZIONE OBBIETTIVO - minimizzare il ritardo dei mezzi rispetto alla timetable normale
# e massimizzare il numero di passeggeri serviti
#
# Dopodichè ci sono i passeggeri per stazione, cioè ad ogni passeggero assegno un arco da percorrere
# (i passeggeri possono avere lo stesso arco da percorrere), facciamo finta siano 500
# la variabile è Ps e conta i passeggeri presenti nelle varie stazioni. s può valere da 1 a 7.
# Ps viene calcolata controllando l'arco associato al passeggero e guardando il valore del primo nodo
#
# la variabile passeggeri_serviti indica i passeggeri serviti nel percorso scelto: se il nodo di partenza e di arrivo
# sono presenti nell'insieme di nodi scelti e il mezzo passa nell'intervallo prestabilito allora si incrementa il
# valore della variabile
#
# l'orario viene calcolato con tempo di partenza stazione precedente + tempo percorrenza arco a-b + sosta fissa (5 min)
#
# ad ogni stazione è assegnato un intervallo di tempo (attesa passeggeri espresso in orario) per cui è possibile
# prendere i passeggeri. Se l'orario calcolato rientra nell'intervallo di tempo allora i passeggeri presenti in quel
# nodo che hanno come destinazione un nodo del percorso scelto vanno ad incrementare la variabile di
# Passeggeri_serviti nella funzione obbiettivo
#
# l'intervallo di tempo viene calcolato per singola stazione (nodo) e corrisponde alla timetable + 10 minuti
#
# ogni tratta (cioè arco a-b) ha una capienza massima (capMax = 120)
#
# Zi è una variabile binaria che mi dice se è stato scelto l'insieme di archi i (cioè il percorso)
# i = 1 se si
# i = 0 se no
#
# max R = 1 - indica quanti insiemi di archi posso scegliere (cioè percorso), in questo caso solo uno fra A e B
#

# TODO AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA

# ogni passeggero_non_servito aggiunge una penalità temporale FUNZIONE OBIETTIVO - minimizzare il
# ritardo dei mezzi (rispetto alla timetable normale) e il numero di passeggeri non serviti

# passeggeri_non_serviti - (variabile che indica il totale di passeggeri) - se il nodo di partenza e di arrivo sono
# presenti nell'insieme di nodi scelti e il mezzo passa nell'intervallo prestabilito
# allora "passeggeri_non_serviti" decrementa
