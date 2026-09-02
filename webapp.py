import os
import json
import time
import asyncio
import sounddevice as sd
import soundfile as sf
from nicegui import ui, app

import motore_ai 
import elaborazione 
import generatore_esercizi 

FILE_JSON = "output/dati_karaoke_completi.json"
app.add_media_files('/media', 'output')
os.makedirs("input", exist_ok=True)

stato_app = {
    'battute_totali': [],
    'battute_scelte': [],
    'durata_video': 0,
    'copione_originale': "",
    'lista_quiz': [],
    'percorso_video': None,
    'cancella_dopo': False,
    'modalita_corrente': 'doppiaggio' # Memorizza a cosa stiamo giocando
}

def carica_dati_video():
    with open(FILE_JSON, 'r', encoding='utf-8') as f:
        battute = json.load(f)
    stato_app['battute_totali'] = battute
    stato_app['durata_video'] = battute[-1]['end'] + 2.0
    stato_app['copione_originale'] = " ".join([b['text'] for b in battute])

# ==========================================
# 1. PAGINA HUB
# ==========================================
@ui.page('/')
def pagina_hub():
    stato_app['percorso_video'] = None
    stato_app['cancella_dopo'] = False

    ui.label('🎬 Piattaforma di Doppiaggio').classes('text-5xl font-extrabold mx-auto mt-10 text-gray-800')
    
    with ui.row().classes('w-full justify-center mt-6 mb-2'):
        modalita_servizio = ui.radio({
            'base': '🟢 Servizio BASE (Veloce - Algoritmo Standard)',
            'plus': '🌟 Servizio PLUS (Analisi IA Avanzata)'
        }, value='base').classes('text-xl font-bold bg-gray-100 p-4 rounded-xl border border-gray-300')

    ui.label('1. Scegli il materiale di studio').classes('text-2xl font-bold mx-auto mt-6 mb-2 text-gray-700')
    label_video_scelto = ui.label('Nessun video selezionato').classes('text-xl font-bold text-red-500 mb-6 mx-auto transition-all duration-300')

    lista_video = [f for f in os.listdir('input') if f.endswith('.mp4')]

    def imposta_catalogo(nome_file):
        if nome_file:
            stato_app['percorso_video'] = f"input/{nome_file}"
            stato_app['cancella_dopo'] = False
            label_video_scelto.text = f"✅ Video selezionato: {nome_file}"
            label_video_scelto.classes(replace='text-xl font-bold text-green-600 mb-6 mx-auto transition-all duration-300')

    async def gestisci_upload(e):
        percorso_temp = 'output/temp_upload.mp4'
        file_obj = getattr(e, 'content', None) or getattr(e, 'file', None) or getattr(e, 'stream', None)
        if file_obj is not None:
            contenuto_video = await file_obj.read()
            with open(percorso_temp, 'wb') as f:
                f.write(contenuto_video)
            stato_app['percorso_video'] = percorso_temp
            stato_app['cancella_dopo'] = True
            label_video_scelto.text = "✅ Video caricato con successo!"
            label_video_scelto.classes(replace='text-xl font-bold text-green-600 mb-6 mx-auto transition-all duration-300')
        else:
            ui.notify('Errore di upload.', type='negative')

    with ui.row().classes('w-full max-w-4xl mx-auto gap-8'):
        with ui.card().classes('w-full flex-1 items-center p-6 bg-gray-50 shadow-md'):
            ui.label('Dal Catalogo').classes('text-xl font-bold mb-4')
            selettore = ui.select(lista_video, label='Seleziona un .mp4', on_change=lambda e: imposta_catalogo(e.value)).classes('w-full mb-2')

        with ui.card().classes('w-full flex-1 items-center p-6 bg-gray-50 shadow-md'):
            ui.label('Carica dal PC').classes('text-xl font-bold mb-4')
            ui.upload(on_upload=gestisci_upload, label='Trascina qui il file .mp4', auto_upload=True).classes('w-full')

    ui.label('2. Scegli il Minigioco').classes('text-2xl font-bold mx-auto mt-12 mb-6 text-gray-700')

    contenitore_loading = ui.column().classes('w-full items-center mt-4').style('display: none;')
    with contenitore_loading:
        ui.spinner('dots', size='lg', color='blue')
        label_progress = ui.label('Elaborazione in corso, attendi...').classes('text-lg mt-2 font-bold text-gray-600')

    contenitore_giochi = ui.row().classes('w-full max-w-5xl mx-auto gap-6 justify-center mb-10')

    async def lancia_gioco(modalita):
        if not stato_app['percorso_video']:
            ui.notify('Devi prima selezionare o caricare un video al Punto 1!', type='warning', position='top')
            return

        if modalita == 'conversazione':
            ui.notify('Funzionalità in arrivo nel prossimo aggiornamento! 🚀', type='info', position='top')
            return

        stato_app['modalita_corrente'] = modalita
        contenitore_giochi.style('display: none;')
        contenitore_loading.style('display: flex;')
        await asyncio.sleep(0.1) 
        
        await asyncio.to_thread(elaborazione.prepara_ambiente, stato_app['percorso_video'], stato_app['cancella_dopo'])
        carica_dati_video()
        
        if modalita == 'quiz':
            if modalita_servizio.value == 'plus':
                quiz = await asyncio.to_thread(generatore_esercizi.crea_quiz_plus, stato_app['copione_originale'])
            else:
                quiz = await asyncio.to_thread(generatore_esercizi.crea_quiz_base, stato_app['battute_totali'])
            stato_app['lista_quiz'] = quiz
            ui.navigate.to('/allenamento')
            
        elif modalita == 'doppiaggio':
            ui.navigate.to('/esercizio')
            
        elif modalita == 'multilingua':
            label_progress.text = "Sto traducendo il copione e generando le voci. Potrebbe volerci 1 minuto..."
            await asyncio.sleep(0.1)
            
            # 1. Traduce le battute
            battute_tradotte = await asyncio.to_thread(motore_ai.traduci_battute, stato_app['battute_totali'], "inglese")
            
            if battute_tradotte:
                stato_app['battute_totali'] = battute_tradotte
                # 2. Crea il video magico doppiato!
                await asyncio.to_thread(elaborazione.crea_video_multilingua, battute_tradotte, stato_app['durata_video'])
                ui.navigate.to('/multilingua')
            else:
                ui.notify('Errore nella traduzione del copione.', type='negative')

    with contenitore_giochi:
        ui.button('🧠 Quiz Pre-Doppiaggio', on_click=lambda: lancia_gioco('quiz')).classes('bg-blue-500 text-white font-bold h-32 w-64 text-xl rounded-2xl shadow-lg hover:scale-105 transition-transform')
        ui.button('🎙️ Doppiaggio Originale', on_click=lambda: lancia_gioco('doppiaggio')).classes('bg-red-500 text-white font-bold h-32 w-64 text-xl rounded-2xl shadow-lg hover:scale-105 transition-transform')
        ui.button('🌍 Doppiaggio Multilingua', on_click=lambda: lancia_gioco('multilingua')).classes('bg-green-600 text-white font-bold h-32 w-64 text-xl rounded-2xl shadow-lg hover:scale-105 transition-transform')
        ui.button('🗣️ Conversazione IA', on_click=lambda: lancia_gioco('conversazione')).classes('bg-gray-400 text-white font-bold h-32 w-64 text-xl rounded-2xl shadow-inner cursor-not-allowed')


# ==========================================
# 2. PAGINA ALLENAMENTO (Quiz)
# ==========================================
@ui.page('/allenamento')
def pagina_esercizi():
    quiz_data = stato_app.get('lista_quiz', [])
    
    if not quiz_data:
        ui.label('Nessun esercizio trovato.').classes('text-2xl mx-auto mt-10')
        ui.button('Torna alla Home', on_click=lambda: ui.navigate.to('/')).classes('mx-auto mt-4')
        return

    stato_quiz = {'indice': 0, 'punteggio': 0}

    ui.button('⬅️ Esci', on_click=lambda: ui.navigate.to('/')).classes('mt-4 ml-4 bg-gray-400')
    ui.label('🧠 Riscaldamento Linguistico').classes('text-4xl font-extrabold mx-auto mt-2 text-green-600')
    
    progresso = ui.label(f'Esercizio 1 di {len(quiz_data)}').classes('text-xl text-center mx-auto mb-6 text-gray-500 font-bold')
    card_esercizio = ui.column().classes('w-full max-w-2xl mx-auto items-center p-8 bg-white shadow-xl rounded-2xl border border-gray-100')
    
    def aggiorna_interfaccia():
        card_esercizio.clear()
        
        if stato_quiz['indice'] >= len(quiz_data):
            progresso.text = "Riscaldamento Completato!"
            with card_esercizio:
                ui.label('🎉 Ottimo Lavoro!').classes('text-5xl font-bold text-green-500 mb-4')
                ui.label(f'Punteggio Finale: {stato_quiz["punteggio"]}/{len(quiz_data)}').classes('text-2xl font-bold text-gray-700 mb-8')
                
                with ui.row().classes('w-full justify-center gap-6 mt-4'):
                    ui.button('🏠 Torna alla Home', on_click=lambda: ui.navigate.to('/')).classes('bg-gray-500 text-white text-xl font-bold px-6 py-4 rounded-full shadow-md')
                    ui.button('🎤 Vai al Doppiaggio', on_click=lambda: ui.navigate.to('/esercizio')).classes('bg-red-500 text-white text-xl font-bold px-6 py-4 rounded-full shadow-md')
            return

        esercizio_corrente = quiz_data[stato_quiz['indice']]
        progresso.text = f'Esercizio {stato_quiz["indice"] + 1} di {len(quiz_data)}'

        with card_esercizio:
            tipo_es = esercizio_corrente.get('tipo', 'completamento')
            if tipo_es == 'traduzione': prefisso = '🇮🇹🇬🇧 [Traduzione]'
            elif tipo_es == 'sinonimo': prefisso = '🔄 [Sinonimo]'
            else: prefisso = '🧩 [Completamento]'

            ui.label(prefisso).classes('text-lg font-bold text-blue-500 mb-2')
            ui.label(esercizio_corrente['domanda']).classes('text-2xl font-bold mb-6 text-gray-800 text-center')
            
            radio_scelta = ui.radio(esercizio_corrente['opzioni']).classes('w-full text-xl mb-6 ml-4')
            feedback_label = ui.label('').classes('text-xl font-bold mt-2 hidden')
            
            def verifica_risposta():
                if not radio_scelta.value:
                    ui.notify('Seleziona una risposta!', type='warning')
                    return
                btn_verifica.disable()
                radio_scelta.disable()
                feedback_label.classes(remove='hidden')
                
                if radio_scelta.value == esercizio_corrente['risposta_corretta']:
                    feedback_label.text = '✅ Corretto!'
                    feedback_label.classes(add='text-green-500')
                    stato_quiz['punteggio'] += 1
                else:
                    feedback_label.text = f"❌ Sbagliato! La risposta corretta era: {esercizio_corrente['risposta_corretta']}"
                    feedback_label.classes(add='text-red-500')
                
                btn_prossimo.classes(remove='hidden')

            with ui.row().classes('w-full justify-between items-center mt-4'):
                btn_verifica = ui.button('Verifica', on_click=verifica_risposta).classes('bg-blue-500 text-lg px-6 py-2')
                btn_prossimo = ui.button('Prossimo ➡️', on_click=prossimo_esercizio).classes('bg-gray-800 text-lg px-6 py-2 hidden')

    def prossimo_esercizio():
        stato_quiz['indice'] += 1
        aggiorna_interfaccia()

    aggiorna_interfaccia()

# ==========================================
# 3. LA PAGINA DEL DOPPIAGGIO ORIGINALE
# ==========================================
@ui.page('/esercizio')
def pagina_esercizio():
    if not stato_app['battute_totali']: carica_dati_video()
    battute = stato_app['battute_totali']
    
    ui.button('⬅️ Torna alla Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4 ml-4 bg-gray-400')
    ui.label('🎙️ Simulatore di Conversazione').classes('text-4xl font-extrabold mx-auto mt-2 text-gray-800')

    with ui.row().classes('w-full max-w-6xl mx-auto flex-nowrap items-stretch gap-8 mt-6'):
        with ui.column().classes('w-1/2 flex-col items-center'):
            timestamp = time.time()
            video = ui.video(f'/media/video_con_sottotitoli.mp4?t={timestamp}').style('width: 100%; max-height: 500px; border-radius: 12px; background: black;')
            sottotitolo = ui.label('In attesa...').classes('text-2xl text-center mt-6 font-bold text-gray-400 h-16')

            with ui.row().classes('mt-4 w-full justify-center'):
                btn_doppiaggio = ui.button('🗣️ Avvia Simulazione', on_click=lambda: avvia_conversazione()).classes('bg-red-500 text-xl font-bold px-8 py-4 rounded-full w-3/4')
            
            btn_vai_risultati = ui.button('📈 Vai al Report', on_click=lambda: ui.navigate.to('/risultati')).classes('bg-purple-600 mt-6 w-3/4 h-16 text-xl rounded-full')
            btn_vai_risultati.set_visibility(False)

        with ui.column().classes('w-1/2 bg-gray-50 rounded-2xl p-6 shadow-inner border border-gray-200 h-[600px] overflow-y-auto flex-nowrap relative'):
            ui.label('Copione Originale').classes('text-2xl font-bold mb-4 text-gray-800 sticky top-0 bg-gray-50 w-full pb-2 z-10')
            
            checkboxes = []
            righe_grafiche = [] 
            
            for i, b in enumerate(battute):
                with ui.row().classes('w-full items-center py-3 px-2 rounded-xl transition-all duration-300') as contenitore_riga:
                    cb = ui.checkbox('').classes('mr-3 transform scale-125') 
                    lbl = ui.label(b['text']).classes('text-xl text-gray-400 font-medium transition-all duration-300 cursor-pointer')
                    checkboxes.append(cb)
                    righe_grafiche.append({'riga': contenitore_riga, 'label': lbl})

    battute_da_doppiare_indici = []
    indice_precedente = -1
    
    async def gestisci_audio_dinamico():
        nonlocal indice_precedente
        tempo_corrente = await ui.run_javascript('let v = document.querySelector("video"); v ? v.currentTime : null;')
        if tempo_corrente is None: return

        in_battuta_utente = False
        testo_corrente = "..."
        indice_corrente = -1

        for i, b in enumerate(battute):
            if b['start'] <= tempo_corrente <= b['end']:
                indice_corrente = i
                if i in battute_da_doppiare_indici: in_battuta_utente = True
                testo_corrente = b['text']
                break

        if indice_corrente != indice_precedente and indice_corrente != -1:
            if indice_precedente != -1:
                righe_grafiche[indice_precedente]['label'].classes(remove='text-black text-3xl font-extrabold', add='text-gray-400 text-xl font-medium')
                righe_grafiche[indice_precedente]['riga'].classes(remove='bg-white shadow-md border border-gray-100')

            righe_grafiche[indice_corrente]['label'].classes(remove='text-gray-400 text-xl font-medium', add='text-black text-3xl font-extrabold')
            righe_grafiche[indice_corrente]['riga'].classes(add='bg-white shadow-md border border-gray-100')
            indice_precedente = indice_corrente

        if in_battuta_utente:
            await ui.run_javascript('document.querySelector("video").muted = true;')
            sottotitolo.text = f"🔴 TOCCA A TE!"
            sottotitolo.classes(replace='text-3xl text-center mt-6 font-extrabold text-red-600 h-16 animate-pulse')
        else:
            await ui.run_javascript('document.querySelector("video").muted = false;')
            sottotitolo.text = f"🔊 Ascolta..."
            sottotitolo.classes(replace='text-2xl text-center mt-6 font-bold text-blue-500 h-16')

    timer = ui.timer(0.05, gestisci_audio_dinamico, active=False)

    async def avvia_conversazione():
        nonlocal indice_precedente
        battute_da_doppiare_indici.clear()
        battute_da_doppiare_indici.extend([i for i, cb in enumerate(checkboxes) if cb.value])
        
        if not battute_da_doppiare_indici:
            ui.notify('Seleziona almeno una battuta!', type='warning', position='top')
            return

        stato_app['battute_scelte'] = [battute[i] for i in battute_da_doppiare_indici]

        btn_doppiaggio.disable()
        btn_vai_risultati.set_visibility(False)
        
        await ui.run_javascript('let v = document.querySelector("video"); v.currentTime = 0; v.play();')
        
        if indice_precedente != -1:
            righe_grafiche[indice_precedente]['label'].classes(remove='text-black text-3xl font-extrabold', add='text-gray-400 text-xl font-medium')
            righe_grafiche[indice_precedente]['riga'].classes(remove='bg-white shadow-md border border-gray-100')
            indice_precedente = -1

        timer.activate()
        audio_registrato = sd.rec(int(stato_app['durata_video'] * 44100), samplerate=44100, channels=1)
        await asyncio.sleep(stato_app['durata_video']) 
        sd.wait() 
        sf.write("voce_utente_completa.wav", audio_registrato, 44100)
        timer.deactivate()
        
        sottotitolo.text = "✅ Conversazione completata!"
        sottotitolo.classes(replace='text-3xl text-center mt-6 font-extrabold text-green-600 h-16')
        btn_doppiaggio.enable()
        btn_doppiaggio.text = '🔄 Rifai Conversazione'
        btn_vai_risultati.set_visibility(True)


# ==========================================
# 4. NUOVA PAGINA: DOPPIAGGIO MULTILINGUA (VIDEO COMPLETAMENTE TRADOTTO)
# ==========================================
@ui.page('/multilingua')
def pagina_multilingua():
    battute = stato_app.get('battute_totali', [])
    
    ui.button('⬅️ Torna alla Home', on_click=lambda: ui.navigate.to('/')).classes('mt-4 ml-4 bg-gray-400')
    ui.label('🌍 Doppiaggio in Lingua (Inglese)').classes('text-4xl font-extrabold mx-auto mt-2 text-green-700')

    with ui.row().classes('w-full max-w-6xl mx-auto flex-nowrap items-stretch gap-8 mt-6'):
        with ui.column().classes('w-1/2 flex-col items-center'):
            timestamp = time.time()
            # ATTENZIONE QUI: Carichiamo il video interamente ricreato con la voce dell'IA!
            video = ui.video(f'/media/video_multilingua.mp4?t={timestamp}').style('width: 100%; max-height: 500px; border-radius: 12px; background: black;')
            sottotitolo = ui.label('In attesa...').classes('text-2xl text-center mt-6 font-bold text-gray-400 h-16')

            with ui.row().classes('mt-4 w-full justify-center'):
                btn_doppiaggio = ui.button('🗣️ Avvia Simulazione', on_click=lambda: avvia_conversazione()).classes('bg-red-500 text-xl font-bold px-8 py-4 rounded-full w-3/4')
            
            btn_vai_risultati = ui.button('📈 Vai al Report', on_click=lambda: ui.navigate.to('/risultati')).classes('bg-purple-600 mt-6 w-3/4 h-16 text-xl rounded-full')
            btn_vai_risultati.set_visibility(False)

        with ui.column().classes('w-1/2 bg-green-50 rounded-2xl p-6 shadow-inner border border-green-200 h-[600px] overflow-y-auto flex-nowrap relative'):
            ui.label('Copione Tradotto (EN)').classes('text-2xl font-bold mb-4 text-green-800 sticky top-0 bg-green-50 w-full pb-2 z-10')
            
            checkboxes = []
            righe_grafiche = [] 
            
            for i, b in enumerate(battute):
                with ui.row().classes('w-full items-center justify-between py-3 px-2 rounded-xl transition-all duration-300') as contenitore_riga:
                    with ui.row().classes('items-center w-full'):
                        cb = ui.checkbox('').classes('mr-2 transform scale-110') 
                        lbl = ui.label(b['text']).classes('text-xl text-gray-500 font-medium transition-all duration-300 cursor-pointer')
                        checkboxes.append(cb)
                        righe_grafiche.append({'riga': contenitore_riga, 'label': lbl})

    battute_da_doppiare_indici = []
    indice_precedente = -1
    
    async def gestisci_audio_dinamico():
        nonlocal indice_precedente
        tempo_corrente = await ui.run_javascript('let v = document.querySelector("video"); v ? v.currentTime : null;')
        if tempo_corrente is None: return

        in_battuta_utente = False
        testo_corrente = "..."
        indice_corrente = -1

        for i, b in enumerate(battute):
            if b['start'] <= tempo_corrente <= b['end']:
                indice_corrente = i
                if i in battute_da_doppiare_indici: in_battuta_utente = True
                testo_corrente = b['text']
                break

        if indice_corrente != indice_precedente and indice_corrente != -1:
            if indice_precedente != -1:
                righe_grafiche[indice_precedente]['label'].classes(remove='text-black text-3xl font-extrabold', add='text-gray-500 text-xl font-medium')
                righe_grafiche[indice_precedente]['riga'].classes(remove='bg-white shadow-md border border-gray-100')

            righe_grafiche[indice_corrente]['label'].classes(remove='text-gray-500 text-xl font-medium', add='text-black text-3xl font-extrabold')
            righe_grafiche[indice_corrente]['riga'].classes(add='bg-white shadow-md border border-gray-100')
            indice_precedente = indice_corrente

        if in_battuta_utente:
            await ui.run_javascript('document.querySelector("video").muted = true;')
            sottotitolo.text = f"🔴 TOCCA A TE!"
            sottotitolo.classes(replace='text-3xl text-center mt-6 font-extrabold text-red-600 h-16 animate-pulse')
        else:
            await ui.run_javascript('document.querySelector("video").muted = false;')
            sottotitolo.text = f"🔊 Ascolta il tuo partner..."
            sottotitolo.classes(replace='text-2xl text-center mt-6 font-bold text-green-600 h-16')

    timer = ui.timer(0.05, gestisci_audio_dinamico, active=False)

    async def avvia_conversazione():
        nonlocal indice_precedente
        battute_da_doppiare_indici.clear()
        battute_da_doppiare_indici.extend([i for i, cb in enumerate(checkboxes) if cb.value])
        
        if not battute_da_doppiare_indici:
            ui.notify('Seleziona almeno una battuta!', type='warning', position='top')
            return

        stato_app['battute_scelte'] = [battute[i] for i in battute_da_doppiare_indici]

        btn_doppiaggio.disable()
        btn_vai_risultati.set_visibility(False)
        
        await ui.run_javascript('let v = document.querySelector("video"); v.currentTime = 0; v.play();')
        
        if indice_precedente != -1:
            righe_grafiche[indice_precedente]['label'].classes(remove='text-black text-3xl font-extrabold', add='text-gray-500 text-xl font-medium')
            righe_grafiche[indice_precedente]['riga'].classes(remove='bg-white shadow-md border border-gray-100')
            indice_precedente = -1

        timer.activate()
        audio_registrato = sd.rec(int(stato_app['durata_video'] * 44100), samplerate=44100, channels=1)
        await asyncio.sleep(stato_app['durata_video']) 
        sd.wait() 
        sf.write("voce_utente_completa.wav", audio_registrato, 44100)
        timer.deactivate()
        
        sottotitolo.text = "✅ Conversazione completata!"
        sottotitolo.classes(replace='text-3xl text-center mt-6 font-extrabold text-green-600 h-16')
        btn_doppiaggio.enable()
        btn_doppiaggio.text = '🔄 Rifai Conversazione'
        btn_vai_risultati.set_visibility(True)

# ==========================================
# 5. LA PAGINA DEI RISULTATI
# ==========================================
@ui.page('/risultati')
def pagina_risultati():
    ui.label('📈 Report della Conversazione').classes('text-4xl font-bold mx-auto mt-10 text-purple-700')
    ui.button('⬅️ Torna alla Home', on_click=lambda: ui.navigate.to('/')).classes('mx-auto mt-4 mb-8')

    container_risultati = ui.column().classes('w-full max-w-4xl mx-auto items-stretch')
    label_caricamento = ui.label('Analisi IA in corso...').classes('text-2xl text-center mx-auto text-orange-500 animate-pulse mt-10')

    battute_selezionate = stato_app['battute_scelte']
    testo_scelto_lista = [b['text'] for b in battute_selezionate]

    # Decidiamo su QUALE video montare la tua voce
    video_di_base = 'output/video_multilingua.mp4' if stato_app['modalita_corrente'] == 'multilingua' else 'output/video_con_sottotitoli.mp4'

    async def genera_report():
        label_caricamento.text = 'Fase 1/3: Ascolto microfono...'
        await asyncio.sleep(0.5) 
        testo_trascritto = await asyncio.to_thread(motore_ai.estrai_testo_da_audio, "voce_utente_completa.wav")
        
        label_caricamento.text = 'Fase 2/3: Valutazione in corso...'
        await asyncio.sleep(0.5) 
        report_finale = await asyncio.to_thread(motore_ai.genera_report_valutazione, testo_trascritto, testo_scelto_lista, stato_app['copione_originale'])
        
        label_caricamento.text = 'Fase 3/3: Montaggio del video in corso...'
        await asyncio.sleep(0.5)
        # Passiamo il video di base corretto all'algoritmo di montaggio!
        await asyncio.to_thread(elaborazione.monta_video_finale, battute_selezionate, video_di_base)
        label_caricamento.set_visibility(False)
        
        with container_risultati:
            ui.label('🎬 Rivedi la tua Performance!').classes('text-3xl font-bold mt-4 mb-2 text-center text-red-600')
            ui.video(f'/media/video_finale.mp4?t={time.time()}').style('width: 100%; max-height: 500px; border-radius: 12px; background: black;')

            with ui.row().classes('items-center mx-auto mt-4 mb-4 bg-gray-100 p-4 rounded-lg shadow-sm border border-gray-300'):
                nome_file_input = ui.input('Salva video come...', value='mio_doppiaggio').classes('w-64 text-lg')
                ui.label('.mp4').classes('text-xl mr-4 font-bold text-gray-500')
                ui.button('⬇️ Scarica Video', on_click=lambda: ui.download('output/video_finale.mp4', f"{nome_file_input.value}.mp4")).classes('bg-green-500 text-white font-bold')

        with container_risultati:
            ui.label('Valutazione dell\'IA:').classes('text-2xl font-bold mt-8 mb-2')
            ui.markdown(report_finale).classes('text-lg bg-gray-100 p-6 rounded-2xl shadow-sm text-black border border-gray-200')
            
        with container_risultati:
            ui.label('Le battute assegnate:').classes('text-2xl font-bold mt-8 mb-2')
            for b in testo_scelto_lista:
                ui.label(b).classes('text-lg font-semibold text-gray-800 bg-blue-50 w-full mb-2 p-3 border-l-4 border-blue-500 rounded')
            
            ui.label('Cosa ha capito il microfono:').classes('text-xl font-bold mt-6 mb-2 text-gray-600')
            ui.label(testo_trascritto).classes('text-lg italic text-gray-600 w-full mb-10 p-4 border-l-4 border-gray-400 bg-gray-50 rounded')

    ui.timer(0.5, genera_report, once=True)