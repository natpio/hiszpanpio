import json
import os
import random
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd

from utils import (
    activity_streak,
    all_lessons,
    answers_match,
    calculate_sm2,
    exercise_card_key,
    exercise_key,
    get_progress_data,
    inject_styles,
    is_due,
    list_lessons,
    list_levels,
    load_lesson,
    record_event,
    section_key,
    save_progress_data,
    touch_activity,
    trigger_confetti,
    update_sm2,
    vocab_card_key,
    vocab_position_key,
)

st.set_page_config(
    page_title="Hiszpański • nauka po ludzku",
    page_icon="🇪🇸",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_styles()


@st.cache_data(show_spinner=False)
def get_catalog():
    return all_lessons()


def lesson_stats(lesson, progress):
    lid = lesson["lesson_metadata"]["id"]
    sections = lesson.get("sections", [])
    done = sum(bool(progress.get(section_key(lid, s["id"]), False)) for s in sections)
    total_items = sum(
        len(s.get("items", [])) for s in sections if s["type"] in ("vocabulary", "exercises")
    )
    return done, len(sections), total_items


def overall_stats(lessons, progress):
    total_sections = done_sections = 0
    vocabulary = exercises = 0
    for lesson in lessons:
        done, total, _ = lesson_stats(lesson, progress)
        done_sections += done
        total_sections += total
        for s in lesson["sections"]:
            if s["type"] == "vocabulary":
                vocabulary += len(s.get("items", []))
            elif s["type"] == "exercises":
                exercises += len(s.get("items", []))
    learned_words = sum(
        1 for k, v in progress.items()
        if k.startswith("vocab_card__") and isinstance(v, dict) and v.get("repetitions", 0) > 0
    )
    return {
        "done_sections": done_sections,
        "total_sections": total_sections,
        "progress": round(done_sections / total_sections * 100) if total_sections else 0,
        "vocabulary": vocabulary,
        "exercises": exercises,
        "learned_words": learned_words,
    }


def due_cards(lessons, progress):
    cards = []
    for lesson in lessons:
        lid = lesson["lesson_metadata"]["id"]
        for section in lesson["sections"]:
            sid = section["id"]
            if not progress.get(section_key(lid, sid), False):
                continue
            if section["type"] == "vocabulary":
                for i, item in enumerate(section.get("items", [])):
                    key = vocab_card_key(lid, sid, i)
                    if is_due(progress.get(key)):
                        cards.append({
                            "key": key, "kind": "Słówko", "front": item["pl"], "back": item["es"],
                            "lesson": lesson["lesson_metadata"]["title"],
                        })
            elif section["type"] == "exercises":
                for i, ex in enumerate(section.get("items", [])):
                    key = exercise_card_key(lid, sid, i)
                    if is_due(progress.get(key)):
                        cards.append({
                            "key": key, "kind": "Zdanie", "front": ex["question"].replace("___", "_____"),
                            "back": ex["question"].replace("___", ex["answer"]),
                            "hint": ex.get("translation", ""),
                            "lesson": lesson["lesson_metadata"]["title"],
                        })
    return cards


def complete_section(progress, lesson_id, section_id):
    progress[section_key(lesson_id, section_id)] = True
    record_event(progress, "section_complete")
    save_progress_data(progress)
    trigger_confetti()


def page_home(lessons, progress):
    stats = overall_stats(lessons, progress)
    due = due_cards(lessons, progress)
    streak = activity_streak(progress)

    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">HISZPAŃSKI • TWÓJ PLAN NA DZIŚ</div>
          <h1>Hola. Zróbmy dziś trochę hiszpańskiego.</h1>
          <p class="hero-copy">Krótka sesja, konkretna lekcja i powtórki wtedy, kiedy naprawdę są potrzebne. Bez przeklikiwania się przez panel administracyjny.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Postęp kursu", f"{stats['progress']}%")
    c2.metric("Do powtórki", len(due))
    c3.metric("Opanowane słówka", stats["learned_words"])
    c4.metric("Seria dni", f"{streak} 🔥")

    st.markdown("## Kontynuuj naukę")
    incomplete = []
    for lesson in lessons:
        done, total, _ = lesson_stats(lesson, progress)
        if done < total:
            incomplete.append((lesson, done, total))
    if incomplete:
        lesson, done, total = incomplete[0]
        lid = lesson["lesson_metadata"]["id"]
        st.markdown(
            f"""
            <div class="feature-card">
              <div class="card-kicker">{lesson['lesson_metadata']['level']} • następny krok</div>
              <div class="card-title">{lesson['lesson_metadata']['title']}</div>
              <div class="muted">{done}/{total} sekcji ukończonych</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.progress(done / total if total else 0)
        if st.button("▶ Otwórz lekcję", type="primary", use_container_width=True):
            st.session_state.page = "Kurs"
            st.session_state.lesson_id = lid
            st.rerun()
    else:
        st.success("🎉 Ukończyłeś wszystkie dostępne lekcje. Czas na powtórki i utrwalanie.")

    st.markdown("## Dzisiejszy wybór")
    a, b, c = st.columns(3)
    with a:
        st.markdown('<div class="feature-card"><div class="card-kicker">01 • POWTÓRKA</div><div class="card-title">Pamięć na pierwszym miejscu</div><p class="muted">Masz <b>%d</b> kart gotowych do powtórzenia.</p></div>' % len(due), unsafe_allow_html=True)
    with b:
        st.markdown('<div class="feature-card"><div class="card-kicker">02 • KURS</div><div class="card-title">Lekcje krok po kroku</div><p class="muted">Dialog → słownictwo → gramatyka → ćwiczenia.</p></div>', unsafe_allow_html=True)
    with c:
        st.markdown('<div class="feature-card"><div class="card-kicker">03 • TRENING</div><div class="card-title">5 minut na słówka</div><p class="muted">Szybka sesja losowych słów z ukończonych sekcji.</p></div>', unsafe_allow_html=True)


def page_course(lessons, progress):
    st.title("Kurs")
    st.caption("Wybierz poziom i pracuj przez lekcje w logicznej kolejności.")

    levels = list(dict.fromkeys(l["lesson_metadata"]["level"] for l in lessons))
    level = st.segmented_control("Poziom", levels, default=st.session_state.get("level", levels[0]) if levels else None)
    if level:
        st.session_state.level = level
    visible = [l for l in lessons if l["lesson_metadata"]["level"] == level]

    for start in range(0, len(visible), 2):
        cols = st.columns(2)
        for col, lesson in zip(cols, visible[start:start+2]):
            done, total, items = lesson_stats(lesson, progress)
            pct = done / total if total else 0
            status = "Ukończona" if pct == 1 else ("W toku" if done else "Do rozpoczęcia")
            with col:
                st.markdown(
                    f"""
                    <div class="lesson-card">
                      <span class="pill">{lesson['lesson_metadata']['level']} · {status}</span>
                      <div class="card-title">{lesson['lesson_metadata']['title']}</div>
                      <div class="muted">{done}/{total} sekcji · {items} elementów treningowych</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.progress(pct)
                if st.button("Otwórz →", key=f"open_{lesson['lesson_metadata']['id']}", use_container_width=True):
                    st.session_state.lesson_id = lesson["lesson_metadata"]["id"]
                    st.session_state.page = "Lekcja"
                    st.rerun()


def render_dialog(section):
    st.markdown('<div class="info-card">', unsafe_allow_html=True)
    for line in section.get("content", []):
        st.markdown(f"**{line.get('speaker','Rozmówca')}**  \n{line.get('text','')}")
        if line.get("translation"):
            st.caption(line["translation"])
    st.markdown("</div>", unsafe_allow_html=True)


def render_grammar(section):
    st.markdown(section.get("content", ""))


def render_vocabulary(lesson, section, progress):
    lid, sid = lesson["lesson_metadata"]["id"], section["id"]
    items = section.get("items", [])
    pos_key = vocab_position_key(lid, sid)
    pos = int(progress.get(pos_key, 0))
    pos = min(pos, len(items))

    st.progress(pos / len(items) if items else 1, text=f"{pos} / {len(items)} słówek przećwiczonych")
    with st.expander("Zobacz pełną listę słówek"):
        for item in items:
            st.markdown(f"**{item['es']}** — {item['pl']}")

    if pos >= len(items):
        st.markdown('<div class="success-box"><b>Gotowe.</b> Wszystkie słówka z tej sekcji zostały przećwiczone.</div>', unsafe_allow_html=True)
        if st.button("Powtórz sekcję od początku", key=f"reset_{lid}_{sid}"):
            progress[pos_key] = 0
            save_progress_data(progress)
            st.rerun()
        return

    item = items[pos]
    show_key = f"show_vocab_{lid}_{sid}"
    show = st.session_state.get(show_key, False)
    st.markdown(
        f"""
        <div class="flashcard">
          <div class="eyebrow">FISZKA {pos+1} / {len(items)}</div>
          <div class="flash-front">{item['pl']}</div>
          <div class="flash-hint">Spróbuj powiedzieć po hiszpańsku, zanim odsłonisz odpowiedź.</div>
          {'<div class="flash-back">'+item['es']+'</div>' if show else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not show:
        if st.button("Pokaż odpowiedź", type="primary", use_container_width=True):
            st.session_state[show_key] = True
            st.rerun()
    else:
        if st.button("Znam → następne", type="primary", use_container_width=True):
            progress[pos_key] = pos + 1
            record_event(progress, "vocab")
            save_progress_data(progress)
            st.session_state[show_key] = False
            st.rerun()


def render_exercises(lesson, section, progress):
    lid, sid = lesson["lesson_metadata"]["id"], section["id"]
    items = section.get("items", [])
    done = sum(progress.get(exercise_key(lid, sid, i), False) for i in range(len(items)))
    st.progress(done / len(items) if items else 1, text=f"{done} / {len(items)} poprawnych")

    for i, ex in enumerate(items):
        key = exercise_key(lid, sid, i)
        with st.expander(f"{'✅' if progress.get(key) else '○'} {ex.get('translation','Ćwiczenie')}"):
            if progress.get(key):
                st.success(f"Poprawnie: {ex['answer']}")
                continue
            answer = st.text_input(ex["question"], key=f"answer_{lid}_{sid}_{i}", placeholder="Wpisz odpowiedź…")
            if st.button("Sprawdź", key=f"check_{lid}_{sid}_{i}"):
                if answers_match(answer, ex["answer"]):
                    progress[key] = True
                    record_event(progress, "exercise")
                    save_progress_data(progress)
                    st.success("¡Perfecto! Poprawna odpowiedź.")
                    st.rerun()
                else:
                    st.error("Jeszcze nie. Spróbuj ponownie — odpowiedź nie została zaliczona.")


def page_lesson(lessons, progress):
    lesson_id = st.session_state.get("lesson_id")
    lesson = next((l for l in lessons if l["lesson_metadata"]["id"] == lesson_id), None)
    if not lesson:
        st.info("Wybierz lekcję z kursu.")
        return
    lid = lesson["lesson_metadata"]["id"]
    done, total, _ = lesson_stats(lesson, progress)

    top1, top2 = st.columns([4,1])
    with top1:
        st.caption(f"{lesson['lesson_metadata']['level']} · LEKCJA")
        st.title(lesson["lesson_metadata"]["title"])
    with top2:
        st.metric("Postęp", f"{done}/{total}")

    st.progress(done / total if total else 0)
    options = lesson["sections"]
    labels = [
        ("✓ " if progress.get(section_key(lid, s["id"])) else "") + s["title"]
        for s in options
    ]
    idx = st.segmented_control("Sekcja", labels, default=labels[0], key=f"sec_nav_{lid}")
    section = options[labels.index(idx)] if idx in labels else options[0]

    st.markdown(f"## {section['title']}")
    st.caption({"dialog":"Czytaj i osłuchuj się z konstrukcjami.", "vocabulary":"Powiedz odpowiedź zanim ją zobaczysz.", "grammar":"Zrozum zasadę, potem wróć do ćwiczeń.", "exercises":"Wpisz odpowiedź z pamięci."}.get(section["type"], "Pracuj krok po kroku."))

    if section["type"] == "dialog":
        render_dialog(section)
    elif section["type"] == "vocabulary":
        render_vocabulary(lesson, section, progress)
    elif section["type"] == "grammar":
        render_grammar(section)
    elif section["type"] == "exercises":
        render_exercises(lesson, section, progress)

    sid = section["id"]
    can_finish = True
    if section["type"] == "vocabulary":
        can_finish = progress.get(vocab_position_key(lid, sid), 0) >= len(section.get("items", []))
    elif section["type"] == "exercises":
        can_finish = all(progress.get(exercise_key(lid, sid, i), False) for i in range(len(section.get("items", []))))

    st.divider()
    if progress.get(section_key(lid, sid)):
        st.success("Sekcja ukończona. Możesz do niej wracać w dowolnym momencie.")
    elif can_finish:
        if st.button("✓ Oznacz sekcję jako ukończoną", type="primary", use_container_width=True):
            complete_section(progress, lid, sid)
            st.rerun()
    else:
        st.info("Dokończ aktywność w tej sekcji, aby ją zaliczyć.")


def page_review(lessons, progress):
    st.title("Powtórki")
    cards = due_cards(lessons, progress)
    if not cards:
        st.success("🎉 Na dziś wszystko zrobione. Wróć jutro albo rozpocznij trening słówek.")
        return

    if "review_index" not in st.session_state:
        st.session_state.review_index = 0
        st.session_state.review_show = False
    if st.session_state.review_index >= len(cards):
        st.session_state.review_index = 0

    card = cards[st.session_state.review_index]
    st.caption(f"{card['kind']} · {st.session_state.review_index+1} / {len(cards)} · {card['lesson']}")
    st.progress(st.session_state.review_index / len(cards))

    back = card.get("back", "")
    st.markdown(
        f"""
        <div class="flashcard">
          <div class="eyebrow">{card['kind']}</div>
          <div class="flash-front">{card['front']}</div>
          {('<div class="flash-hint">'+card.get('hint','')+'</div>') if card.get('hint') else ''}
          {('<div class="flash-back">'+back+'</div>') if st.session_state.review_show else ''}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.review_show:
        if st.button("Pokaż odpowiedź", type="primary", use_container_width=True):
            st.session_state.review_show = True
            st.rerun()
    else:
        st.write("Jak dobrze to pamiętałeś?")
        cols = st.columns(4)
        for col, label, quality in zip(
            cols, ["Nie wiem", "Trudne", "Dobre", "Łatwe"], [0, 3, 4, 5]
        ):
            if col.button(label, key=f"rate_{quality}", use_container_width=True):
                update_sm2(progress, card["key"], quality)
                st.session_state.review_index += 1
                st.session_state.review_show = False
                st.rerun()


def page_trainer(lessons, progress):
    st.title("Trener słówek")
    unlocked = []
    for lesson in lessons:
        lid = lesson["lesson_metadata"]["id"]
        for s in lesson["sections"]:
            if s["type"] == "vocabulary" and progress.get(section_key(lid, s["id"])):
                unlocked += [{"es": x["es"], "pl": x["pl"]} for x in s.get("items", [])]

    if not unlocked:
        st.info("Najpierw ukończ sekcję ze słownictwem w kursie.")
        return

    if not st.session_state.get("trainer_active"):
        st.markdown('<div class="info-card"><b>5 minut, zero przygotowań.</b><br>Losujemy do 20 słów z materiału, który już ukończyłeś.</div>', unsafe_allow_html=True)
        if st.button("Rozpocznij trening", type="primary", use_container_width=True):
            st.session_state.trainer_active = True
            st.session_state.trainer_words = random.sample(unlocked, min(20, len(unlocked)))
            st.session_state.trainer_idx = 0
            st.session_state.trainer_score = 0
            st.session_state.trainer_show = False
            st.rerun()
        return

    words = st.session_state.trainer_words
    i = st.session_state.trainer_idx
    if i >= len(words):
        st.success(f"Trening ukończony: {st.session_state.trainer_score} / {len(words)}.")
        trigger_confetti()
        if st.button("Nowy trening", type="primary", use_container_width=True):
            st.session_state.trainer_active = False
            st.rerun()
        return

    word = words[i]
    st.progress(i / len(words), text=f"{i+1} / {len(words)}")
    st.markdown(f'<div class="flashcard"><div class="eyebrow">PRZYPOMNIJ SOBIE</div><div class="flash-front">{word["pl"]}</div>{"<div class=\"flash-back\">"+word["es"]+"</div>" if st.session_state.trainer_show else ""}</div>', unsafe_allow_html=True)
    if not st.session_state.trainer_show:
        if st.button("Pokaż odpowiedź", type="primary", use_container_width=True):
            st.session_state.trainer_show = True
            st.rerun()
    else:
        a,b = st.columns(2)
        if a.button("Nie pamiętałem", use_container_width=True):
            st.session_state.trainer_idx += 1
            st.session_state.trainer_show = False
            st.rerun()
        if b.button("Pamiętałem ✓", type="primary", use_container_width=True):
            st.session_state.trainer_score += 1
            st.session_state.trainer_idx += 1
            st.session_state.trainer_show = False
            st.rerun()


VERB_TABLES = {
    "Regularne": """| Osoba | -AR: trabajar | -ER: comer | -IR: vivir |
|---|---|---|---|
| Yo | trabajo | como | vivo |
| Tú | trabajas | comes | vives |
| Él / Ella / Usted | trabaja | come | vive |
| Nosotros/as | trabajamos | comemos | vivimos |
| Vosotros/as | trabajáis | coméis | vivís |
| Ellos/as / Ustedes | trabajan | comen | viven |""",
    "Nieregularne": """| Osoba | SER | ESTAR | TENER | IR |
|---|---|---|---|---|
| Yo | soy | estoy | tengo | voy |
| Tú | eres | estás | tienes | vas |
| Él / Ella / Usted | es | está | tiene | va |
| Nosotros/as | somos | estamos | tenemos | vamos |
| Vosotros/as | sois | estáis | tenéis | vais |
| Ellos/as / Ustedes | son | están | tienen | van |""",
    "Zwrotne": """| Osoba | Zaimek | levantarse |
|---|---|---|
| Yo | me | levanto |
| Tú | te | levantas |
| Él / Ella / Usted | se | levanta |
| Nosotros/as | nos | levantamos |
| Vosotros/as | os | levantáis |
| Ellos/as / Ustedes | se | levantan |""",
}


def page_grammar():
    st.title("Ściąga gramatyczna")
    st.caption("Szybki dostęp do najważniejszych konstrukcji z kursu.")
    tabs = st.tabs(list(VERB_TABLES) + ["Pretérito Perfecto", "Gerundio", "Gustar / Hay / Estar"])
    for tab, (name, content) in zip(tabs[:3], VERB_TABLES.items()):
        with tab:
            st.markdown(content)
    with tabs[3]:
        st.markdown("### Pretérito Perfecto")
        st.markdown("**haber + participio**: he, has, ha, hemos, habéis, han.")
        st.markdown("-AR → **-ado** · -ER/-IR → **-ido**")
        st.markdown("Nieregularne: **abierto, dicho, escrito, hecho, puesto, roto, sido, visto, vuelto**.")
    with tabs[4]:
        st.markdown("### Estar + gerundio")
        st.markdown("-AR → **-ando** · -ER/-IR → **-iendo**")
        st.markdown("Przykłady: *trabajando, comiendo, viviendo, leyendo, durmiendo, diciendo*.")
    with tabs[5]:
        st.markdown("### Trzy konstrukcje, które warto zapamiętać")
        st.markdown("**Gustar:** me gusta + liczba pojedyncza / bezokolicznik; me gustan + liczba mnoga.")
        st.markdown("**Hay:** informuje, że coś istnieje / znajduje się gdzieś. **Estar:** wskazuje lokalizację konkretnej rzeczy.")
        st.markdown("**Ir + a + bezokolicznik:** *Voy a trabajar* — zamierzam pracować.")


def page_analytics(lessons, progress):
    stats = overall_stats(lessons, progress)
    st.title("Twój postęp")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Ukończone sekcje", stats["done_sections"])
    c2.metric("Łącznie sekcji", stats["total_sections"])
    c3.metric("Postęp", f"{stats['progress']}%")
    c4.metric("Seria", f"{activity_streak(progress)} dni")

    rows=[]
    for lesson in lessons:
        done,total,_=lesson_stats(lesson,progress)
        rows.append({"Lekcja": f"{lesson['lesson_metadata']['level']} · {lesson['lesson_metadata']['title']}", "Ukończono": round(done/total*100) if total else 0})
    if rows:
        st.subheader("Postęp lekcji")
        st.bar_chart(pd.DataFrame(rows).set_index("Lekcja"), y="Ukończono")

    st.subheader("Odznaki")
    achievements = [
        ("🌱 Pierwszy krok", stats["done_sections"] >= 1, "Ukończ pierwszą sekcję."),
        ("📚 Dziesięć sekcji", stats["done_sections"] >= 10, "Ukończ 10 sekcji."),
        ("🧠 Pierwsza powtórka", any(k.startswith("vocab_card__") for k in progress), "Zrób pierwszą kartę SM-2."),
        ("🔥 Seria 7 dni", activity_streak(progress) >= 7, "Ucz się przez 7 kolejnych dni."),
        ("🏁 Cały poziom", any(
            all(progress.get(section_key(l["lesson_metadata"]["id"], s["id"])) for s in l["sections"])
            for l in lessons
        ), "Ukończ wszystkie sekcje jednej lekcji."),
    ]
    for name, unlocked, hint in achievements:
        st.markdown(
            f'<div class="section-chip"><b>{name}</b> {"— odblokowane" if unlocked else "— "+hint}</div>',
            unsafe_allow_html=True,
        )


def page_settings(progress):
    st.title("Ustawienia i dane")
    st.caption("Postęp jest zapisywany lokalnie w pliku JSON. Możesz go przenosić między instalacjami.")

    st.download_button(
        "⬇ Pobierz kopię postępu",
        data=json.dumps(progress, ensure_ascii=False, indent=2),
        file_name=f"hiszpanski_postep_{date.today().isoformat()}.json",
        mime="application/json",
        use_container_width=True,
    )
    uploaded = st.file_uploader("Wczytaj kopię postępu", type=["json"])
    if uploaded and st.button("Przywróć postęp", type="primary"):
        try:
            data=json.load(uploaded)
            if not isinstance(data, dict):
                raise ValueError
            save_progress_data(data)
            st.success("Postęp przywrócony.")
            st.rerun()
        except Exception:
            st.error("Nie udało się odczytać pliku.")

    st.divider()
    st.markdown("### Strefa ostrożności")
    st.caption("Reset usuwa lokalny postęp i historię powtórek.")
    if st.button("Resetuj cały postęp", type="secondary"):
        st.session_state.confirm_reset = True
    if st.session_state.get("confirm_reset"):
        st.warning("To działanie jest nieodwracalne bez kopii JSON.")
        a,b=st.columns(2)
        if a.button("Tak, usuń postęp"):
            save_progress_data({})
            st.session_state.confirm_reset=False
            st.rerun()
        if b.button("Anuluj"):
            st.session_state.confirm_reset=False
            st.rerun()


def main():
    progress = get_progress_data()
    lessons = get_catalog()
    if not lessons:
        st.error("Brak danych lekcji w katalogu data/.")
        return

    with st.sidebar:
        st.markdown('<div class="brand">🇪🇸 Hiszpański</div><div class="brand-sub">nauka po ludzku</div>', unsafe_allow_html=True)
        pages = ["Start", "Kurs", "Powtórki", "Trener słówek", "Ściąga", "Postęp", "Dane"]
        current = st.session_state.get("page", "Start")
        page = st.radio("Nawigacja", pages, index=pages.index(current) if current in pages else 0)
        st.session_state.page = page
        st.divider()
        stats=overall_stats(lessons,progress)
        st.caption("TWÓJ POSTĘP")
        st.progress(stats["progress"]/100)
        st.write(f"**{stats['progress']}%** kursu")
        st.caption(f"{len(due_cards(lessons, progress))} kart do powtórki · {activity_streak(progress)} dni serii")

    if st.session_state.page == "Start":
        page_home(lessons, progress)
    elif st.session_state.page == "Kurs":
        page_course(lessons, progress)
    elif st.session_state.page == "Lekcja":
        page_lesson(lessons, progress)
    elif st.session_state.page == "Powtórki":
        page_review(lessons, progress)
    elif st.session_state.page == "Trener słówek":
        page_trainer(lessons, progress)
    elif st.session_state.page == "Ściąga":
        page_grammar()
    elif st.session_state.page == "Postęp":
        page_analytics(lessons, progress)
    elif st.session_state.page == "Dane":
        page_settings(progress)


if __name__ == "__main__":
    main()
