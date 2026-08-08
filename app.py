import streamlit as st
import streamlit.components.v1 as components
import json
import os
import random
import base64

# 1. Konfiguracja strony
st.set_page_config(page_title="Kurs Hiszpańskiego A1", page_icon="🇪🇸", layout="wide")

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

def load_lesson(filename):
    with open(os.path.join("data", "A1", filename), "r", encoding="utf-8") as f:
        return json.load(f)

def get_progress_data():
    if 'user_progress' not in st.session_state:
        if os.path.exists(os.path.join("data", "user_progress.json")):
            with open(os.path.join("data", "user_progress.json"), "r", encoding="utf-8") as f:
                st.session_state.user_progress = json.load(f)
        else:
            st.session_state.user_progress = {}
    return st.session_state.user_progress

def save_progress_data(data):
    with open(os.path.join("data", "user_progress.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    st.session_state.user_progress = data

def main():
    set_random_background_and_styles()
    
    st.sidebar.title("📚 Kurs A1 - Ultra Pro")
    
    # Wybór trybu: Lekcje lub Dashboard Analityczny
    mode = st.sidebar.radio("Widok:", ["🎓 Moduły Kursu", "📊 Dashboard Analityczny"])
    st.sidebar.markdown("---")
    
    lesson_dir = os.path.join("data", "A1")
    lesson_files = [f for f in os.listdir(lesson_dir) if f.endswith('.json')]
    lesson_files.sort()
    progress = get_progress_data()

    if mode == "🎓 Moduły Kursu":
        if not lesson_files:
            st.warning("Brak plików lekcji w folderze data/A1.")
            return

        selected_file = st.sidebar.selectbox("Wybierz lekcję", lesson_files)
        lesson = load_lesson(selected_file)
        
        st.sidebar.markdown("### Struktura lekcji")
        
        completed_sections = [s['id'] for s in lesson['sections'] if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)]
        
        section_options = []
        for s in lesson['sections']:
            is_done = progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)
            section_options.append((s['title'], "✅" if is_done else "⭕"))
        
        selected_name = st.sidebar.radio("Sekcje:", [opt[0] for opt in section_options])
        current_section = next(s for s in lesson['sections'] if s['title'] == selected_name)
        
        st.sidebar.markdown(f"**Postęp lekcji:** {len(completed_sections)}/{len(lesson['sections'])} ukończonych")

        # Renderowanie treści głównej
        st.title(lesson['lesson_metadata']['title'])
        st.header(current_section['title'])
        
        if current_section['type'] == 'dialog':
            for line in current_section['content']:
                st.write(f"**{line['speaker']}**: {line['text']}")
                
        elif current_section['type'] == 'vocabulary':
            for item in current_section['items']:
                st.write(f"✅ **{item['es']}** - {item['pl']}")
                
        elif current_section['type'] == 'grammar':
            st.info(current_section['content'])
                
        elif current_section['type'] == 'exercises':
            st.write("Wypełnij luki i naciśnij Enter, aby sprawdzić odpowiedź.")
            st.markdown("<br>", unsafe_allow_html=True)
            for i, ex in enumerate(current_section['items']):
                with st.expander(f"💡 {ex['translation']}"):
                    ans = st.text_input(ex['question'].replace("___", "[ ... ]"), key=f"ex_{selected_file}_{current_section['id']}_{i}")
                    if ans:
                        if ans.strip().lower() == ex['answer'].lower():
                            st.success("✅ ¡Perfecto!")
                        else:
                            st.error(f"❌ Poprawnie: {ex['answer']}")

        # Przycisk zaliczenia sekcji
        st.markdown("---")
        prog_key = f"{lesson['lesson_metadata']['id']}_{current_section['id']}"
        if not progress.get(prog_key, False):
            if st.button("Zakończ tę sekcję", use_container_width=True):
                progress[prog_key] = True
                save_progress_data(progress)
                trigger_js_confetti() # Konfetti po zaliczeniu!
                st.rerun()
        else:
            st.success("🎉 Sekcja ukończona!")
            if st.button("Zresetuj postęp tej sekcji"):
                progress[prog_key] = False
                save_progress_data(progress)
                st.rerun()

    elif mode == "📊 Dashboard Analityczny":
        st.title("📊 Dashboard Analityczny Kursu")
        st.write("Statystyki Twoich postępów w nauce języka hiszpańskiego.")
        
        total_sections = 0
        completed_sections_count = 0
        
        lesson_progress_summary = []
        
        for f in lesson_files:
            l_data = load_lesson(f)
            l_id = l_data['lesson_metadata']['id']
            l_title = l_data['lesson_metadata']['title']
            
            l_total = len(l_data['sections'])
            l_done = sum(1 for s in l_data['sections'] if progress.get(f"{l_id}_{s['id']}", False))
            
            total_sections += l_total
            completed_sections_count += l_done
            
            pct = int((l_done / l_total) * 100) if l_total > 0 else 0
            lesson_progress_summary.append({"Lekcja": l_title, "Ukończono (%)": pct, "Zaliczone": f"{l_done}/{l_total}"})

        # Metryki główne
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Ukończone sekcje", f"{completed_sections_count} / {total_sections}")
        with col2:
            global_pct = int((completed_sections_count / total_sections) * 100) if total_sections > 0 else 0
            st.metric("Ogólny postęp kursu", f"{global_pct}%")
        with col3:
            st.metric("Aktywne moduły", len(lesson_files))

        st.markdown("---")
        st.subheader("📈 Postęp w poszczególnych lekcjach")
        
        for item in lesson_progress_summary:
            st.write(f"**{item['Lekcja']}** — {item['Zaliczone']} sekcji")
            st.progress(item['Ukończono (%)'])

if __name__ == "__main__":
    main()
