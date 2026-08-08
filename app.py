import streamlit as st
import os
import random
from datetime import datetime, timedelta

from utils import (
    load_lesson, get_progress_data, save_progress_data, 
    calculate_sm2, set_random_background_and_styles, trigger_js_confetti
)

st.set_page_config(page_title="Kurs Hiszpańskiego Ultra Pro", page_icon="🇪🇸", layout="wide")

def main():
    set_random_background_and_styles()
    
    # 1. DYNAMICZNE WYKRYWANIE POZIOMÓW
    data_dir = "data"
    available_levels = [d for d in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, d))]
    available_levels.sort() # np. ['A1', 'A2']
    
    if not available_levels:
        st.error("Brak folderów z danymi (np. data/A1). Utwórz strukturę plików.")
        return

    st.sidebar.title("📚 Kurs Hiszpańskiego")
    selected_level = st.sidebar.selectbox("Wybierz poziom:", available_levels)
    st.sidebar.markdown(f"**Obecnie przerabiasz: {selected_level}**")
    st.sidebar.markdown("---")
    
    mode = st.sidebar.radio("Widok:", [
        "🎓 Moduły Kursu", 
        "🧠 Tryb Powtórek (SM-2)", 
        "🏋️ Trener Słówek (Losowe 20)",
        "📖 Tablice Czasowników", 
        "📊 Dashboard Analityczny"
    ])
    st.sidebar.markdown("---")
    
    # Pobieranie plików dla WYBRANEGO poziomu
    lesson_dir = os.path.join(data_dir, selected_level)
    lesson_files = sorted([f for f in os.listdir(lesson_dir) if f.endswith('.json')]) if os.path.exists(lesson_dir) else []
    
    # Pobieranie WSZYSTKICH lekcji dla trybów globalnych (Fiszki, Dashboard)
    all_lessons_data = []
    for lvl in available_levels:
        lvl_dir = os.path.join(data_dir, lvl)
        for f in os.listdir(lvl_dir):
            if f.endswith('.json'):
                all_lessons_data.append(load_lesson(lvl, f))

    progress = get_progress_data()

    # -------------------------------------
    # TRYB 1: MODUŁY KURSU
    # -------------------------------------
    if mode == "🎓 Moduły Kursu":
        if not lesson_files:
            st.warning(f"Brak plików lekcji w folderze {selected_level}.")
            return

        selected_file = st.sidebar.selectbox("Wybierz lekcję", lesson_files)
        lesson = load_lesson(selected_level, selected_file)
        
        st.sidebar.markdown("### Struktura lekcji")
        completed_sections = [s['id'] for s in lesson['sections'] if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)]
        
        section_options = [(s['title'], "✅" if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False) else "⭕") for s in lesson['sections']]
        selected_name = st.sidebar.radio("Sekcje:", [opt[0] for opt in section_options])
        current_section = next(s for s in lesson['sections'] if s['title'] == selected_name)
        
        st.sidebar.markdown(f"**Postęp lekcji:** {len(completed_sections)}/{len(lesson['sections'])} ukończonych")

        st.title(f"[{selected_level}] {lesson['lesson_metadata']['title']}")
        st.header(current_section['title'])
        
        if current_section['type'] == 'dialog':
            for line in current_section['content']:
                st.markdown(f"**{line['speaker']}**: {line['text']}")
                if 'translation' in line:
                    st.caption(f"*{line['translation']}*")
                
        elif current_section['type'] == 'vocabulary':
            st.write("### Spis słówek")
            for item in current_section['items']:
                st.write(f"✅ **{item['es']}** - {item['pl']}")
            
            st.markdown("---")
            st.subheader("🧠 Trening nowych słówek")
            st.write("Zanim przejdziesz dalej, przećwicz nowe słownictwo na szybkich fiszkach!")
            
            vocab_key = f"vocab_idx_{lesson['lesson_metadata']['id']}_{current_section['id']}"
            if vocab_key not in st.session_state:
                st.session_state[vocab_key] = 0
            
            if 'vocab_show_answer' not in st.session_state:
                st.session_state.vocab_show_answer = False

            idx = st.session_state[vocab_key]
            vocab_items = current_section['items']
            
            if idx < len(vocab_items):
                active_word = vocab_items[idx]
                st.progress(idx / len(vocab_items), text=f"Fiszka {idx+1} z {len(vocab_items)}")
                
                st.markdown(f"<div class='flashcard-front'>{active_word['pl']}</div>", unsafe_allow_html=True)
                
                if not st.session_state.vocab_show_answer:
                    if st.button("Pokaż hiszpańskie tłumaczenie", key="show_es", use_container_width=True):
                        st.session_state.vocab_show_answer = True
                        st.rerun()
                else:
                    st.markdown(f"<div class='flashcard-back'>{active_word['es']}</div>", unsafe_allow_html=True)
                    if st.button("Następne słówko ➡️", key="next_es", use_container_width=True):
                        st.session_state[vocab_key] += 1
                        st.session_state.vocab_show_answer = False
                        st.rerun()
            else:
                st.progress(100, text="Zakończono trening!")
                st.success("Brawo! Przećwiczyłeś wszystkie nowe słówka.")
                if st.button("🔄 Przećwicz ponownie (Opcjonalnie)"):
                    st.session_state[vocab_key] = 0
                    st.session_state.vocab_show_answer = False
                    st.rerun()
                
        elif current_section['type'] == 'grammar':
            st.markdown(current_section['content'])
                
        elif current_section['type'] == 'exercises':
            st.write("Wypełnij luki i naciśnij Enter, aby sprawdzić odpowiedź.")
            for i, ex in enumerate(current_section['items']):
                with st.expander(f"💡 {ex['translation']}"):
                    ans = st.text_input(ex['question'].replace("___", "[ ... ]"), key=f"ex_{selected_file}_{current_section['id']}_{i}")
                    if ans:
                        if ans.strip().lower() == ex['answer'].lower():
                            st.success("✅ ¡Perfecto!")
                        else:
                            st.error(f"❌ Poprawnie: {ex['answer']}")

        st.markdown("---")
        prog_key = f"{lesson['lesson_metadata']['id']}_{current_section['id']}"
        
        can_finish = True
        if current_section['type'] == 'vocabulary':
            if st.session_state.get(f"vocab_idx_{lesson['lesson_metadata']['id']}_{current_section['id']}", 0) < len(current_section['items']):
                can_finish = False
                st.info("💡 Przeklikaj wszystkie fiszki powyżej, aby odblokować przycisk zakończenia sekcji.")

        if not progress.get(prog_key, False):
            if can_finish:
                if st.button("Zakończ tę sekcję", use_container_width=True):
                    progress[prog_key] = True
                    save_progress_data(progress)
                    trigger_js_confetti()
                    st.rerun()
        else:
            st.success("🎉 Sekcja ukończona!")
            if current_section['type'] == 'vocabulary':
                st.info("💡 Słówka z tej sekcji zostały odblokowane do globalnych powtórek SuperMemo!")
            elif current_section['type'] == 'exercises':
                st.info("💡 Te ćwiczenia zostały odblokowane do powtórek SuperMemo (jako fiszki ze zdaniami)!")

    # -------------------------------------
    # TRYB 2: FISZKI (SUPERMEMO + ĆWICZENIA)
    # -------------------------------------
    elif mode == "🧠 Tryb Powtórek (SM-2)":
        st.title("🧠 Globalny Tryb Powtórek (SM-2)")
        st.write("Algorytm dba o to, byś powtarzał słówka i zdania z lukami w idealnym momencie. Pobiera wiedzę ze wszystkich odblokowanych poziomów!")
        today_str = datetime.now().strftime("%Y-%m-%d")
        due_cards = []
        
        for l_data in all_lessons_data:
            l_id = l_data['lesson_metadata']['id']
            for s in l_data['sections']:
                if progress.get(f"{l_id}_{s['id']}", False):
                    if s['type'] == 'vocabulary':
                        for item in s['items']:
                            vocab_key = f"vocab_{l_id}_{item['es']}"
                            card_data = progress.get(vocab_key)
                            if not card_data or card_data['next_review'] <= today_str:
                                due_cards.append({'key': vocab_key, 'front': item['pl'], 'back': item['es']})
                    elif s['type'] == 'exercises':
                        for i, ex in enumerate(s['items']):
                            ex_key = f"ex_card_{l_id}_{s['id']}_{i}"
                            card_data = progress.get(ex_key)
                            if not card_data or card_data['next_review'] <= today_str:
                                front_text = f"{ex['question'].replace('___', '[ ... ]')}<br><br><span style='font-size: 0.8em; color: #5c2c16;'>💡 {ex['translation']}</span>"
                                back_text = ex['question'].replace("___", f"<b style='color:#b33929;'>{ex['answer']}</b>")
                                due_cards.append({'key': ex_key, 'front': front_text, 'back': back_text})

        if not due_cards:
            st.success("🎉 Świetna robota! Nie masz na dziś żadnych elementów do powtórki.")
            trigger_js_confetti()
        else:
            if 'current_card_index' not in st.session_state: st.session_state.current_card_index = 0
            if 'show_answer' not in st.session_state: st.session_state.show_answer = False
            if st.session_state.current_card_index >= len(due_cards): st.session_state.current_card_index = 0
                
            active_card = due_cards[st.session_state.current_card_index]
            st.info(f"Fiszek do powtórki w tej sesji: **{len(due_cards)}**")
            
            st.markdown(f"<div class='flashcard-front'>{active_card['front']}</div>", unsafe_allow_html=True)
            
            if not st.session_state.show_answer:
                if st.button("Pokaż odpowiedź", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                st.markdown(f"<div class='flashcard-back'>{active_card['back']}</div>", unsafe_allow_html=True)
                st.write("Jak dobrze to pamiętałeś?")
                
                cols = st.columns(4)
                buttons = [("Nie wiem (0)", 0), ("Trudne (3)", 3), ("Dobre (4)", 4), ("Łatwe (5)", 5)]
                
                def process_answer(quality):
                    key = active_card['key']
                    if key not in progress:
                        progress[key] = {'repetitions': 0, 'ease_factor': 2.5, 'interval': 0, 'next_review': today_str}
                    rep, ef, intrv = progress[key]['repetitions'], progress[key]['ease_factor'], progress[key]['interval']
                    new_rep, new_ef, new_intrv = calculate_sm2(quality, rep, ef, intrv)
                    progress[key] = {
                        'repetitions': new_rep, 'ease_factor': new_ef, 'interval': new_intrv,
                        'next_review': (datetime.now() + timedelta(days=new_intrv)).strftime("%Y-%m-%d")
                    }
                    save_progress_data(progress)
                    st.session_state.show_answer = False
                    st.rerun()

                for col, (label, q_val) in zip(cols, buttons):
                    if col.button(label, use_container_width=True): process_answer(q_val)

    # -------------------------------------
    # TRYB 3: TRENER SŁÓWEK
    # -------------------------------------
    elif mode == "🏋️ Trener Słówek (Losowe 20)":
        st.title("🏋️ Szybki Trening Słówek")
        st.write("Idealne na 5 minut przerwy! Aplikacja wylosuje 20 słówek ze wszystkich zakończonych przez Ciebie sekcji.")
        
        unlocked_words = []
        for l_data in all_lessons_data:
            l_id = l_data['lesson_metadata']['id']
            for s in l_data['sections']:
                if s['type'] == 'vocabulary' and progress.get(f"{l_id}_{s['id']}", False):
                    for item in s['items']:
                        unlocked_words.append(item)

        if not unlocked_words:
            st.warning("Nie ukończyłeś jeszcze żadnej sekcji ze słownictwem. Przerób moduły z lekcji, aby odblokować słówka!")
        else:
            if 'trainer_active' not in st.session_state or not st.session_state.trainer_active:
                if st.button("Rozpocznij losowanie 20 słówek 🚀", use_container_width=True):
                    st.session_state.trainer_active = True
                    sample_size = min(20, len(unlocked_words))
                    st.session_state.trainer_words = random.sample(unlocked_words, sample_size)
                    st.session_state.trainer_idx = 0
                    st.session_state.trainer_score = 0
                    st.session_state.trainer_show_ans = False
                    st.rerun()
            else:
                idx = st.session_state.trainer_idx
                words = st.session_state.trainer_words
                
                if idx < len(words):
                    st.progress(idx / len(words), text=f"Słówko {idx + 1} z {len(words)}")
                    current_word = words[idx]
                    
                    st.markdown(f"<div class='flashcard-front'>{current_word['pl']}</div>", unsafe_allow_html=True)
                    
                    if not st.session_state.trainer_show_ans:
                        if st.button("Pokaż odpowiedź", use_container_width=True):
                            st.session_state.trainer_show_ans = True
                            st.rerun()
                    else:
                        st.markdown(f"<div class='flashcard-back'>{current_word['es']}</div>", unsafe_allow_html=True)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔴 Nie pamiętałem", use_container_width=True):
                                st.session_state.trainer_idx += 1
                                st.session_state.trainer_show_ans = False
                                st.rerun()
                        with col2:
                            if st.button("🟢 Pamiętałem (+1)", use_container_width=True):
                                st.session_state.trainer_score += 1
                                st.session_state.trainer_idx += 1
                                st.session_state.trainer_show_ans = False
                                st.rerun()
                else:
                    st.progress(100, text="Trening zakończony!")
                    st.success(f"Twój wynik: **{st.session_state.trainer_score} / {len(words)}**")
                    trigger_js_confetti()
                    if st.button("Zakończ i wróć", use_container_width=True):
                        st.session_state.trainer_active = False
                        st.rerun()

    # -------------------------------------
    # TRYB 4: TABLICE CZASOWNIKÓW 
    # -------------------------------------
    elif mode == "📖 Tablice Czasowników":
        st.title("📖 Tablice Odmian Czasowników")
        st.write("Twój podręczny niezbędnik gramatyczny. Szybka ściągawka z najważniejszych hiszpańskich zasad.")
        
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
            "📏 Regularne", 
            "🔥 Nieregularne", 
            "🔀 Wymiana Samogł.",
            "🔄 Zwrotne", 
            "⏳ Przeszły (Perf.)",
            "🏃 Gerundio",
            "⭐ Specjalne",
            "👈 Zaimki"
        ])
        
        with tab1:
            st.subheader("Czasowniki Regularne (Presente de Indicativo)")
            st.markdown("""
            | Osoba (Zaimek) | -AR (np. **trabajar** - pracować) | -ER (np. **comer** - jeść) | -IR (np. **vivir** - mieszkać/żyć) |
            | :--- | :--- | :--- | :--- |
            | **Yo** (Ja) | trabaj**o** | com**o** | viv**o** |
            | **Tú** (Ty) | trabaj**as** | com**es** | viv**es** |
            | **Él/Ella/Usted** (On/Ona/Pan/i) | trabaj**a** | com**e** | viv**e** |
            | **Nosotros/as** (My) | trabaj**amos** | com**emos** | viv**imos** |
            | **Vosotros/as** (Wy) | trabaj**áis** | com**éis** | viv**ís** |
            | **Ellos/Ellas/Ustedes** (Oni/One/Państwo)| trabaj**an** | com**en** | viv**en** |
            """)
            
        with tab2:
            st.subheader("Najważniejsze Czasowniki Nieregularne")
            st.markdown("""
            | Osoba | SER (być - cechy) | ESTAR (być - lokalizacja) | TENER (mieć) | IR (iść/jechać) |
            | :--- | :--- | :--- | :--- | :--- |
            | **Yo** | soy | estoy | tengo | voy |
            | **Tú** | eres | estás | tienes | vas |
            | **Él/Ella/Usted** | es | está | tiene | va |
            | **Nosotros/as** | somos | estamos | tenemos | vamos |
            | **Vosotros/as** | sois | estáis | tenéis | vais |
            | **Ellos/Ellas/Ustedes**| son | están | tienen | van |
            """)
            st.markdown("---")
            st.markdown("#### Nieregularne TYLKO w 1. osobie (Dla 'Yo')")
            st.write("W tych czasownikach tylko forma 'Ja' jest inna, reszta odmienia się w 100% regularnie.")
            st.markdown("""
            | Bezokolicznik | Forma 'Yo' (Ja) | Forma 'Tú' (Ty) | Znaczenie |
            | :--- | :--- | :--- | :--- |
            | **Hacer** | **hago** | haces | robić |
            | **Salir** | **salgo** | sales | wychodzić |
            | **Poner** | **pongo** | pones | kłaść / zakładać |
            | **Saber** | **sé** | sabes | wiedzieć / umieć |
            | **Dar** | **doy** | das | dawać |
            """)
            
        with tab3:
            st.subheader("Wymiana Samogłoskowa ('Zasada Buta')")
            st.write("Wielu hiszpańskich czasowników dotyczy wymiana w rdzeniu (w środku słowa). Samogłoska wymienia się we wszystkich osobach **OPRÓCZ** 'nosotros' i 'vosotros'.")
            st.markdown("""
            #### 1. O ➡️ UE
            * **Costar** (kosztować): yo c**ue**sto, tú c**ue**stas, él c**ue**sta, nosotros costamos, vosotros costáis, ellos c**ue**stan.
            * **Volar** (latać): v**ue**lo, v**ue**las, v**ue**la, volamos, voláis, v**ue**lan.
            * **Dormir** (spać): d**ue**rmo, d**ue**rmes...
            
            #### 2. E ➡️ IE
            * **Querer** (chcieć): yo qu**ie**ro, tú qu**ie**res, él qu**ie**re, nosotros queremos, vosotros queréis, ellos qu**ie**ren.
            * **Pensar** (myśleć): p**ie**nso, p**ie**nsas...
            * **Empezar** (zaczynać): emp**ie**zo, emp**ie**zas...
            
            #### 3. E ➡️ I
            * **Pedir** (prosić / zamawiać): p**i**do, p**i**des, p**i**de, pedimos, pedís, p**i**den.
            """)
            
        with tab4:
            st.subheader("Czasowniki Zwrotne (z cząstką 'się')")
            st.write("Zaimek zwrotny wędruje ZAWSZE przed odmieniony czasownik.")
            st.markdown("""
            | Osoba | Zaimek | LEVANTARSE (budzić się / wstawać) |
            | :--- | :--- | :--- |
            | **Yo** | **me** | levanto |
            | **Tú** | **te** | levantas |
            | **Él/Ella/Usted** | **se** | levanta |
            | **Nosotros/as** | **nos** | levantamos |
            | **Vosotros/as** | **os** | levantáis |
            | **Ellos/Ellas/Ustedes**| **se** | levantan |
            """)
            
        with tab5:
            st.subheader("Czas Przeszły (Pretérito Perfecto)")
            st.write("Składa się z posiłkowego **HABER** i imiesłowu biernego.")
            st.markdown("""
            #### 1. Odmiana czasownika posiłkowego HABER
            | Yo | Tú | Él/Ella/Usted | Nosotros/as | Vosotros/as | Ellos/Ellas/Ustedes |
            | :--- | :--- | :--- | :--- | :--- | :--- |
            | **he** | **has** | **ha** | **hemos** | **habéis** | **han** |

            #### 2. Tworzenie regularnych imiesłowów
            * Czasowniki na **-AR** ➡️ dodajemy **-ado** (np. trabajar ➡️ **trabajado**)
            * Czasowniki na **-ER** / **-IR** ➡️ dodajemy **-ido** (np. comer ➡️ **comido**, vivir ➡️ **vivido**)

            #### 3. Najważniejsze imiesłowy NIEREGULARNE 🔥
            | Bezokolicznik | Znaczenie | Forma nieregularna |
            | :--- | :--- | :--- |
            | **Abrir** | otwierać | **abierto** (otwarty) |
            | **Decir** | mówić | **dicho** (powiedziany) |
            | **Escribir** | pisać | **escrito** (napisany) |
            | **Hacer** | robić | **hecho** (zrobiony) |
            | **Poner** | kłaść | **puesto** (położony) |
            | **Romper** | psuć / łamać | **roto** (zepsuty / złamany) |
            | **Ser** | być | **sido** (był) |
            | **Ver** | widzieć | **visto** (widziany) |
            | **Volver** | wracać | **vuelto** (wrócił) |
            """)
            
        with tab6:
            st.subheader("Czas Ciągły (Estar + Gerundio)")
            st.write("Używamy go do opisania czynności, która dzieje się **dokładnie w tej chwili**.")
            st.markdown("""
            #### 1. Tworzenie Gerundio
            | Końcówka bezokolicznika | Końcówka Gerundio | Przykład |
            | :--- | :--- | :--- |
            | **-AR** | **-ando** | trabajar ➡️ trabaj**ando** |
            | **-ER / -IR** | **-iendo** | comer ➡️ com**iendo** |
            
            #### 2. Najważniejsze wyjątki (Zmiana pisowni)
            * **Leer** (czytać) ➡️ **leyendo**
            * **Dormir** (spać) ➡️ **durmiendo**
            * **Decir** (mówić) ➡️ **diciendo**
            * **Pedir** (zamawiać) ➡️ **pidiendo**
            
            #### 3. Przykłady z odmienionym ESTAR
            * *Yo **estoy volando** en el simulador.* (Właśnie teraz lecę w symulatorze).
            * *Natalia **está conduciendo**.* (Natalia w tym momencie prowadzi).
            """)
            
        with tab7:
            st.subheader("Konstrukcje Specjalne")
            st.markdown("#### 1. HAY vs ESTAR")
            st.markdown("""
            Najczęstszy problem! Kiedy użyć którego "jest"?
            | HAY (Istnienie - "tam jest coś") | ESTAR (Lokalizacja - "to coś jest tu") |
            | :--- | :--- |
            | Rzeczy nieznane, nowe w rozmowie | Rzeczy konkretne, znane rozmówcy |
            | Z rodzajnikami nieokreślonymi: **un, una, unos, unas** | Z rodzajnikami określonymi: **el, la, los, las** |
            | Z liczbami: **dos, tres, muchos** | Z zaimkami dzierżawczymi: **mi, tu, su** |
            | *Hay una mesa* (Jest jakiś stół) | *La mesa está aquí* (Ten stół jest tutaj) |
            """)
            
            st.markdown("#### 2. Czasownik GUSTAR (Lubić / Smakować)")
            st.markdown("""
            *Dosłownie: 'Coś sprawia mi przyjemność'. Dopasowujemy końcówkę do tego, **co** lubimy, a nie kto lubi.*
            * **(A mí) me gusta** + l. poj. (np. *la carne*) / bezokolicznik (np. *comer*)
            * **(A ti) te gustan** + l. mnoga (np. *los tomates*)
            * Inne zaimki: **le** (jemu/jej), **nos** (nam), **os** (wam), **les** (im).
            """)
            st.markdown("#### 3. Plany na przyszłość: IR + A + Bezokolicznik")
            st.markdown("""
            * **Voy a trabajar.** - Zamierzam pracować.
            * **Vamos a comer.** - Zamierzamy jeść.
            """)
            st.markdown("#### 4. Obowiązek: TENER QUE vs HAY QUE")
            st.markdown("""
            * **Tengo que** + bezokolicznik -> *Ja muszę...* (Osobisty obowiązek)
            * **Hay que** + bezokolicznik -> *Trzeba...* (Ogólna zasada, forma bezosobowa)
            """)
            
        with tab8:
            st.subheader("Zaimki Wskazujące (Ten, Ta, Ci, Te)")
            st.write("Używamy ich, by wskazać przedmioty znajdujące się **blisko** nas.")
            st.markdown("""
            | Liczba | Rodzaj Męski | Rodzaj Żeński |
            | :--- | :--- | :--- |
            | **Pojedyncza (Ten/Ta)** | **este** (np. *este coche* - ten samochód) | **esta** (np. *esta maleta* - ta walizka) |
            | **Mnoga (Ci/Te)** | **estos** (np. *estos zapatos* - te buty) | **estas** (np. *estas chicas* - te dziewczyny) |
            
            💡 **Uwaga na wyjątek:** Słowo *este* często myli się z *esto*.
            * **Este** używamy z rzeczownikiem męskim (*Este ordenador* - Ten komputer).
            * **Esto** to forma neutralna, używana gdy nie znamy nazwy przedmiotu, na który patrzymy (*¿Qué es esto?* - Co to jest?).
            """)

    # -------------------------------------
    # TRYB 5: DASHBOARD ANALITYCZNY
    # -------------------------------------
    elif mode == "📊 Dashboard Analityczny":
        st.title("📊 Dashboard Analityczny Kursu")
        total_sections, completed_sections_count = 0, 0
        lesson_progress_summary = []
        
        for l_data in all_lessons_data:
            l_total = len(l_data['sections'])
            l_done = sum(1 for s in l_data['sections'] if progress.get(f"{l_data['lesson_metadata']['id']}_{s['id']}", False))
            total_sections += l_total
            completed_sections_count += l_done
            pct = int((l_done / l_total) * 100) if l_total > 0 else 0
            lesson_progress_summary.append({
                "Poziom": l_data['lesson_metadata']['level'], 
                "Lekcja": l_data['lesson_metadata']['title'], 
                "Ukończono (%)": pct, 
                "Zaliczone": f"{l_done}/{l_total}"
            })

        words_in_learning = sum(1 for key in progress if key.startswith("vocab_"))
        ex_in_learning = sum(1 for key in progress if key.startswith("ex_card_"))

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Ukończone sekcje", f"{completed_sections_count} / {total_sections}")
        col2.metric("Ogólny postęp", f"{int((completed_sections_count / total_sections) * 100) if total_sections > 0 else 0}%")
        col3.metric("Opanowane słówka", words_in_learning)
        col4.metric("Opanowane zdania", ex_in_learning)

        st.markdown("---")
        for item in lesson_progress_summary:
            st.write(f"**[{item['Poziom']}] {item['Lekcja']}** — {item['Zaliczone']} sekcji")
            st.progress(item['Ukończono (%)'])

if __name__ == "__main__":
    main()
