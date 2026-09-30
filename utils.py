import re
import base64
import json
import os
import random
from datetime import date, datetime, timedelta
import unicodedata

import streamlit as st
import streamlit.components.v1 as components

DATA_DIR = "data"
PROGRESS_FILE = os.path.join(DATA_DIR, "user_progress.json")


def load_lesson(level, filename):
    with open(os.path.join(DATA_DIR, level, filename), "r", encoding="utf-8") as f:
        return json.load(f)


def list_levels():
    if not os.path.isdir(DATA_DIR):
        return []
    return sorted(
        [d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))]
    )


def list_lessons(level):
    path = os.path.join(DATA_DIR, level)
    if not os.path.isdir(path):
        return []
    return sorted(
        [f for f in os.listdir(path) if f.endswith(".json")],
        key=lambda x: int(re.search(r"(\d+)", x).group(1)) if re.search(r"(\d+)", x) else 999
    )


def all_lessons():
    lessons = []
    for level in list_levels():
        for filename in list_lessons(level):
            try:
                lessons.append(load_lesson(level, filename))
            except (OSError, json.JSONDecodeError):
                continue
    return lessons


def get_progress_data():
    if "user_progress" not in st.session_state:
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}
        st.session_state.user_progress = data
    return st.session_state.user_progress


def save_progress_data(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, PROGRESS_FILE)
    st.session_state.user_progress = data


def touch_activity(progress):
    today = date.today().isoformat()
    days = set(progress.get("_activity_days", []))
    days.add(today)
    progress["_activity_days"] = sorted(days)[-180:]
    progress["_last_activity"] = today


def record_event(progress, event="study"):
    touch_activity(progress)
    events = progress.get("_events", [])
    events.append({"date": date.today().isoformat(), "event": event})
    progress["_events"] = events[-500:]


def activity_streak(progress):
    days = set(progress.get("_activity_days", []))
    if not days:
        return 0
    cursor = date.today()
    if cursor.isoformat() not in days:
        cursor -= timedelta(days=1)
    streak = 0
    while cursor.isoformat() in days:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def normalize_answer(value):
    value = str(value).strip().lower()
    value = unicodedata.normalize("NFD", value)
    return "".join(ch for ch in value if unicodedata.category(ch) != "Mn")


def answers_match(user_answer, expected):
    options = expected if isinstance(expected, list) else [expected]
    user = normalize_answer(user_answer)
    return any(user == normalize_answer(option) for option in options)


def section_key(lesson_id, section_id):
    return f"{lesson_id}__{section_id}"


def exercise_key(lesson_id, section_id, index):
    return f"ex_done__{lesson_id}__{section_id}__{index}"


def vocab_position_key(lesson_id, section_id):
    return f"vocab_idx__{lesson_id}__{section_id}"


def vocab_card_key(lesson_id, section_id, index):
    return f"vocab_card__{lesson_id}__{section_id}__{index}"


def exercise_card_key(lesson_id, section_id, index):
    return f"exercise_card__{lesson_id}__{section_id}__{index}"


def calculate_sm2(quality, repetitions, ease_factor, interval):
    if quality >= 3:
        if repetitions == 0:
            interval = 1
        elif repetitions == 1:
            interval = 6
        else:
            interval = max(1, round(interval * ease_factor))
        ease_factor += 0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)
        repetitions += 1
    else:
        repetitions = 0
        interval = 1
    ease_factor = max(1.3, ease_factor)
    return repetitions, ease_factor, interval


def update_sm2(progress, key, quality):
    today = date.today()
    card = progress.get(
        key,
        {"repetitions": 0, "ease_factor": 2.5, "interval": 0, "next_review": today.isoformat()},
    )
    rep, ef, interval = calculate_sm2(
        quality, card["repetitions"], card["ease_factor"], card["interval"]
    )
    card.update(
        {
            "repetitions": rep,
            "ease_factor": round(ef, 3),
            "interval": interval,
            "next_review": (today + timedelta(days=interval)).isoformat(),
            "last_review": today.isoformat(),
        }
    )
    progress[key] = card
    record_event(progress, "review")
    save_progress_data(progress)


def is_due(card):
    return not card or card.get("next_review", "") <= date.today().isoformat()


def trigger_confetti():
    components.html(
        """
        <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
        <script>
        const end = Date.now() + 1200;
        (function frame() {
          confetti({particleCount: 5, spread: 60, origin: {y: .7}});
          if (Date.now() < end) requestAnimationFrame(frame);
        })();
        </script>
        """,
        height=0,
    )


def get_base64(path):
    try:
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    except OSError:
        return None


def inject_styles():
    backgrounds = [
        "1000049109.png", "1000049110.png", "1000049111.png",
        "1000049112.png", "1000049113.png"
    ]
    bg = random.choice(backgrounds)
    bg64 = get_base64(os.path.join("assets", bg))
    paper64 = get_base64(os.path.join("assets", "washi_bg.jpg"))
    bg_rule = f'background-image:url("data:image/png;base64,{bg64}");' if bg64 else ""
    paper_rule = (
        f'background-image:url("data:image/jpeg;base64,{paper64}");'
        if paper64 else ""
    )
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,600;9..144,700&display=swap');
        :root {{
          --ink:#1d2521; --muted:#69736d; --paper:#fffdf8; --cream:#f5efe4;
          --green:#1f6b57; --green2:#2e8b70; --gold:#c38b2d; --line:#e5ddcf;
          --red:#b65045; --shadow:0 18px 50px rgba(36,31,24,.10);
        }}
        html, body, [class*="css"] {{ font-family:'DM Sans', sans-serif; }}
        .stApp {{ background:#e8dfd1; }}
        .stApp::before {{
          content:""; position:fixed; inset:0; z-index:-2; opacity:.34;
          {bg_rule} background-size:cover; background-position:center; filter:blur(2px);
        }}
        .stApp::after {{
          content:""; position:fixed; inset:0; z-index:-1;
          background:linear-gradient(135deg,rgba(255,250,242,.90),rgba(238,231,219,.82));
        }}
        .block-container {{ max-width:1180px; padding:2.5rem 2rem 4rem; }}
        h1,h2,h3 {{ font-family:'Fraunces',serif !important; color:var(--ink) !important; letter-spacing:-.02em; }}
        h1 {{ font-size:clamp(2.2rem,5vw,4rem) !important; line-height:1.02 !important; }}
        h2 {{ font-size:2rem !important; }}
        p, li, label, .stMarkdown {{ color:var(--ink); }}
        [data-testid="stSidebar"] {{
          background:rgba(250,247,240,.96); border-right:1px solid var(--line);
        }}
        [data-testid="stSidebar"] > div:first-child {{ padding-top:1.5rem; }}
        [data-testid="stSidebar"] .stRadio label {{
          padding:.25rem .2rem; border-radius:10px;
        }}
        .brand {{ font-family:'Fraunces',serif; font-size:1.55rem; font-weight:700; margin-bottom:.15rem; }}
        .brand-sub {{ color:var(--muted); font-size:.85rem; margin-bottom:1.2rem; }}
        .hero {{
          background:linear-gradient(135deg,#174f42 0%,#2c8067 100%);
          color:white; border-radius:26px; padding:2.4rem; box-shadow:var(--shadow); margin-bottom:1.6rem;
        }}
        .hero h1,.hero p,.hero span {{ color:white !important; }}
        .eyebrow {{ text-transform:uppercase; letter-spacing:.13em; font-weight:700; font-size:.74rem; opacity:.78; }}
        .hero-copy {{ max-width:680px; font-size:1.08rem; line-height:1.65; opacity:.9; }}
        .stat-card,.lesson-card,.feature-card,.info-card {{
          background:rgba(255,253,248,.93); border:1px solid var(--line); border-radius:20px;
          padding:1.2rem; box-shadow:0 8px 25px rgba(40,33,24,.055); height:100%;
        }}
        .stat-value {{ font-family:'Fraunces',serif; font-size:2rem; font-weight:700; color:var(--green); }}
        .stat-label {{ color:var(--muted); font-size:.86rem; margin-top:.15rem; }}
        .card-kicker {{ color:var(--green); text-transform:uppercase; font-size:.72rem; letter-spacing:.1em; font-weight:700; }}
        .card-title {{ font-family:'Fraunces',serif; font-size:1.35rem; font-weight:700; margin:.35rem 0; }}
        .muted {{ color:var(--muted); }}
        .lesson-card {{ min-height:190px; }}
        .pill {{ display:inline-block; padding:.25rem .6rem; border-radius:999px; background:#e9f2ee; color:var(--green); font-weight:700; font-size:.72rem; }}
        .flashcard {{
          background:var(--paper); border:1px solid var(--line); border-radius:26px; min-height:280px;
          display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center;
          padding:2rem; box-shadow:var(--shadow); margin:1rem 0;
        }}
        .flash-front {{ font-family:'Fraunces',serif; font-size:clamp(2rem,5vw,3.4rem); font-weight:700; }}
        .flash-hint {{ color:var(--muted); margin-top:.7rem; }}
        .flash-back {{ color:var(--green); font-family:'Fraunces',serif; font-size:clamp(2.1rem,5vw,3.7rem); font-weight:700; }}
        .section-chip {{ background:#f0eadf; border:1px solid var(--line); border-radius:12px; padding:.7rem .8rem; margin-bottom:.45rem; }}
        .success-box {{ border-radius:18px; background:#e8f4ef; border:1px solid #cbe2d8; padding:1rem 1.1rem; }}
        .danger-box {{ border-radius:18px; background:#fff0ed; border:1px solid #f0d0ca; padding:1rem 1.1rem; }}
        .quote {{ border-left:4px solid var(--gold); padding:.2rem 0 .2rem 1rem; color:#51483d; }}
        .stButton > button {{ border-radius:12px; min-height:2.7rem; font-weight:700; border:1px solid var(--line); }}
        .stButton > button[kind="primary"] {{ background:var(--green); border-color:var(--green); }}
        div[data-testid="stProgressBar"] > div > div {{ background:var(--green); }}
        [data-testid="stMetric"] {{ background:rgba(255,253,248,.85); border:1px solid var(--line); padding:1rem; border-radius:18px; }}
        @media(max-width:800px) {{
          .block-container {{ padding:1.2rem .9rem 3rem; }}
          .hero {{ padding:1.5rem; border-radius:20px; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
