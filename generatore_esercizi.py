import ollama
import json
import re
import random

NOME_MODELLO_OLLAMA = "gemma4" 

# ==========================================
# SERVIZIO PLUS: Esercizi Generati dall'IA
# ==========================================
def crea_quiz_plus(copione):
    print("\n--- GENERAZIONE ESERCIZI PLUS (OLLAMA) ---")

    # ---------- FASE 1: classificazione genere/tono ----------
    '''prompt_classificazione = f"""Analizza il seguente copione tratto da un video e identifica il genere/tono prevalente.

COPIONE:
\"\"\"{copione}\"\"\"

Scegli UNA sola etichetta tra queste (la più adatta):
comico, horror, drammatico, romantico, avventura, documentario/neutro, tragico, satirico, mistero, azione

Rispondi SOLO con un oggetto JSON in questo formato, senza altro testo:
{{
"genere": "etichetta_scelta",
"descrizione_stile": "breve frase (max 15 parole) che descrive il registro linguistico da usare, es. 'linguaggio teso, frasi brevi, atmosfera inquietante'"
}}
"""

    genere = "documentario/neutro"          # default di sicurezza
    descrizione_stile = "tono didattico standard"  # default di sicurezza

    try:
        risposta_classificazione = ollama.chat(
            model=NOME_MODELLO_OLLAMA,
            messages=[{'role': 'user', 'content': prompt_classificazione}],
            format='json',
        )
        contenuto_class = risposta_classificazione['message']['content']
        match_class = re.search(r'\{.*\}', contenuto_class, re.DOTALL)
        if match_class:
            dati_classificazione = json.loads(match_class.group(0))
            genere = dati_classificazione.get("genere", genere)
            descrizione_stile = dati_classificazione.get("descrizione_stile", descrizione_stile)
        print(f"🎭 Genere rilevato: {genere} — {descrizione_stile}")
    except Exception as e:
        print(f"⚠️ Classificazione fallita, uso stile neutro di default: {e}")
#GENERE IDENTIFICATO: {genere}
STILE DA MANTENERE: {descrizione_stile}
        '''

    # ---------- FASE 2: generazione esercizi ----------
    prompt = f"""Sei un insegnante di inglese esperto nella creazione di esercizi didattici.

COPIONE DI RIFERIMENTO:
\"\"\"{copione}\"\"\"
COMPITO:
Crea esattamente 10 esercizi basati ESCLUSIVAMENTE su parole, frasi o situazioni presenti nel copione.
Adatta il TONO delle domande e delle opzioni allo stile indicato sopra:
- se il genere è comico/satirico → usa un tono leggero, magari con opzioni errate buffe/assurde ma chiaramente sbagliate
- se il genere è horror/tragico/mistero → mantieni un linguaggio teso, evita opzioni scherzose che stonerebbero
- se il genere è documentario/neutro → usa un tono didattico standard, senza colorazioni emotive forzate

DISTRIBUZIONE ESEMPIO:
- 3 esercizi di tipo "sinonimo"
- 3 esercizi di tipo "completamento"
- 4 esercizi di tipo "traduzione"

REGOLA SULLA LINGUA:
- Il testo introduttivo della domanda (l'istruzione) deve essere SEMPRE in italiano.
- La frase o parola tratta dal copione (l'elemento su cui verte l'esercizio) resta in inglese, perché è materiale didattico di lingua inglese.
- Le opzioni di risposta restano in inglese per gli esercizi di "sinonimo" e "completamento".
- Per gli esercizi di "traduzione", la domanda in italiano contiene la frase inglese da tradurre, mentre le opzioni sono le possibili traduzioni in italiano.

ATTENZIONE: NON tradurre mai le opzioni degli esercizi di tipo "sinonimo" e "completamento" — devono restare in inglese. Solo il testo introduttivo della domanda va in italiano.

Esempi corretti:

{{
  "tipo": "completamento",
  "domanda": "In base al dialogo, gli orsi sono erroneamente convinti di mangiare _________.",
  "opzioni": ["cheese", "beets", "gummy bears", "banana chips"],
  "risposta_corretta": "beets"
}}

{{
  "tipo": "sinonimo",
  "domanda": "Nel copione, quale parola è sinonimo di 'happy'?",
  "opzioni": ["sad", "joyful", "angry", "tired"],
  "risposta_corretta": "joyful"
}}

{{
  "tipo": "traduzione",
  "domanda": "Come si traduce in italiano la frase: 'I can't believe this is happening'?",
  "opzioni": [
    "Non riesco a credere che stia succedendo",
    "Non voglio credere a niente",
    "Credo che sia già successo",
    "Non capisco cosa sta succedendo"
  ],
  "risposta_corretta": "Non riesco a credere che stia succedendo"
}}
"""
    try:
        response = ollama.chat(
            model=NOME_MODELLO_OLLAMA,
            messages=[{'role': 'user', 'content': prompt}],
        )
        match = re.search(r'\[.*\]', response['message']['content'], re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return []
    except Exception as e:
        print(f"❌ Errore Ollama: {e}")
        return []

# ==========================================
# SERVIZIO BASE: Esercizi Generati da Python
# ==========================================
def crea_quiz_base(battute):
    print("\n--- GENERAZIONE ESERCIZI BASE (Algoritmo Python) ---")
    esercizi = []
    
    # 1. Creiamo un "calderone" con tutte le parole del video (lunghe almeno 4 lettere)
    tutte_le_parole = []
    for b in battute:
        parole = re.findall(r'\b[a-zA-Z]{4,}\b', b['text'].lower())
        tutte_le_parole.extend(parole)
    
    tutte_le_parole = list(set(tutte_le_parole)) # Rimuoviamo i duplicati
    
    # Fallback di sicurezza se il video è muto o cortissimo
    if len(tutte_le_parole) < 4:
        tutte_le_parole.extend(["time", "house", "friend", "water", "world", "school", "thing"])

    # 2. Scegliamo un massimo di 10 battute a caso
    battute_scelte = random.sample(battute, min(10, len(battute)))
    
    for b in battute_scelte:
        testo_originale = b['text']
        parole_nella_frase = re.findall(r'\b[a-zA-Z]{4,}\b', testo_originale)
        
        if not parole_nella_frase: continue
            
        parola_da_indovinare = random.choice(parole_nella_frase)
        
        # Sostituiamo la parola esatta con i trattini
        frase_nascosta = re.sub(rf'(?i)\b{re.escape(parola_da_indovinare)}\b', '____', testo_originale, count=1)
        
        # Scegliamo 3 parole sbagliate dal calderone
        distrattori_disponibili = [p for p in tutte_le_parole if p.lower() != parola_da_indovinare.lower()]
        distrattori = random.sample(distrattori_disponibili, min(3, len(distrattori_disponibili)))
        
        opzioni = distrattori + [parola_da_indovinare.lower()]
        random.shuffle(opzioni)
        
        esercizi.append({
            "domanda": f"Completa la frase:\n\"{frase_nascosta}\"",
            "opzioni": opzioni,
            "risposta_corretta": parola_da_indovinare.lower()
        })
        
    print(f"✅ {len(esercizi)} Esercizi base creati in 0 secondi!")
    return esercizi