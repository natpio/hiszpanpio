import streamlit as st
import streamlit.components.v1 as components
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

def set_random_background_and_styles():
    """Wczytuje zew. plik CSS oraz dynamicznie generuje reguły dla zakodowanych teł"""
    bg_image = random.choice(BG_IMAGES)
    main_bg_path = os.path.join("assets", bg_image)
    panel_bg_path = os.path.join("assets", "washi_bg.jpg")
    css_path = os.path.join("assets", "style.css")
    
    try:
        # 1. Wczytanie statycznego CSS z pliku
        with open(css_path, "r", encoding="utf-8") as f:
            static_css = f.read()
            
        # 2. Generowanie dynamicznego CSS z grafikami Base64
        main_bin_str = get_base64_of_bin_file(main_bg_path)
        
        try:
            panel_bin_str = get_base64_of_bin_file(panel_bg_path)
            panel_bg_css = f'background-image: url("data:image/jpeg;base64,{panel_bin_str}") !important; background-size: cover !important;'
        except FileNotFoundError:
            panel_bg_css = 'background-color: #F9F1E6 !important;'

        dynamic_css = f"""
        .stApp::before {{
            content: "";
            position: fixed;
            top: 0; left: 0; width: 100vw; height: 100vh;
            background-image: url("data:image/png;base64,{main_bin_str}");
            background-size: cover;
            background-position: center;
            filter: blur(3px) brightness(0.4);
            z-index: -1;
            transition: background-image 0.5s ease-in-out;
        }}
        [data-testid="stAppViewBlockContainer"] {{
            {panel_bg_css}
        }}
        """
        
        # 3. Wstrzyknięcie pełnego pakietu stylów do aplikacji
        st.markdown(f"<style>\n{static_css}\n{dynamic_css}\n</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Błąd ładowania stylów: {e}")

def trigger_js_confetti():
    """Uruchamia natywny efekt JavaScript (Konfetti) za pomocą biblioteki canvas-confetti"""
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            var duration = 3 * 1000;
            var end = Date.now() + duration;

            (function frame() {
                confetti({
                    particleCount: 7,
                    angle: 60,
                    spread: 55,
                    origin: { x: 0 },
                    colors: ['#26ccff', '#a25afd', '#ff5e7e', '#88ff5a', '#fcff42', '#ffa62d', '#ff36ff']
                });
                confetti({
                    particleCount: 7,
                    angle: 120,
                    spread: 55,
                    origin: { x: 1 },
                    colors: ['#26ccff', '#a25afd', '#ff5e7e', '#88ff5a', '#fcff42', '#ffa62d', '#ff36ff']
                });

                if (Date.now() < end) {
                    requestAnimationFrame(frame);
                }
            }());
        </script>
        """,
        height=0,
    )

def load_data():
    with open(os.path.join("data", "A1", "lekcja_01.json"), "r", encoding="utf-8") as f:
        lesson_data = json.load(f)
    with open(os.path.join("data", "user_progress.json"), "r", encoding="utf-8") as f:
        progress_data = json.load(f)
    return lesson_data, progress_data

def save_progress(progress_data):
    with open(os.path.join("data", "user_progress.json"), "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=4)

def calculate_sm2(quality, repetitions, ease_factor, interval):
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
    set_random_background_and_styles()
    lesson_data, progress_data = load_data()
    
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
        
        due_cards = []
        for card in lesson_data['sections']['flashcards']:
            c_id = card['id']
            if c_id not in progress_data:
                due_cards.append(card)
            elif progress_data[c_id]['next_review'] <= today_str:
                due_cards.append(card)
        
        if not due_cards:
            # Wystrzelenie konfetti z JavaScriptu po ukończeniu materiału!
            trigger_js_confetti()
            st.success("🎉 Świetna robota! Przerobiłeś wszystkie słówka na dzisiaj. Wróć jutro!")
            if st.button("Zresetuj dzisiejszą sesję (Tylko do testów)"):
                st.session_state.clear()
                st.rerun()
        else:
            if st.session_state.current_card >= len(due_cards):
                st.session_state.current_card = 0
                
            active_card = due_cards[st.session_state.current_card]
            
            st.markdown(f"<div class='flashcard-front'>{active_card['pl']}</div>", unsafe_allow_html=True)
            
            if not st.session_state.show_answer:
                if st.button("Pokaż odpowiedź", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                st.markdown(f"<div class='flashcard-back'>{active_card['es']}</div>", unsafe_allow_html=True)
                
                st.write("Jak dobrze pamiętałeś to słówko?")
                col1, col2, col3, col4 = st.columns(4)
                
                def process_answer(quality):
                    c_id = active_card['id']
                    if c_id not in progress_data:
                        progress_data[c_id] = {'repetitions': 0, 'ease_factor': 2.5, 'interval': 0, 'next_review': today_str}
                    
                    rep = progress_data[c_id]['repetitions']
                    ef = progress_data[c_id]['ease_factor']
                    intrv = progress_data[c_id]['interval']
                    
                    new_rep, new_ef, new_intrv = calculate_sm2(quality, rep, ef, intrv)
                    next_date = datetime.now() + timedelta(days=new_intrv)
                    
                    progress_data[c_id] = {
                        'repetitions': new_rep,
                        'ease_factor': new_ef,
                        'interval': new_intrv,
                        'next_review': next_date.strftime("%Y-%m-%d")
                    }
                    
                    save_progress(progress_data)
                    st.session_state.show_answer = False
                    st.rerun()

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
            st.caption(f"💡 {ex['translation']}")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                user_answer = st.text_input(ex['question'].replace("___", "[ ... ]"), key=f"ex_{ex['id']}")
            
            with col2:
                if user_answer:
                    if user_answer.strip().lower() == ex['answer'].lower():
                        st.success("✅ ¡Perfecto!")
                    else:
                        st.error(f"❌ Poprawnie: {ex['answer']}")
            
            st.markdown("---")

if __name__ == "__main__":
    main()
