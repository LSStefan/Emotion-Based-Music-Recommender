import requests
from bs4 import BeautifulSoup
import re
import time
from transformers import pipeline

# 1. Initializare Pipeline NLP (RoBERTa)
# Folosim modelul de sentiment antrenat pe Twitter
sentiment_pipeline = pipeline(
    "text-classification",
    model="cardiffnlp/twitter-roberta-base-sentiment-latest",
    truncation=True,
    max_length=512
)

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

def clean_name(text: str) -> str:
    """Curata numele piesei/artistului pentru a imbunatati cautarea pe Genius."""
    text = str(text)
    # Elimina parantezele, textul dintre paranteze patrate si mentiunile de 'feat'
    text = re.sub(r'\(.*?\)|\[.*?\]', '', text)
    text = re.sub(r'feat\..*|ft\..*|remastered|remaster|20\d{2}', '', text, flags=re.IGNORECASE)
    return text.strip()

def get_genius_lyrics(artist: str, track_name: str) -> str | None:
    """Extrage versurile de pe Genius folosind Web Scraping."""
    artist_clean = clean_name(artist)
    track_clean = clean_name(track_name)
    
    query = f"{artist_clean} {track_clean}".replace(' ', '%20')
    search_url = f"https://genius.com/api/search/multi?per_page=1&q={query}"
    
    try:
        response = requests.get(search_url, headers=headers, timeout=5)
        data = response.json()
        
        # Cautam sectiunea de tip 'song' in rezultate
        song_section = next((s for s in data['response']['sections'] if s['type'] == 'song'), None)
        if not song_section or not song_section['hits']:
            return None
        
        song_url = song_section['hits'][0]['result']['url']
        
        # Scraping pagina de versuri
        page = requests.get(song_url, headers=headers, timeout=5)
        soup = BeautifulSoup(page.text, 'html.parser')
        
        # Genius foloseste containere cu atributul data-lyrics-container
        lyrics_divs = soup.find_all('div', attrs={'data-lyrics-container': 'true'})
        if not lyrics_divs:
            return None
        
        lyrics_parts = [div.get_text(separator='\n') for div in lyrics_divs]
        raw_lyrics = '\n'.join(lyrics_parts)
        
        # Curatare metadate (ex: [Chorus], [Bridge])
        clean_lyrics = re.sub(r'\[.*?\]', '', raw_lyrics)
        return clean_lyrics.strip()
        
    except Exception:
        return None

def analyze_sentiment(lyrics: str) -> dict:
    """Analizeaza sentimentul combinand AI-ul cu reguli lexicale (Heuristici)."""
    if not lyrics:
        return {'polarity': 0.0, 'label': 'neutral'}
    
    # --- PASUL A: Analiza prin Modelul Transformer ---
    # Cerem toate scorurile pentru a calcula polaritatea neta
    raw_results = sentiment_pipeline(lyrics[:1000], top_k=None)
    scores = {res['label'].lower(): res['score'] for res in raw_results}
    
    # Polaritate bruta: Pozitiv minus Negativ
    ai_polarity = scores.get('positive', 0) - scores.get('negative', 0)
    
    # --- PASUL B: Corectie prin Dictionar de Context (Sistem Hibrid) ---
    # Cuvinte care indica tristete profunda sau agresivitate (frecvente in Metal/Grunge)
    sad_keywords = ['alone', 'hollow', 'shell', 'broken', 'dead', 'dark', 'cold', 'pain', 
                    'lies', 'empty', 'lonely', 'buried', 'hurt', 'dirt', 'mad', 'tear', 'cry', 'shame']
    
    aggressive_keywords = ['blood', 'death', 'kill', 'hell', 'war', 'suicide', 'hate', 'suffocate', 'suffering']
    
    lyrics_lower = lyrics.lower()
    penalty = 0
    
    for word in sad_keywords:
        if word in lyrics_lower:
            penalty += 0.04 # Scadere usoara pentru melancolie
            
    for word in aggressive_keywords:
        if word in lyrics_lower:
            penalty += 0.08 # Scadere mai mare pentru agresivitate/death metal
            
    # Calculam polaritatea finala (Clasificator Hibrid)
    final_polarity = ai_polarity - penalty
    final_polarity = max(-1.0, min(1.0, final_polarity)) # Limitam intre -1 si 1
    
    # Determinam eticheta finala pe baza scorului ajustat
    if final_polarity <= -0.1:
        label = 'negative'
    elif final_polarity >= 0.1:
        label = 'positive'
    else:
        label = 'neutral'
        
    return {
        'polarity': round(final_polarity, 3),
        'label': label,
        'ai_raw': round(ai_polarity, 3)
    }

def get_lyrics_and_sentiment(artist: str, track_name: str, delay: float = 0.3) -> dict:
    """Functie principala care returneaza datele complete pentru o piesa."""
    lyrics = get_genius_lyrics(artist, track_name)
    sentiment = analyze_sentiment(lyrics)
    
    if delay > 0:
        time.sleep(delay) # Prevenim blocarea IP-ului de catre Genius
        
    return {
        'lyrics_sample': lyrics[:100] + "..." if lyrics else None,
        'polarity': sentiment['polarity'],
        'label': sentiment['label'],
        'found': lyrics is not None
    }

def sentiment_to_emotion(polarity: float) -> str:
    """Traduce scorul numeric intr-o descriere vizuala fara emoji."""
    if polarity > 0.4: return "Extrem de Pozitiv / Euphoric"
    if 0.1 < polarity <= 0.4: return "Vesel / Optimist"
    if -0.1 <= polarity <= 0.1: return "Echilibrat / Neutru"
    if -0.4 <= polarity < -0.1: return "Melancolic / Trist"
    return "Foarte Negativ / Agresiv"

# --- ZONA DE TESTARE ---
if __name__ == "__main__":
    test_songs = [
        ("Pharrell Williams", "Happy"),
        ("Queen", "Don't Stop Me Now"),
        ("Zillakami", "Hello"),
        ("Slayer", "Raining Blood"),
        ("Alice in Chains", "Nutshell"),
        ("Johnny Cash", "Hurt"),
        ("Gary Jules", "Mad World"),
        ("Enya", "Only Time")
    ]
    
    print(f"{'ARTIST & PIESA':<40} | {'POLARITY':<10} | {'EMOTIE'}")
    print("-" * 80)
    
    for artist, track in test_songs:
        res = get_lyrics_and_sentiment(artist, track)
        if res['found']:
            emotion = sentiment_to_emotion(res['polarity'])
            print(f"{artist + ' - ' + track:<40} | {res['polarity']:<10} | {emotion}")
        else:
            print(f"{artist + ' - ' + track:<40} | Versuri negasite")