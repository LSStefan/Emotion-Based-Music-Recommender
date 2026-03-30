# 🎵 EMOTION-BASED-MUSIC-RECOMMENDER

**EMOTION-BASED-MUSIC-RECOMMENDER** este un sistem inteligent de recomandare muzicală care îmbină **Computer Vision**, **Natural Language Processing (NLP)** și **Spotify API** pentru a crea o experiență audio personalizată în funcție de starea de spirit a utilizatorului.

---

## 🚀 Caracteristici Principale

* **Detecție Facială în Timp Real:** Identificarea emoțiilor (Happy, Sad, Angry, Neutral, etc.) folosind camera web și biblioteca `DeepFace`.
* **Filtrare Hibridă de Date:**
    * **Audio Features:** Analiza metricilor de tip `Valence`, `Energy` și `Danceability` dintr-un dataset extins.
    * **Analiză Semantică (NLP):** Validarea mesajului pieselor prin extragerea versurilor (Genius Scraper) și clasificarea sentimentului cu modelul Transformer `RoBERTa`.
* **Sistem de Corecție Lexicală:** Algoritm hibrid care ajustează scorul AI pentru a înțelege corect genuri muzicale complexe (Metal, Grunge, Blues).
* **Integrare Spotify Cloud:** Generarea automată a playlist-urilor direct în contul utilizatorului prin protocolul OAuth 2.0.

---

## 🛠️ Tehnologii Utilizate

| Componentă          | Tehnologie                                       |
| :------------------ | :----------------------------------------------- |
| **Limbaj** | Python 3.13                                     |
| **AI (Viziune)** | OpenCV, DeepFace (TensorFlow backend)            |
| **AI (NLP)** | HuggingFace Transformers (RoBERTa Model)         |
| **Data Analysis** | Pandas, Numpy                                   |
| **API / Web** | Spotipy (Spotify API), BeautifulSoup4 (Scraping) |
| **Securitate** | Python-Dotenv                                   |

---

## 📂 Structura Proiectului

* `main.py`: Scriptul principal care coordonează fluxul logic (Cameră -> Dataset -> Spotify).
* `lyrics_analyzer.py`: Modulul pentru scraping-ul versurilor și procesarea NLP a sentimentelor.
* `spotify_dataset.csv`: Baza de date cu metadatele audio ale pieselor.
* `.env`: Fișier securizat pentru stocarea cheilor API (Client ID, Secret).

---

## ⚙️ Configurare și Instalare

1. **Clonarea depozitului:**
   ```bash
   git clone [https://github.com/licanstefan/EMOTION-BASED-MUSIC-RECOMMENDER.git](https://github.com/licanstefan/EMOTION-BASED-MUSIC-RECOMMENDER.git)
   cd EMOTION-BASED-MUSIC-RECOMMENDER

2. **Instalarea dependentelor**
    ```bash
    pip install spotipy pandas opencv-python deepface transformers torch beautifulsoup4 requests python-dotenv

3. **Configurarea credidentialelor**
    ```
    Creează un fișier .env în folderul rădăcină și adaugă:
    SPOTIPY_CLIENT_ID='id_ul_tau_aici'
    SPOTIPY_CLIENT_SECRET='secret_ul_tau_aici'
    SPOTIPY_REDIRECT_URI='[http://127.0.0.1:9090](http://127.0.0.1:9090)'

---

## 🖥️ Mod de Utilizare

**1. Ruleaza aplicatia**
```bash
python3 main.py
```
**2. Autorizare: Browser-ul se va deschide automat pentru a permite accesul aplicației la contul dumneavoastră de Spotify. Apăsați "Agree".**

**3. Captură: Camera web se activează. Priviți obiectivul și apăsați tasta q pentru a captura emoția curentă.**

**4. Generare: Sistemul va analiza piesele și va crea automat un playlist intitulat Mood: [Emotia Ta].**



## 📊 Metodologie (Data Fusion)

Proiectul implementează un sistem de validare în trei pași:

    Analiza Biometrică: Extragerea stării afective prin viziune artificială (DeepFace).

    Filtrarea Statistică: Selecția pieselor din dataset bazată pe corelația dintre emoție și atributele audio (ex: Tristețe -> Valence mic).

    Cross-Validation NLP: Utilizarea modelului twitter-roberta pentru a asigura că versurile nu contrazic starea dorită, eliminând astfel contradicțiile dintre ritm și mesajul textual.