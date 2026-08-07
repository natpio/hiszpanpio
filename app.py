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
    bg_image = random.choice(BG_IMAGES)
    main_bg_path = os.path.join("assets", bg_image)
    panel_bg_path = os.path.join("assets", "washi_bg.jpg")
    
    main_bg_css = ""
    panel_bg_css = "background-color: #F9F1E6 !important;"
    
    try:
        main_bin_str = get_base64_of_bin_file(main_bg_path)
        main_bg_css = f'background-image: url("data:image/png;base64,{main_bin_str}");'
    except Exception:
        pass
        
    try:
        panel_bin_str = get_base64_of_bin_file(panel_bg_path)
        panel_bg_css = f'background: #F9F1E6 url("data:image/jpeg;base64,{panel_bin_str}") center/cover no-repeat !important;'
    except Exception:
        pass

    css = f"""
    <style>
    .stApp {{ background-color: transparent !important; }}

    .stApp::before {{
        content: "";
        position: fixed;
        top: 0; left: 0; width: 100vw; height: 100vh;
        {main_bg_css}
        background-size: cover;
        background-position: center;
        filter: blur(4px) brightness(0.8); 
        z-index: -1;
        transition: background-image 0.5s ease-in-out;
    }}

    div.block-container {{
        {panel_bg_css}
        border: 1px solid #D2B48C !important;
        border-radius: 8px !important;
        box-shadow: 0px 20px 50px rgba(0,0,0,0.6) !important;
        padding: 3rem !important;
        margin-top: 2rem !important;
        margin-bottom: 2rem !important;
        animation: fadeInDocument 0.8s ease-out; 
    }}

    @keyframes fadeInDocument {{
        from {{ opacity: 0; transform: translateY(15px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}

    .stMarkdown, .stText, p, div, span, label, li {{
        color: #2c1e16 !important; 
        font-size: clamp(1rem, 2.5vw, 1.15rem) !important;
    }}
    
    h1 {{ 
        color: #5c2c16 !important; 
        font-size: clamp(1.8rem, 4vw, 2.5rem) !important; 
        border-bottom: 2px solid rgba(210, 180, 140, 0.6); 
        padding-bottom: 10px;
    }}
    h2 {{ color: #4a2511 !important; font-size: clamp(1.5rem, 3vw, 2rem) !important; }}
    h3 {{ color: #3a1c0d !important; font-size: clamp(1.2rem, 2.5vw, 1.6rem) !important; }}

    .flashcard-front, .flashcard-back {{
        border-radius: 8px;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }}
    .flashcard-front:hover, .flashcard-back:hover {{
        transform: scale(1.02); 
        box-shadow: 0px 10px 20px rgba(0,0,0,0.25);
        cursor: pointer;
    }}
    .flashcard-front {{ 
        text-align: center; 
        font-size: clamp(24px, 5vw, 32px) !important; 
        font-weight: 600; 
        color: #2C3E50 !important; 
        background: rgba(255, 255, 255, 0.5) !important;
        padding: 20px;
        border: 1px dashed #b89d7d !important;
        margin-bottom: 20px; 
    }}
    .flashcard-back {{ 
        text-align: center; 
        font-size: clamp(32px, 7vw, 44px) !important; 
        font-weight: 800; 
        color: #b33929 !important; 
        background: rgba(255, 255, 255, 0.7) !important;
        padding: 30px;
        border: 1px solid #b89d7d !important;
        margin-bottom: 30px; 
        animation: flipCard 0.4s ease-out; 
    }}

    @keyframes flipCard {{
        from {{ transform: rotateX(90deg); opacity: 0; }}
        to {{ transform: rotateX(0deg); opacity: 1; }}
    }}

    [data-testid="stSidebar"] {{
        background-color: rgba(249, 241, 230, 0.95) !important;
        border-right: 1px solid #D2B48C;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{background: transparent !important;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def trigger_js_confetti():
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
            var duration = 3 * 1000;
            var end = Date.now() + duration;
            (function frame() {
                confetti({ particleCount: 7, angle: 60, spread: 55, origin: { x: 0 }, colors: ['#26ccff', '#a25afd', '#ff5e7e', '#88ff5a', '#fcff42', '#ffa62d', '#ff36ff'] });
                confetti({ particleCount: 7, angle: 120, spread: 55, origin: { x: 1 }, colors: ['#26ccff', '#a25afd', '#ff5e7e', '#88ff5a', '#fcff42', '#ffa62d', '#ff36ff'] });
                if (Date.now() < end) requestAnimationFrame(frame);
            }());
        </script>
        """,
        height=0,
    )

def load_data(lesson_filename):
    with open(os.path.join("data", "A1", lesson_filename), "r", encoding="utf-8") as f:
        lesson_data = json.load(f)
    with open(os.path.join("data", "user_progress.json"), "r", encoding="utf-8") as f:
        progress_data = json.load(f)
    return lesson_data, progress_data

def load_all_vocabulary(lesson_dir):
    """Pobiera wszystkie słówka ze wszystkich lekcji do Słownika Globalnego"""
    all_words = []
    lesson_names = []
    try:
        for f in os.listdir(lesson_dir):
            if f.endswith('.json'):
                with open(os.path.join(lesson_dir, f), "r", encoding="utf-8") as file:
                    data = json.load(file)
                    title = data['lesson_metadata']['title']
                    lesson_names.append(title)
                    for card in data['sections']['flashcards']:
                        all_words.append({
                            "es": card["es"],
                            "pl": card["pl"],
                            "lesson": title
                        })
    except FileNotFoundError:
        pass
    
    lesson_names.sort()
    return all_words, lesson_names

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
    
    # -------------------------------------
    # NAWIGACJA W PASKU BOCZNYM (SIDEBAR)
    # -------------------------------------
    st.sidebar.title("🇪🇸 Menu Kursu")
    
    # Wybór trybu działania aplikacji
    app_mode = st.sidebar.radio("Wybierz tryb:", ["🎓 Tryb Nauki (Lekcje)", "📚 Słownik Globalny"])
    st.sidebar.markdown("---")
    
    lesson_dir = os.path.join("data", "A1")
    
    if app_mode == "🎓 Tryb Nauki (Lekcje)":
        try:
            available_lessons = [f for f in os.listdir(lesson_dir) if f.endswith('.json')]
            available_lessons.sort() 
        except FileNotFoundError:
            available_lessons = []
            st.sidebar.error("Nie znaleziono folderu z lekcjami.")

        if available_lessons:
            selected_file = st.sidebar.selectbox(
                "Wybierz moduł:", 
                available_lessons, 
                format_func=lambda x: x.replace(".json", "").replace("_", " ").title()
            )
            
            lesson_data, progress_data = load_data(selected_file)
            
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
                    trigger_js_confetti()
                    st.success("🎉 Świetna robota! Przerobiłeś wszystkie słówka w tej lekcji na dzisiaj. Wróć jutro!")
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

    # -------------------------------------
    # TRYB SŁOWNIKA GLOBALNEGO
    # -------------------------------------
    elif app_mode == "📚 Słownik Globalny":
        st.title("📚 Słownik Globalny")
        st.write("Przeglądaj, filtruj i wyszukuj słownictwo z całego kursu.")
        
        all_words, lesson_names = load_all_vocabulary(lesson_dir)
        
        if not all_words:
            st.warning("Nie znaleziono słówek. Upewnij się, że lekcje są dodane.")
        else:
            # Panele filtrowania
            col_search, col_filter = st.columns([1, 1])
            with col_search:
                search_query = st.text_input("🔍 Szukaj słówka (PL / ES):")
            with col_filter:
                selected_lessons = st.multiselect("Filtruj po lekcjach:", lesson_names, default=lesson_names)
            
            # Logika filtrowania
            filtered_words = [w for w in all_words if w['lesson'] in selected_lessons]
            if search_query:
                query = search_query.strip().lower()
                filtered_words = [w for w in filtered_words if query in w['es'].lower() or query in w['pl'].lower()]
            
            # Generowanie estetycznej tabeli HTML dopasowanej do pergaminu
            if filtered_words:
                table_html = "<table style='width:100%; border-collapse: collapse; margin-top: 15px;'>"
                table_html += """
                <tr style='border-bottom: 2px solid #D2B48C;'>
                    <th style='text-align:left; padding:12px; color:#5c2c16;'>Hiszpański</th>
                    <th style='text-align:left; padding:12px; color:#5c2c16;'>Polski</th>
                    <th style='text-align:right; padding:12px; color:#5c2c16;'>Moduł</th>
                </tr>
                """
                for w in filtered_words:
                    table_html += f"<tr style='border-bottom: 1px dashed rgba(210, 180, 140, 0.5);'>"
                    table_html += f"<td style='padding:12px; font-weight:bold; color:#b33929; font-size: 1.1rem;'>{w['es']}</td>"
                    table_html += f"<td style='padding:12px; color:#2C3E50;'>{w['pl']}</td>"
                    table_html += f"<td style='padding:12px; text-align:right; font-size:0.85em; opacity:0.8;'>{w['lesson']}</td>"
                    table_html += "</tr>"
                table_html += "</table>"
                
                st.markdown(table_html, unsafe_allow_html=True)
                st.caption(f"Wyświetlono słówek: {len(filtered_words)}")
            else:
                st.info("Brak słówek spełniających kryteria wyszukiwania.")

if __name__ == "__main__":
    main()
