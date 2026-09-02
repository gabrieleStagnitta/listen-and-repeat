import os
import json
import ffmpeg
import whisper
from gtts import gTTS

FILE_JSON = "output/dati_karaoke_completi.json"
FILE_VIDEO_SUB = "output/video_con_sottotitoli.mp4"

def format_time(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{milliseconds:03d}"

def prepara_ambiente(percorso_video, cancella_dopo_elaborazione=False):
    os.makedirs("input", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    print("\n--- FASE 1: TRASCRIZIONE DEL VIDEO ORIGINALE ---")
    modello_whisper = whisper.load_model("base") 
    
    audio_temp = "output/temp_audio_originale.wav"
    (
        ffmpeg
        .input(percorso_video)
        .output(audio_temp, acodec='pcm_s16le', ac=1, ar='16k')
        .run(overwrite_output=True, quiet=True)
    )

    result = modello_whisper.transcribe(audio_temp, language="en", fp16=False)
    
    battute = []
    for i, segment in enumerate(result["segments"]):
        battute.append({
            "id_battuta": f"Battuta_{i+1}",
            "start": round(segment["start"], 3),
            "end": round(segment["end"], 3),
            "text": segment["text"].strip()
        })

    with open(FILE_JSON, "w", encoding="utf-8") as f:
        json.dump(battute, f, indent=4, ensure_ascii=False)
        
    print("\n--- FASE 2: IMPRESSIONE SOTTOTITOLI SUL VIDEO ---")
    srt_path = "output/temp_subs.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, b in enumerate(battute, 1):
            start = format_time(b['start'])
            end = format_time(b['end'])
            f.write(f"{i}\n{start} --> {end}\n{b['text']}\n\n")
            
    (
        ffmpeg
        .input(percorso_video)
        .output(FILE_VIDEO_SUB, vf=f"subtitles={srt_path}", vcodec='libx264', acodec='copy')
        .run(overwrite_output=True, quiet=True)
    )

    os.remove(audio_temp)
    os.remove(srt_path)
    
    if cancella_dopo_elaborazione:
        try: os.remove(percorso_video)
        except Exception as e: print(f"Impossibile cancellare il file temporaneo: {e}")
            
    print("✅ Preparazione completata con successo!\n")
    return True

# --- NUOVA MAGIA: Generazione del video doppiato dall'IA (Tramite FFmpeg puro) ---
def crea_video_multilingua(battute_tradotte, durata_totale):
    print("\n--- CREAZIONE VIDEO BILINGUE IN CORSO (Via FFmpeg) ---")
    try:
        files_temp = []
        delayed_audios = []
        
        # 1. Creiamo una base silenziosa per dare la durata esatta al video finale
        base_muta = ffmpeg.input('anullsrc', f='lavfi', t=durata_totale).audio
        delayed_audios.append(base_muta)
        
        # 2. Generiamo e ritardiamo i file TTS di Google
        for i, b in enumerate(battute_tradotte):
            testo = b['text']
            start_ms = int(b['start'] * 1000) # FFmpeg calcola il ritardo in millisecondi
            temp_mp3 = f"output/temp_tts_{i}.mp3"
            
            tts = gTTS(text=testo, lang='en', slow=False)
            tts.save(temp_mp3)
            files_temp.append(temp_mp3)
            
            # Importiamo l'audio e applichiamo il ritardo ('adelay' sposta l'audio in avanti nel tempo)
            audio_in = ffmpeg.input(temp_mp3).audio
            delayed = audio_in.filter('adelay', f"{start_ms}|{start_ms}")
            delayed_audios.append(delayed)
            
        # 3. Mixiamo tutto insieme!
        num_inputs = len(delayed_audios)
        mixed_audio = (
            ffmpeg
            .filter(delayed_audios, 'amix', inputs=num_inputs)
            # amix abbassa il volume in automatico se ci sono tante tracce, quindi lo rialziamo al livello corretto:
            .filter('volume', str(num_inputs)) 
        )
        
        # 4. Uniamo al video originale
        in_video = ffmpeg.input(FILE_VIDEO_SUB)
        
        (
            ffmpeg
            .output(in_video.video, mixed_audio, 'output/video_multilingua.mp4', vcodec='copy', acodec='aac')
            .run(overwrite_output=True, quiet=True)
        )
        
        # Puliamo la cartella cancellando i file temporanei delle vocine
        for f in files_temp:
            os.remove(f)
            
        print("✅ Video multilingua creato con successo!")
        return True
    except Exception as e:
        print(f"❌ Errore durante la creazione del video multilingua: {e}")
        return False