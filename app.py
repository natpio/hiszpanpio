import streamlit as st
import json
import os
import random
import base64
from datetime import datetime, timedelta

# 1. Konfiguracja strony
st.set_page_config(page_title="Kurs Hiszpańskiego A1", page_icon="🇪🇸", layout="centered")

BG_IMAGES = [
    "1000049108.png", "1000049109.png", "1000049110.png", 
    "1000049111.png", "1000049112.png", "1000049113.png"
]

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_random_background():
    """Losuje tło przy każdym przeładowaniu (np. przy obrocie fiszki)"""
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
            transition: background-image 0.4s ease-in-out;
        }}
        .main .block-container {{
            background-color: rgba(255, 255, 255, 0.92);
            padding: 2.5rem;
            border-radius: 15px;
            margin-top: 2rem;
            box-shadow: 0px 8px 25px rgba(0,0,0,0.3);
        }}
        /* Stylizacja karty fiszki */
        .flashcard-front {{ text-align: center; font-size: 24px; font-weight: 500; color: #2C3E50; margin-bottom: 20px; }}
        .flashcard-back {{ text-align: center; font-size: 32px; font-weight: bold; color: #E74C3C; margin-bottom: 30px; }}
        </style>
        """
        st.markdown(page_bg_img, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def load_data():
    with open(os.path.join("data", "A1", "lekcja_01.json"), "r", encoding="utf-8") as f:
        lesson_data = json.load(f)
    with open(os.path.join("data", "user_progress.json"), "r", encoding="utf-8") as f:
        progress_data = json.load(f)
    return lesson_data, progress_data

def save_progress(progress_data):
    """Zapisuje postępy z powrotem do pliku JSON"""
    with open(os.path.join("data", "user_progress.json"), "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=4)

def calculate_sm2(quality, repetitions, ease_factor, interval):
    """Algorytm SuperMemo-2 do obliczania kolejnej daty powtórki"""
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = round(interval * ease_factor)
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    
    ease_factor = max(1.3, ease_factor)
    return repetitions, ease_factor, interval

def main():
    set_random_background()
    lesson_data, progress_data = load_data()
    
    # Inicjalizacja stanu sesji dla fiszek
    if 'current_card' not in st.session_state:
        st.session_state.current_card = 0
    if 'show_answer' not in st.session_state:
        st.session_state.show_answer = False
    
    st.title(f"🇪🇸 {lesson_data['lesson_metadata']['title']}")
    
    tab1, tab2, tab3 = st.tabs(["📖 Teoria", "🧠 Fiszki (Tryb SuperMemo)", "📝 Ćwiczenia"])
    
    # --- ZAKŁADKA 1: TEORIA ---
    with tab1:
        st.subheader(lesson_data['sections']['dialog']['title'])
        for line in lesson_data['sections']['dialog']['content']:
            st.write(f"**{line['speaker']}**: {line['text']}")
            
        st.markdown("---")
        st.subheader(lesson_data['sections']['grammar']['title'])
        st.info(lesson_data['sections']['grammar']['explanation'])
        st.table(lesson_data['sections']['grammar']['table'])
        
    # --- ZAKŁADKA 2: FISZKI I SRS ---
    with tab2:
        st.subheader("Tryb Powtórek")
        today_str = datetime.now().strftime("%Y-%m-%d")
        
        # Filtrujemy fiszki: szukamy nowych lub tych, którym minął termin powtórki
        due_cards = []
        for card in lesson_data['sections']['flashcards']:
            c_id = card['id']
            if c_id not in progress_data:
                due_cards.append(card)
            elif progress_data[c_id]['next_review'] <= today_str:
                due_cards.append(card)
        
        if not due_cards:
            st.success("🎉 Świetna robota! Przerobiłeś wszystkie słówka na dzisiaj. Wróć jutro!")
            if st.button("Zresetuj dzisiejszą sesję (Tylko do testów)"):
                st.session_state.clear()
                st.rerun()
        else:
            # Mechanika wyświetlania fiszki
            if st.session_state.current_card >= len(due_cards):
                st.session_state.current_card = 0
                
            active_card = due_cards[st.session_state.current_card]
            
            st.markdown(f"<div class='flashcard-front'>{active_card['pl']}</div>", unsafe_allow_html=True)
            
            if not st.session_state.show_answer:
                if st.button("Pokaż odpowiedź", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun() # Przeładowanie wyzwoli też zmianę tła!
            else:
                st.markdown(f"<div class='flashcard-back'>{active_card['es']}</div>", unsafe_allow_html=True)
                
                st.write("Jak dobrze pamiętałeś to słówko?")
                col1, col2, col3, col4 = st.columns(4)
                
                # Przetwarzanie odpowiedzi użytkownika
                def process_answer(quality):
                    c_id = active_card['id']
                    # Jeśli słówko jest nowe, stwórz mu profil w bazie
                    if c_id not in progress_data:
                        progress_data[c_id] = {'repetitions': 0, 'ease_factor': 2.5, 'interval': 0, 'next_review': today_str}
                    
                    # Pobierz stare dane
                    rep = progress_data[c_id]['repetitions']
                    ef = progress_data[c_id]['ease_factor']
                    intrv = progress_data[c_id]['interval']
                    
                    # Przelicz nowe dane za pomocą algorytmu
                    new_rep, new_ef, new_intrv = calculate_sm2(quality, rep, ef, intrv)
                    next_date = datetime.now() + timedelta(days=new_intrv)
                    
                    # Zapisz w słowniku
                    progress_data[c_id] = {
                        'repetitions': new_rep,
                        'ease_factor': new_ef,
                        'interval': new_intrv,
                        'next_review': next_date.strftime("%Y-%m-%d")
                    }
                    
                    # Zapisz do pliku JSON
                    save_progress(progress_data)
                    
                    # Przejdź do następnej karty i ukryj odpowiedź
                    st.session_state.show_answer = False
                    st.rerun()

                # Przyciski oceny trudności
                with col1:
                    if st.button("Nie wiem (0)", use_container_width=True): process_answer(0)
                with col2:
                    if st.button("Trudne (3)", use_container_width=True): process_answer(3)
                with col3:
                    if st.button("Dobre (4)", use_container_width=True): process_answer(4)
                with col4:
                    if st.button("Łatwe (5)", use_container_width=True): process_answer(5)

    # --- ZAKŁADKA 3: ĆWICZENIA ---
    with tab3:
        st.subheader("Sprawdź wiedzę (Wypełnij luki)")
        st.write("Wpisz brakujące słowo i naciśnij Enter, aby sprawdzić.")
        st.markdown("<br>", unsafe_allow_html=True)
        
        for i, ex in enumerate(lesson_data['sections']['exercises']):
            # Pokazujemy polskie tłumaczenie jako podpowiedź nad polem
            st.caption(f"💡 {ex['translation']}")
            
            # Dzielimy układ na kolumnę z polem i kolumnę na wynik
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Zamieniamy symbol "___" z JSONa na pole tekstowe
                user_answer = st.text_input(ex['question'].replace("___", "[ ... ]"), key=f"ex_{ex['id']}")
            
            with col2:
                # Sprawdzanie odpowiedzi w czasie rzeczywistym
                if user_answer:
                    if user_answer.strip().lower() == ex['answer'].lower():
                        st.success("✅ ¡Perfecto!")
                    else:
                        st.error(f"❌ Poprawnie: {ex['answer']}")
            
            st.markdown("---")

if __name__ == "__main__":
    main()
