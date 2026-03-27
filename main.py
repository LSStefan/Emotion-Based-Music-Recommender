import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
import re
from dotenv import load_dotenv
import cv2
from deepface import DeepFace


load_dotenv()

# Citim variabilele
client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')

# Dataset-ul
df = pd.read_csv('spotify_dataset.csv', low_memory=False)

# Definim scope-ul clar
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




def create_playlist(sp_instance):
    try:
    
        me = sp_instance.me()
        user_id = me['id']
        print(f"--- Logat ca: {me['display_name']} ---")
        print(f"Încercăm crearea pentru ID: {user_id}")
        
        # Asa nu a mers
        # playlist = sp_instance.user_playlist_create(
        #     user=user_id, 
        #     name="MoodStream AI Test", 
        #     public=True, 
        #     description="Creat de AI-ul lui Stefan"
        # )

        playlist = sp.current_user_playlist_create(
            name="MoodStream AI Test", 
            public=True, 
            description="Creat de AI-ul lui Stefan"
        )
        
        print(f"✅ SUCCES! Playlist creat: {playlist['id']}")

        playlist_id = playlist['id']
        print(f"✅ Playlist creat: {playlist_id}")

        # URI-uri piese (exemple)
        tracks = [
            "spotify:track:4uLU6hMCjMI75M1A2tKUQC",  # Never Gonna Give You Up
            "spotify:track:1BxfuPKGuaTgP7aM0Bbdwr",  # Bohemian Rhapsody
            "spotify:track:7qiZfU4dY1lWllzX7mPBI3",  # Shape of You
        ]

        # Adăugare piese
        sp_instance.playlist_add_items(playlist_id, tracks)
        print(f"✅ {len(tracks)} piese adăugate cu succes!")

        
    except Exception as e:
        print(f"❌ Eroare fatală: {e}")


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

            # Emoție dominantă
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

            # Dreptunghi față
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



if __name__ == "__main__":
    if os.path.exists(".cache"):
        try:
            os.remove(".cache")
            print("--- Fișier .cache șters cu succes ---")
        except:
            pass


    #sp = initialize_spotify()
    #create_playlist(sp)

    # detectare emotie
    emotion = detect_emotion()
    print(f"Emoție detectata: {emotion}")

    