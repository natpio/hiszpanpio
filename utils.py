import json
import os
import random
import base64
import streamlit as st
import streamlit.components.v1 as components

# --- 1. OBSŁUGA DANYCH ---
def load_lesson(level, filename):
    with open(os.path.join("data", level, filename), "r", encoding="utf-8") as f:
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

# --- 2. ALGORYTM SUPERMEMO (SM-2) ---
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

# --- 3. UI, STYLE I EFEKTY ---
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

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_random_background_and_styles():
    BG_IMAGES = [
        "1000049108.png", "1000049109.png", "1000049110.png", 
        "1000049111.png", "1000049112.png", "1000049113.png"
    ]
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
        content: ""; position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        {main_bg_css} background-size: cover; background-position: center;
        filter: blur(4px) brightness(0.8); z-index: -1;
    }}
    div.block-container {{
        {panel_bg_css} border: 1px solid #D2B48C !important; border-radius: 8px !important;
        box-shadow: 0px 20px 50px rgba(0,0,0,0.6) !important; padding: 3rem !important;
        margin-top: 2rem !important; margin-bottom: 2rem !important;
        animation: fadeInDocument 0.8s ease-out; 
    }}
    @keyframes fadeInDocument {{ from {{ opacity: 0; transform: translateY(15px); }} to {{ opacity: 1; transform: translateY(0); }} }}
    .stMarkdown, .stText, p, div, span, label, li {{ color: #2c1e16 !important; font-size: clamp(1rem, 2.5vw, 1.15rem) !important; }}
    h1 {{ color: #5c2c16 !important; font-size: clamp(1.8rem, 4vw, 2.5rem) !important; border-bottom: 2px solid rgba(210, 180, 140, 0.6); padding-bottom: 10px; }}
    h2 {{ color: #4a2511 !important; font-size: clamp(1.5rem, 3vw, 2rem) !important; }}
    h3 {{ color: #3a1c0d !important; font-size: clamp(1.2rem, 2.5vw, 1.6rem) !important; }}
    .flashcard-front, .flashcard-back {{ border-radius: 8px; transition: transform 0.3s ease, box-shadow 0.3s ease; }}
    .flashcard-front:hover, .flashcard-back:hover {{ transform: scale(1.02); box-shadow: 0px 10px 20px rgba(0,0,0,0.25); cursor: pointer; }}
    .flashcard-front {{ text-align: center; font-size: clamp(24px, 5vw, 32px) !important; font-weight: 600; color: #2C3E50 !important; background: rgba(255, 255, 255, 0.5) !important; padding: 20px; border: 1px dashed #b89d7d !important; margin-bottom: 20px; }}
    .flashcard-back {{ text-align: center; font-size: clamp(32px, 7vw, 44px) !important; font-weight: 800; color: #b33929 !important; background: rgba(255, 255, 255, 0.7) !important; padding: 30px; border: 1px solid #b89d7d !important; margin-bottom: 30px; animation: flipCard 0.4s ease-out; }}
    @keyframes flipCard {{ from {{ transform: rotateX(90deg); opacity: 0; }} to {{ transform: rotateX(0deg); opacity: 1; }} }}
    [data-testid="stSidebar"] {{ background-color: rgba(249, 241, 230, 0.95) !important; border-right: 1px solid #D2B48C; }}
    #MainMenu {{visibility: hidden;}} footer {{visibility: hidden;}} header {{background: transparent !important;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
