import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
import re
from dotenv import load_dotenv
import cv2
from deepface import DeepFace
import random
import lyrics_analyzer


# Profiluri emoție - caracteristici muzicale
EMOTION_PROFILE = {
    "happy": {
        "valence":      (0.7, 1.0),
        "energy":       (0.6, 1.0),
        "danceability": (0.6, 1.0),
        "tempo":        (100, 180),
    },
    "sad": {
        "valence":      (0.0, 0.3),
        "energy":       (0.0, 0.4),
        "danceability": (0.0, 0.4),
        "tempo":        (40, 100),
        "speechiness":  (0.03, 0.4),
    },
    "angry": {
        "valence":      (0.0, 0.4),
        "energy":       (0.7, 1.0),
        "danceability": (0.4, 0.8),
        "tempo":        (120, 200),
    },
    "neutral": {
        "valence":      (0.4, 0.6),
        "energy":       (0.3, 0.6),
        "danceability": (0.4, 0.6),
        "tempo":        (80, 130),
    },
    "surprise": {
        "valence":      (0.5, 0.9),
        "energy":       (0.6, 1.0),
        "danceability": (0.5, 0.9),
        "tempo":        (110, 180),
    },
    "fear": {
        "valence":      (0.0, 0.3),
        "energy":       (0.5, 0.8),
        "danceability": (0.0, 0.4),
        "tempo":        (60, 140),
    },
    "disgust": {
        "valence":      (0.0, 0.3),
        "energy":       (0.4, 0.7),
        "danceability": (0.0, 0.4),
        "tempo":        (60, 130),
    },
}

load_dotenv()

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Dataset
df = pd.read_csv('spotify_dataset.csv', low_memory=False)

# Definim scope-ul
scope = "playlist-modify-public playlist-modify-private user-read-currently-playing"

def initialize_spotify():
    """Funcție care inițializează Spotify DOAR după ce am curățat mediul"""
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=scope,
        open_browser=True,
        show_dialog=True 
    ))




# def create_playlist(sp_instance):
#     try:
    
#         me = sp_instance.me()
#         user_id = me['id']
#         print(f"--- Logat ca: {me['display_name']} ---")
#         print(f"Încercăm crearea pentru ID: {user_id}")
        
#         # Asa nu a mers
#         # playlist = sp_instance.user_playlist_create(
#         #     user=user_id, 
#         #     name="MoodStream AI Test", 
#         #     public=True, 
#         #     description="Creat de AI-ul lui Stefan"
#         # )

#         playlist = sp.current_user_playlist_create(
#             name="MoodStream AI Test", 
#             public=True, 
#             description="Creat de AI-ul lui Stefan"
#         )
        
#         print(f"SUCCES! Playlist creat: {playlist['id']}")

#         playlist_id = playlist['id']
#         print(f"Playlist creat: {playlist_id}")

#         # URI-uri piese (exemple)
#         tracks = [
#             "spotify:track:4uLU6hMCjMI75M1A2tKUQC",  # Never Gonna Give You Up
#             "spotify:track:1BxfuPKGuaTgP7aM0Bbdwr",  # Bohemian Rhapsody
#             "spotify:track:7qiZfU4dY1lWllzX7mPBI3",  # Shape of You
#         ]

#         # Adăugare piese
#         sp_instance.playlist_add_items(playlist_id, tracks)
#         print(f"{len(tracks)} piese adăugate cu succes!")

        
#     except Exception as e:
#         print(f"Eroare fatală: {e}")


def detect_emotion():
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Nu s-a putut deschide webcam-ul")
        return None

    print("--- Webcam pornit. Apasă 'q' pentru a captura emoția ---")
    detected_emotion = None
    result = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Eroare la citirea frame-ului")
            break

        try:
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False,
                silent=True
            )

            emotion = result[0]['dominant_emotion']
            emotions_all = result[0]['emotion']

            # Emotie dominantă
            cv2.putText(frame, f"Emotie: {emotion}",
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX,
                        1.2, (0, 255, 0), 2)

            # Toate scorurile
            y = 90
            for em, score in emotions_all.items():
                cv2.putText(frame, f"{em}: {score:.1f}%",
                            (30, y), cv2.FONT_HERSHEY_SIMPLEX,
                            0.5, (255, 255, 255), 1)
                y += 22

            # Dreptunghi fata
            region = result[0]['region']
            x, y_box = region['x'], region['y']
            w, h = region['w'], region['h']
            cv2.rectangle(frame, (x, y_box), (x+w, y_box+h), (0, 255, 0), 2)

        except Exception as e:
            cv2.putText(frame, "Nicio fata detectata", (30, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

        cv2.imshow("MoodStream - Detectare Emotie", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            if result:
                detected_emotion = result[0]['dominant_emotion']
                print(f"Emoție capturată: {detected_emotion}")
            else:
                print("Nicio față detectată la captură")
            break

    cap.release()
    cv2.destroyAllWindows()
    return detected_emotion




def get_tracks_for_emotion(emotion: str, df: pd.DataFrame, n: int = 11) -> pd.DataFrame:
    """
    Filtreaza datasetul și returneaza n piese potrivite pentru emotia data.
    """
    emotion = emotion.lower()

    if emotion not in EMOTION_PROFILE:
        print(f"Emoție necunoscută: {emotion}, folosim 'neutral'")
        emotion = "neutral"

    profile = EMOTION_PROFILE[emotion]

    # Filtrare dupa caracteristici
    filtered = df[
        (df['valence']      >= profile['valence'][0])      & (df['valence']      <= profile['valence'][1])      &
        (df['energy']       >= profile['energy'][0])       & (df['energy']       <= profile['energy'][1])       &
        (df['danceability'] >= profile['danceability'][0]) & (df['danceability'] <= profile['danceability'][1]) &
        (df['tempo']        >= profile['tempo'][0])        & (df['tempo']        <= profile['tempo'][1])
    ]

    print(f"Piese găsite pentru '{emotion}': {len(filtered)}")

    # Daca sunt prea putine, relaxam filtrele
    if len(filtered) < n:
        print("Prea puține piese, relaxăm filtrele...")
        filtered = df[
            (df['valence'] >= profile['valence'][0]) &
            (df['valence'] <= profile['valence'][1]) &
            (df['energy']  >= profile['energy'][0])  &
            (df['energy']  <= profile['energy'][1])
        ]

    # Selectam n piese random
    n = min(n, len(filtered))
    selected = filtered.sample(n=n, random_state=random.randint(0, 9999))

    return selected[['track_id', 'track_name', 'artists', 'valence', 'energy', 'danceability', 'tempo']]



def create_playlist_for_emotion(sp_instance, emotion: str, df: pd.DataFrame):
    """
    Creează un playlist pe Spotify folosind filtrarea hibridă:
    Dataset (Caracteristici Audio) + NLP (Analiză Versuri).
    """
    print(f"\n--- Procesare Recomandări pentru: {emotion.upper()} ---")

    # 1. Obținem un set mai mare de piese inițiale (ex: 20) pentru a avea de unde filtra prin NLP
    initial_tracks_df = get_tracks_for_emotion(emotion, df, n=20)

    if initial_tracks_df.empty:
        print("Nu s-au găsit piese în dataset.")
        return

    final_track_uris = []
    processed_count = 0
    target_count = 10 # Câte piese vrem să avem în playlist-ul final

    print("\n Validăm piesele prin Analiza Versurilor (NLP)...")
    
    for _, row in initial_tracks_df.iterrows():
        if len(final_track_uris) >= target_count:
            break
            
        artist = row['artists']
        track = row['track_name']
        track_id = row['track_id']

        # Apelăm modulul tău de versuri
        nlp_result = lyrics_analyzer.get_lyrics_and_sentiment(artist, track)
        
        # LOGICA DE FILTRARE HIBRIDĂ:
        # Dacă userul este SAD/DISGUST, evităm piesele cu Polarity prea mare (veselie forțată)
        # sau dacă este HAPPY, evităm piesele cu versuri Foarte Negative.
        
        keep_track = True
        if nlp_result['found']:
            polarity = nlp_result['polarity']
            
            # Exemplu de logică: Dacă ești HAPPY, nu vrem piese cu versuri "Foarte Negative"
            if emotion == "happy" and polarity < -0.4:
                print(f"  [Sarit] {track} - Versuri prea negative pentru starea Happy ({polarity})")
                keep_track = False
            
            # Dacă ești SAD, s-ar putea să vrei piese melancolice (nu le sărim), 
            # dar dacă vrei "Mood Boost", poți sări peste cele cu polarity < -0.5
            elif emotion == "sad" and polarity < -0.6:
                print(f"  [Sarit] {track} - Versuri mult prea depresive ({polarity})")
                keep_track = False

        if keep_track:
            print(f"  [Adaugat] {track} | Polarity NLP: {nlp_result['polarity'] if nlp_result['found'] else 'N/A'}")
            final_track_uris.append(f"spotify:track:{track_id}")

    # 3. Creăm playlist-ul pe Spotify
    if not final_track_uris:
        print("Nicio piesă nu a trecut de filtrele NLP.")
        return

    playlist_name = f"MoodStreamm - {emotion.capitalize()}"
    playlist = sp_instance.current_user_playlist_create(
        name=playlist_name,
        public=True,
        description=f"Playlist hibrid (Audio Features + NLP) pentru starea: {emotion}"
    )
    
    sp_instance.playlist_add_items(playlist['id'], final_track_uris)
    print(f"\nSUCCES! Playlist '{playlist_name}' creat cu {len(final_track_uris)} piese verificate.")

    return playlist['id']


if __name__ == "__main__":
    sp = initialize_spotify()
    
    emotion = detect_emotion()  # din emotion_detector.py
    #emotion = "disgust"  # pentru testare rapida
    
    if emotion:
        create_playlist_for_emotion(sp, emotion, df)

    