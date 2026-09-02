import whisper
import ollama

NOME_MODELLO_OLLAMA = "gemma4"

print("Caricamento dell'IA in corso...")
modello_whisper = whisper.load_model("base") 

def estrai_testo_da_audio(percorso_audio):
    try:
        risultato = modello_whisper.transcribe(percorso_audio, language="en", fp16=False)
        return risultato['text'].strip()
    except Exception as e:
        return f"[Errore audio: {e}]"

def genera_report_valutazione(testo_trascritto, battute_scelte_dall_utente, copione_completo):
    # Formattiamo le battute dell'utente per farle leggere bene all'IA
    testo_battute = "\n".join([f"- {b}" for b in battute_scelte_dall_utente])
    
    prompt = f"""Sei un insegnante di lingue esigente.
L'utente ha appena simulato una conversazione doppiando SOLO un personaggio specifico.

COPIONE COMPLETO DEL VIDEO:
"{copione_completo}"

LE BATTUTE ASSEGNATE ALL'UTENTE ERANO ESCLUSIVAMENTE QUESTE:
{testo_battute}

TRASCRIZIONE DELL'AUDIO REGISTRATO DAL MICROFONO:
"{testo_trascritto}"
(Nota: Se l'utente non ha usato le cuffie, potresti sentire anche la voce originale del video nelle pause).

IMPORTANTE: Valuta L'UTENTE SOLO ED ESCLUSIVAMENTE sulle battute a lui assegnate. Fai un ragionamento fonetico per capire se le ha pronunciate bene. Ignora le parole dell'altro personaggio.

Scrivi un "Report di Valutazione" strutturato ESATTAMENTE così:
## Voto Complessivo: [Voto da 1 a 10]/10
## Analisi della Conversazione
[Un paragrafo sul ritmo, tempismo e fluidità nelle SUE battute.]
## Correzioni Principali
[Elenco puntato con i suoi errori specifici].

Non scrivere codice."""

    try:
        response = ollama.chat(model=NOME_MODELLO_OLLAMA, messages=[{'role': 'user', 'content': prompt}])
        return response['message']['content']
    except Exception as e:
        return f"Errore durante l'analisi: {e}."
import json
import re


def traduci_battute(battute, lingua="inglese"):
    print(f"\n--- TRADUZIONE IN {lingua.upper()} (OLLAMA) ---")
    
    # Prepariamo un JSON snello per non far confondere l'IA con i timestamp
    dati_semplificati = [{"id": i, "text": b["text"]} for i, b in enumerate(battute)]
    
    prompt = f"""Sei un traduttore professionista. Traduci il seguente copione dall'italiano all'{lingua}.
MANTIENI ESATTAMENTE LA STESSA STRUTTURA JSON, cambia solo il testo in inglese.
DEVI RISPONDERE SOLO ED ESCLUSIVAMENTE CON UN ARRAY JSON. Non aggiungere commenti.

{json.dumps(dati_semplificati, ensure_ascii=False)}
"""
    try:
        response = ollama.chat(model=NOME_MODELLO_OLLAMA, messages=[{'role': 'user', 'content': prompt}])
        match = re.search(r'\[.*\]', response['message']['content'], re.DOTALL)
        if match:
            traduzione = json.loads(match.group(0))
            nuove_battute = []
            for originale, tradotta in zip(battute, traduzione):
                nuova_b = originale.copy()
                nuova_b['text'] = tradotta['text']
                nuova_b['originale'] = originale['text'] # Salviamo il testo italiano di backup
                nuove_battute.append(nuova_b)
            print("✅ Traduzione completata con successo!")
            return nuove_battute
        return []
    except Exception as e:
        print(f"❌ Errore traduzione Ollama: {e}")
        return []