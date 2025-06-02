# 🚉 Ottimizzazione Percorsi e Servizio Passeggeri

Questo progetto implementa un modello di **Ricerca Operativa** per ottimizzare la scelta di un percorso tra più alternative, tenendo conto della possibilità di prelevare passeggeri lungo il tragitto, vincoli di orario, capacità degli archi e ritardi.

## 📌 Obiettivo

Minimizzare una funzione che bilancia:
- Il ritardo di arrivo alle stazioni rispetto a una timetable predefinita
- Il numero di passeggeri serviti

## 📁 Struttura del progetto

- `main.py`: Script principale che definisce i dati, le variabili decisionali, i vincoli e la funzione obiettivo.
- `model.tex`: Formulazione matematica del modello (in LaTeX).
- `README.md`: Questo file.
- `requirements.txt`: Librerie Python necessarie.

## ⚙️ Dipendenze

Assicurati di avere Python 3.7+ e installa le dipendenze con:

```bash
pip install -r requirements.txt
```

**Requisiti principali:**
- `gurobipy`: per la modellazione e risoluzione del problema
- `itertools`, `random`: per generare i dati casuali
- `typing`: per annotazioni

## 🧠 Modello matematico

Il modello considera:
- Un insieme di percorsi, ciascuno costituito da una sequenza di archi
- Tempi di percorrenza sugli archi
- Finestra temporale per la presa dei passeggeri
- Capacità massima su ogni arco
- Compatibilità tra passeggeri e percorsi

La funzione obiettivo minimizza:

```math
0.5 \cdot 	ext{ritardi totali} - 	ext{numero passeggeri serviti}
```

## 📊 Variabili chiave

- `Z_p`: binaria, vale 1 se il percorso `p` è scelto
- `t_s`: tempo di arrivo alla stazione `s`
- `x_i`: binaria, vale 1 se il passeggero `i` è servito
- `pax_served`: intero, totale passeggeri serviti

## 🧩 Esempi di vincoli

- Capacità su ogni arco: nessun arco può trasportare più di `capMax` passeggeri
- Ogni passeggero può essere servito solo se compatibile con un percorso selezionato
- Il tempo di arrivo alla stazione deve rientrare nella finestra consentita

## 📦 Output

Il modello restituisce:
- Il percorso ottimale selezionato
- Il numero di passeggeri serviti
- Gli orari di arrivo alle stazioni
- I ritardi rispetto alla timetable

## 📄 Licenza

Distribuito sotto licenza MIT.

## 🤝 Contatti

Per domande, apri una issue o contattami su [email@example.com](mailto:email@example.com)