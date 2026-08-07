import streamlit as st
import json
import os
import random
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="Kurs Hiszpańskiego A1", page_icon="🇪🇸", layout="centered")

# Lista Twoich grafik wrzuconych do folderu assets
BG_IMAGES = [
    "1000049108.png", "1000049109.png", "1000049110.png", 
    "1000049111.png", "1000049112.png", "1000049113.png"
]

def get_base64_of_bin_file(bin_file):
    """Odczytuje plik graficzny i konwertuje go na base64 (wymóg Streamlit dla tła CSS)"""
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_random_background():
    """Losuje i ustawia tło przy każdym odświeżeniu widoku"""
    bg_image = random.choice(BG_IMAGES)
    file_path = os.path.join("assets", bg_image)
    
    try:
        bin_str = get_base64_of_bin_file(file_path)
        page_bg_img = f"""
        <style>
        .stApp {{
            background-image: url("data:image/png;base64,{bin_str}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            transition: background-image 0.5s ease-in-out;
        }}
        /* Główny kontener z lekkim prześwitem, by tekst był czytelny na tytle */
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.90);
            padding: 2rem 3rem;
            border-radius: 15px;
            margin-top: 2rem;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.2);
        }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Nie znaleziono pliku tła: {file_path}")

def load_data():
    """Wczytuje pliki JSON do pamięci podręcznej"""
    with open(os.path.join("data", "A1", "lekcja_01.json"), "r", encoding="utf-8") as f:
        lesson_data = json.load(f)
    with open(os.path.join("data", "user_progress.json"), "r", encoding="utf-8") as f:
        progress_data = json.load(f)
    return lesson_data, progress_data

def main():
    # Odpalenie dynamicznego tła
    set_random_background()
    
    # Wczytanie danych
    lesson_data, progress_data = load_data()
    
    # Nagłówek aplikacji
    st.title(f"🇪🇸 {lesson_data['lesson_metadata']['title']}")
    st.caption(f"Poziom: {lesson_data['lesson_metadata']['level']}")
    
    # Nawigacja (Zakładki)
    tab1, tab2, tab3 = st.tabs(["📖 Teoria i Dialogi", "🧠 Fiszki (Tryb SuperMemo)", "📝 Ćwiczenia"])
    
    with tab1:
        st.subheader(lesson_data['sections']['dialog']['title'])
        for line in lesson_data['sections']['dialog']['content']:
            st.write(f"**{line['speaker']}**: {line['text']}")
            
        st.markdown("---")
        st.subheader(lesson_data['sections']['grammar']['title'])
        st.info(lesson_data['sections']['grammar']['explanation'])
        st.table(lesson_data['sections']['grammar']['table'])
        
    with tab2:
        st.subheader("Tryb Powtórek")
        st.warning("Mechanika wyliczania interwałów (SuperMemo-2) zostanie zaimplementowana w kolejnym kroku.")
        
    with tab3:
        st.subheader("Sprawdź wiedzę")
        st.warning("Logika sprawdzania odpowiedzi z luki zostanie dodana w kolejnym kroku.")

if __name__ == "__main__":
    main()
