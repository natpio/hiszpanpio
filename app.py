import streamlit as st
import os
from datetime import datetime, timedelta

from utils import (
    load_lesson, get_progress_data, save_progress_data, 
    calculate_sm2, set_random_background_and_styles, trigger_js_confetti
)

st.set_page_config(page_title="Kurs Hiszpańskiego A1", page_icon="🇪🇸", layout="wide")

def main():
    set_random_background_and_styles()
    
    st.sidebar.title("📚 Kurs A1 - Ultra Pro")
    mode = st.sidebar.radio("Widok:", ["🎓 Moduły Kursu", "🧠 Tryb Powtórek (Fiszki)", "📊 Dashboard Analityczny"])
    st.sidebar.markdown("---")
    
    lesson_dir = os.path.join("data", "A1")
    lesson_files = sorted([f for f in os.listdir(lesson_dir) if f.endswith('.json')]) if os.path.exists(lesson_dir) else []
    progress = get_progress_data()

    # -------------------------------------
    # TRYB 1: MODUŁY KURSU
    # -------------------------------------
    if mode == "🎓 Moduły Kursu":
        if not lesson_files:
            st.warning("Brak plików lekcji w folderze data/A1.")
            return

        selected_file = st.sidebar.selectbox("Wybierz lekcję", lesson_files)
        lesson = load_lesson(selected_file)
        
        st.sidebar.markdown("### Struktura lekcji")
        completed_sections = [s['id'] for s in lesson['sections'] if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)]
        
        section_options = [(s['title'], "✅" if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False) else "⭕") for s in lesson['sections']]
        selected_name = st.sidebar.radio("Sekcje:", [opt[0] for opt in section_options])
        current_section = next(s for s in lesson['sections'] if s['title'] == selected_name)
        
        st.sidebar.markdown(f"**Postęp lekcji:** {len(completed_sections)}/{len(lesson['sections'])} ukończonych")

        st.title(lesson['lesson_metadata']['title'])
        st.header(current_section['title'])
        
        # --- NOWOŚĆ: TŁUMACZENIA DIALOGÓW ---
        if current_section['type'] == 'dialog':
            for line in current_section['content']:
                st.markdown(f"**{line['speaker']}**: {line['text']}")
                if 'translation' in line:
                    st.caption(f"*{line['translation']}*")
                
        # --- NOWOŚĆ: MINI-FISZKI PRZED ZAKOŃCZENIEM ---
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
                
        # --- NOWOŚĆ: GRAMATYKA MARKDOWN ---
        elif current_section['type'] == 'grammar':
            # st.markdown obsługuje teraz bogate tabele i pogrubienia prosto z JSON-a
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
        
        # BLOKADA: Przycisk zaliczenia słownictwa pojawia się dopiero po przejściu Mini-Fiszek
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

    # -------------------------------------
    # TRYB 2: FISZKI (SUPERMEMO)
    # -------------------------------------
    elif mode == "🧠 Tryb Powtórek (Fiszki)":
        st.title("🧠 Globalny Tryb Powtórek")
        today_str = datetime.now().strftime("%Y-%m-%d")
        due_cards = []
        
        for f in lesson_files:
            l_data = load_lesson(f)
            l_id = l_data['lesson_metadata']['id']
            for s in l_data['sections']:
                if s['type'] == 'vocabulary' and progress.get(f"{l_id}_{s['id']}", False):
                    for item in s['items']:
                        vocab_key = f"vocab_{l_id}_{item['es']}"
                        card_data = progress.get(vocab_key)
                        if not card_data or card_data['next_review'] <= today_str:
                            due_cards.append({'key': vocab_key, 'es': item['es'], 'pl': item['pl']})

        if not due_cards:
            st.success("🎉 Świetna robota! Brak słówek do powtórki na dzisiaj.")
            trigger_js_confetti()
        else:
            if 'current_card_index' not in st.session_state: st.session_state.current_card_index = 0
            if 'show_answer' not in st.session_state: st.session_state.show_answer = False
            if st.session_state.current_card_index >= len(due_cards): st.session_state.current_card_index = 0
                
            active_card = due_cards[st.session_state.current_card_index]
            st.info(f"Słówek do powtórki w tej sesji: **{len(due_cards)}**")
            
            st.markdown(f"<div class='flashcard-front'>{active_card['pl']}</div>", unsafe_allow_html=True)
            
            if not st.session_state.show_answer:
                if st.button("Pokaż odpowiedź", use_container_width=True):
                    st.session_state.show_answer = True
                    st.rerun()
            else:
                st.markdown(f"<div class='flashcard-back'>{active_card['es']}</div>", unsafe_allow_html=True)
                st.write("Jak dobrze pamiętałeś to słówko?")
                
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
    # TRYB 3: DASHBOARD ANALITYCZNY
    # -------------------------------------
    elif mode == "📊 Dashboard Analityczny":
        st.title("📊 Dashboard Analityczny Kursu")
        total_sections, completed_sections_count, words_in_learning = 0, 0, 0
        lesson_progress_summary = []
        
        for f in lesson_files:
            l_data = load_lesson(f)
            l_total = len(l_data['sections'])
            l_done = sum(1 for s in l_data['sections'] if progress.get(f"{l_data['lesson_metadata']['id']}_{s['id']}", False))
            total_sections += l_total
            completed_sections_count += l_done
            pct = int((l_done / l_total) * 100) if l_total > 0 else 0
            lesson_progress_summary.append({"Lekcja": l_data['lesson_metadata']['title'], "Ukończono (%)": pct, "Zaliczone": f"{l_done}/{l_total}"})

        words_in_learning = sum(1 for key in progress if key.startswith("vocab_"))

        col1, col2, col3 = st.columns(3)
        col1.metric("Ukończone sekcje", f"{completed_sections_count} / {total_sections}")
        col2.metric("Ogólny postęp", f"{int((completed_sections_count / total_sections) * 100) if total_sections > 0 else 0}%")
        col3.metric("Opanowane słówka", words_in_learning)

        st.markdown("---")
        for item in lesson_progress_summary:
            st.write(f"**{item['Lekcja']}** — {item['Zaliczone']} sekcji")
            st.progress(item['Ukończono (%)'])

if __name__ == "__main__":
    main()
