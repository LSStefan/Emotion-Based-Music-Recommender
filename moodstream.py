import cv2
import numpy as np
import threading
import main
import lyrics_analyzer


CAM_W  = 720
CAM_H  = 480
LOG_H  = 260
WIN_W  = CAM_W
WIN_H  = CAM_H + LOG_H


BG_DARK    = (18,  18,  24)
BG_PANEL   = (26,  26,  36)
BG_ROW_ALT = (32,  32,  44)
GREEN      = (80,  200,  80)
YELLOW     = (40,  180, 220)
RED        = (60,  60, 210)
WHITE      = (230, 230, 230)
GRAY       = (130, 130, 150)
ACCENT     = (50,  185, 100)

EMOTION_COLORS = {
    "happy":    (0,   200, 100),
    "sad":      (200,  80,  20),
    "angry":    (30,   30, 220),
    "neutral":  (140, 140, 140),
}

FONT      = cv2.FONT_HERSHEY_SIMPLEX
FONT_MONO = cv2.FONT_HERSHEY_PLAIN

#functii pentru desenare UI

def draw_rounded_rect(img, x1, y1, x2, y2, color, radius=8, thickness=-1):
    # Desenăm corpul dreptunghiului (fără colțuri)
    cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, thickness)
    cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, thickness)
    
    # desen colturi rotunjite
    puncte_colturi = [
        (x1 + radius, y1 + radius), 
        (x2 - radius, y1 + radius),
        (x1 + radius, y2 - radius), 
        (x2 - radius, y2 - radius)
    ]
    for centru in puncte_colturi:
        cv2.circle(img, centru, radius, color, thickness)

def draw_camera_overlay(frame, result, hint):
    """Deseneaza bounding box, emotie dominanta, bare scoruri si hint pe frame."""
    if result:
        # Extragem datele din primul rezultat 
        fata = result[0]
        emotion = fata['dominant_emotion']
        scores  = fata['emotion']
        region  = fata['region']
        
        ecol = EMOTION_COLORS.get(emotion, (200, 200, 200))

        # Bounding box fata
        x, y, w, h = region['x'], region['y'], region['w'], region['h']
        cv2.rectangle(frame, (x, y), (x + w, y + h), ecol, 2)

        # Eticheta emotie deasupra fetei
        lbl = emotion.upper()
        marime_text = cv2.getTextSize(lbl, FONT, 0.7, 2)[0]
        tw, th = marime_text[0], marime_text[1]
        
        draw_rounded_rect(frame, x, y - th - 14, x + tw + 12, y - 2, ecol, radius=5)
        cv2.putText(frame, lbl, (x + 6, y - 6), FONT, 0.7, BG_DARK, 2, cv2.LINE_AA)

        # Bare scoruri top 4
        items = list(scores.items())
        # Sortam dupa scor
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][1] < items[j][1]:
                    items[i], items[j] = items[j], items[i]
        
        sorted_scores = items[:4]
        
        bx = CAM_W - 185
        for index, date_emotie in enumerate(sorted_scores):
            em_nume = date_emotie[0]
            em_scor = date_emotie[1]
            
            bcol = EMOTION_COLORS.get(em_nume, GRAY)
            bar_w = int(em_scor * 1.5)
            by_cur = 12 + index * 28
            
            # Afisare nume emotie
            cv2.putText(frame, em_nume[:7], (bx, by_cur + 13), FONT, 0.38, WHITE, 1, cv2.LINE_AA)
            # Fundal bara
            cv2.rectangle(frame, (bx + 58, by_cur + 2), (bx + 208, by_cur + 16), (50, 50, 60), -1)
            # Bara progres
            cv2.rectangle(frame, (bx + 58, by_cur + 2), (bx + 58 + bar_w, by_cur + 16), bcol, -1)
            # Procentaj
            cv2.putText(frame, f"{em_scor:.0f}%", (bx + 212, by_cur + 13), FONT, 0.35, GRAY, 1, cv2.LINE_AA)

    # Hint tasta
    cv2.putText(frame, hint, (10, CAM_H - 12), FONT, 0.48, ACCENT, 1, cv2.LINE_AA)
    return frame

def draw_log_panel(canvas, logs, emotion, phase):
    """Deseneaza panoul de jos cu header, emotie detectata si linii de log."""
    y0 = CAM_H

    # Fundal panou loguri
    cv2.rectangle(canvas, (0, y0), (WIN_W, WIN_H), BG_PANEL, -1)
    cv2.line(canvas, (0, y0), (WIN_W, y0), ACCENT, 2)

    # Header aplicatie
    header_h = 36
    cv2.rectangle(canvas, (0, y0), (WIN_W, y0 + header_h), BG_DARK, -1)
    cv2.putText(canvas, "MoodStream", (14, y0 + 24), FONT, 0.55, ACCENT, 1, cv2.LINE_AA)

    # Status fază procesare
    phase_colors = {"camera": YELLOW, "processing": (80, 160, 255), "done": GREEN}
    phase_labels = {"camera": "DETECTARE EMOTIE", "processing": "GENERARE PLAYLIST", "done": "FINALIZAT"}
    
    pcol = phase_colors.get(phase, GRAY)
    plbl = phase_labels.get(phase, "")
    
    # Calculare pozitie text status
    marime_plbl = cv2.getTextSize(plbl, FONT, 0.42, 1)[0]
    tw = marime_plbl[0]
    
    cv2.circle(canvas, (WIN_W - tw - 22, y0 + 18), 5, pcol, -1)
    cv2.putText(canvas, plbl, (WIN_W - tw - 14, y0 + 24), FONT, 0.42, pcol, 1, cv2.LINE_AA)

    # afisez emotia detectata
    ey = y0 + header_h + 6
    if emotion:
        ecol = EMOTION_COLORS.get(emotion, GRAY)
        draw_rounded_rect(canvas, 10, ey, 300, ey + 26, ecol, radius=6)
        cv2.putText(canvas, f"Emotie detectata:  {emotion.upper()}",
                    (18, ey + 18), FONT, 0.48, BG_DARK, 1, cv2.LINE_AA)
    else:
        cv2.putText(canvas, "Emotie detectata:  ---",
                    (14, ey + 18), FONT, 0.48, GRAY, 1, cv2.LINE_AA)

    # gesionare si afisare loguri (ultimele n linii)
    log_y_start = ey + 34
    line_h = 22
    # cate linii de log incap in zona vizibila
    max_lines = int((WIN_H - log_y_start - 6) / line_h)
    
    # luam ultimele linii de log care incap in zona
    visible = []
    if len(logs) > max_lines:
        visible = logs[-max_lines:]
    else:
        visible = logs

    icons  = {"ok": "OK", "skip": "->", "info": "..", "err": "!!"}
    colors = {"ok": GREEN, "skip": YELLOW, "info": (160, 160, 180), "err": RED}

    for index, log_data in enumerate(visible):
        text = log_data[0]
        kind = log_data[1]
        
        ly = log_y_start + index * line_h
        
        # Alternare culoare rand pentru lizibilitate
        if index % 2 == 0:
            cv2.rectangle(canvas, (0, ly), (WIN_W, ly + line_h - 1), BG_ROW_ALT, -1)
        
        color = colors.get(kind, GRAY)
        icon_str = icons.get(kind, '..')
        
        cv2.putText(canvas, f"[{icon_str}]", (8, ly + 15), FONT_MONO, 0.95, color, 1, cv2.LINE_AA)
        
        # daca e prea lung, trunchiem textul si adaugam "..."
        if len(text) > 95:
            display_text = text[:95] + "..."
        else:
            display_text = text
            
        cv2.putText(canvas, display_text, (58, ly + 15), FONT_MONO, 0.95, WHITE, 1, cv2.LINE_AA)


def generate_playlist_thread(sp, emotion, logs, phase_ref):
    phase_ref[0] = "processing"
    logs.append((f"Emotie capturata: {emotion.upper()}", "info"))
    logs.append(("Filtrare piese din dataset...", "info"))

    # obtine piese candidate pentru emotia detectata
    initial = main.get_tracks_for_emotion(emotion, main.df, n=20)
    logs.append((f"{len(initial)} piese candidate gasite", "info"))

    uris = []
    target_count = 10

    for index, row in initial.iterrows():
        if len(uris) >= target_count:
            break

        track_name = row['track_name']
        artist_name = row['artists']
        track_id = row['track_id']

        logs.append((f"NLP: {artist_name[:25]} - {track_name[:30]}", "info"))

        # Analiza versuri + polaritate folosind Lyrics Analyzer
        nlp_data = lyrics_analyzer.get_lyrics_and_sentiment(artist_name, track_name)
        keep_song = True

        if nlp_data['found']:
            polarity = nlp_data['polarity']
            # Filtru: daca esti fericit, nu vrem versuri prea negative
            if emotion == "happy" and polarity < -0.4:
                logs.append((f"Sarit: {track_name[:40]} (prea negativ {polarity:.2f})", "skip"))
                keep_song = False
            # Filtru: daca esti trist, nu vrem versuri prea depresive
            elif emotion == "sad" and polarity < -0.6:
                logs.append((f"Sarit: {track_name[:40]} (prea depresiv {polarity:.2f})", "skip"))
                keep_song = False

        if keep_song:
            # Formatare text polaritate pentru log
            if nlp_data['found']:
                pol_str = f"{nlp_data['polarity']:+.2f}"
            else:
                pol_str = "N/A"
                
            logs.append((f"Adaugat: {track_name[:40]} [{pol_str}]", "ok"))
            uris.append(f"spotify:track:{track_id}")

    # Creare playlist pe Spotify
    if len(uris) > 0:
        nume_playlist = f"MoodStream - {emotion.capitalize()}"
        descriere = f"Playlist MoodStream pentru starea: {emotion}"
        
        pl = sp.current_user_playlist_create(
            name=nume_playlist, 
            public=True,
            description=descriere
        )
        sp.playlist_add_items(pl['id'], uris)
        
        logs.append((f"Playlist '{nume_playlist}' creat cu {len(uris)} piese!", "ok"))
        logs.append(("Apasa Q pentru a iesi.", "info"))
    else:
        logs.append(("Nicio piesa nu a trecut filtrele NLP.", "err"))

    phase_ref[0] = "done"


def run():
    sp = main.initialize_spotify()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Webcam-ul nu a putut fi deschis.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAM_W)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_H)

    cv2.namedWindow("MoodStream", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("MoodStream", WIN_W, WIN_H)

    logs = [
        ("Pornire MoodStream...", "info"),
        ("Pozitioneaza-te in fata camerei si apasa Q.", "info")
    ]
    
    last_result = []
    captured_emotion = [None]  # Lista pentru a putea modifica valoarea din thread
    phase_ref = ["camera"]
    running = True

    while running:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame = cv2.resize(frame, (CAM_W, CAM_H))

        # DeepFace ruleaza doar in faza de camera pentru a detecta emotia in timp real
        if phase_ref[0] == "camera":
            try:
                last_result = main.DeepFace.analyze(
                    frame, 
                    actions=['emotion'],
                    enforce_detection=False, 
                    silent=True
                )
            except Exception:
                pass

        # Selectam ce hint sa afisam in partea de jos in functie de faza curenta
        hints = {
            "camera":     "Q - captureaza emotia si genereaza playlist  |  ESC - iesire",
            "processing": "Se genereaza playlist-ul, asteptati...",
            "done":       "Gata!  Apasa Q pentru a iesi.",
        }
        hint_text = hints.get(phase_ref[0], "")

        # Determinam ce emotie sa afisam in panoul de jos
        if captured_emotion[0] is not None:
            display_emotion = captured_emotion[0]
        elif len(last_result) > 0:
            display_emotion = last_result[0]['dominant_emotion']
        else:
            display_emotion = None

        # Overlay pe imaginea camerei
        camera_data = []
        if phase_ref[0] == "camera":
            camera_data = last_result
            
        draw_camera_overlay(frame, camera_data, hint_text)

        # Creare fundal negru si asamblare componente
        canvas = np.zeros((WIN_H, WIN_W, 3), dtype=np.uint8)
        canvas[0:CAM_H, 0:CAM_W] = frame
        draw_log_panel(canvas, logs, display_emotion, phase_ref[0])

        cv2.imshow("MoodStream", canvas)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q') or key == ord('Q'):
            if phase_ref[0] == "camera":
                if len(last_result) > 0:
                    emotion_now = last_result[0]['dominant_emotion']
                    captured_emotion[0] = emotion_now
                    
                    # Pornim thread-ul pentru a nu bloca imaginea camerei
                    t = threading.Thread(
                        target=generate_playlist_thread,
                        args=(sp, emotion_now, logs, phase_ref),
                        daemon=True
                    )
                    t.start()
                else:
                    logs.append(("Nicio fata detectata. Incearca din nou.", "err"))

            elif phase_ref[0] == "done":
                running = False

        if key == 27:  # Tasta ESC
            running = False

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run()