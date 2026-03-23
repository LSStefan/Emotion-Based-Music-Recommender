import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
import re
from dotenv import load_dotenv

load_dotenv() # Încarcă variabilele din fișierul .env

client_id = os.getenv('SPOTIPY_CLIENT_ID')
client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')


# Încărcăm dataset-ul cel nou
df = pd.read_csv('spotify_dataset.csv',low_memory=False)

if os.path.exists(".cache"):
    os.remove(".cache")

scope = "playlist-modify-public playlist-modify-private user-read-currently-playing"

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    open_browser=False
))

def get_current_track_info():
    try:
        current_playback = sp.currently_playing()
        if current_playback is not None and current_playback['is_playing']:
            item = current_playback['item']
            track_name = item['name']
            artist_name = item['artists'][0]['name']
            track_id = item['id'] # EXTRAGEM ID-UL PENTRU CĂUTARE PRECISĂ
            
            print(f"🎶 Asculti acum: {track_name} - {artist_name}")
            return track_name, artist_name, track_id
        else:
            return None, None, None
    except Exception as e:
        print(f"⚠️ Eroare la citirea datelor live: {e}")
        return None, None, None

def get_metrics_from_csv(track_id, track_name, artist_name):
    # 1. Încercăm după ID (varianta precisă)
    result = df[df['track_id'] == track_id]
    
    if result.empty:
        # 2. Curățăm numele piesei (scoatem tot ce e după dash, paranteze sau ani)
        # "Rust In Peace...Polaris - 2004 Remix" devine "Rust In Peace...Polaris"
        clean_name = re.split(r' - | \(', track_name)[0].strip()
        
        print(f"🔍 Nu am găsit ID-ul. Încercăm căutare după nume curățat: '{clean_name}'")
        
        result = df[
            (df['track_name'].str.contains(re.escape(clean_name), case=False, na=False)) & 
            (df['artists'].str.contains(re.escape(artist_name), case=False, na=False))
        ]
    
    if not result.empty:
        # Luăm prima potrivire și afișăm ce am găsit în CSV pentru confirmare
        found_name = result.iloc[0]['track_name']
        v = result.iloc[0]['valence']
        e = result.iloc[0]['energy']
        print(f"✅ Potrivire găsită în Dataset: {found_name}")
        return v, e
    else:
        print(f"❌ Piesa '{track_name}' nu a fost găsită deloc în dataset.")
        return 0.5, 0.5

def check_and_analyze(t_name, a_name, t_id):
    v, e = get_metrics_from_csv(t_id, t_name, a_name)
    
    print(f"📊 Metricile din Dataset -> Valence: {v}, Energy: {e}")
    
    if v > 0.5 and e > 0.5:
        mood = "HAPPY/ENERGETIC"
    elif v < 0.5 and e < 0.5:
        mood = "SAD/CALM"
    else:
        mood = "NEUTRAL"
    print(f"🧠 Mood Detectat în Muzică: {mood}")



def create_mood_playlist(track_ids):
    try:
        # 1. Aflăm cine ești (ID-ul tău de utilizator)
        user_id = sp.me()['id']
        
        # 2. Creăm playlist-ul gol pe contul tău
        playlist_name = "MoodStream AI - Generat"
        new_playlist = sp.user_playlist_create(user=user_id, name=playlist_name, public=True)
        playlist_id = new_playlist['id']
        
        # 3. Adăugăm piesele (track_ids este o listă de ID-uri din CSV-ul tău)
        sp.playlist_add_items(playlist_id=playlist_id, items=track_ids)
        
        print(f"✅ Playlist creat cu succes! Îl poți vedea acum pe Spotify.")
        return playlist_id
        
    except Exception as e:
        print(f"❌ Eroare la crearea playlist-ului: {e}")
        return None


if __name__ == "__main__":
    # Rulăm ciclul complet
    t_name, a_name, t_id = get_current_track_info()
    
    if t_id:
        check_and_analyze(t_name, a_name, t_id)
    else:
        print("Nu se redă nicio piesă în acest moment.")

    