import streamlit as st
import json
import os

# Konfiguracja strony
st.set_page_config(page_title="Kurs Hiszpańskiego A1", layout="wide")

# Funkcje pomocnicze
def load_lesson(filename):
    with open(os.path.join("data", "A1", filename), "r", encoding="utf-8") as f:
        return json.load(f)

def get_progress_data():
    if 'user_progress' not in st.session_state:
        # Wczytujemy z pliku lub tworzymy pusty słownik
        if os.path.exists("data/user_progress.json"):
            with open("data/user_progress.json", "r") as f:
                st.session_state.user_progress = json.load(f)
        else:
            st.session_state.user_progress = {}
    return st.session_state.user_progress

def save_progress_data(data):
    with open("data/user_progress.json", "w") as f:
        json.dump(data, f)
    st.session_state.user_progress = data

def main():
    st.sidebar.title("📚 Kurs A1 - Ultra Pro")
    
    # 1. Wybór lekcji
    lesson_files = [f for f in os.listdir("data/A1") if f.endswith('.json')]
    lesson_files.sort()
    selected_file = st.sidebar.selectbox("Wybierz lekcję", lesson_files)
    lesson = load_lesson(selected_file)
    progress = get_progress_data()
    
    # 2. Dynamiczne Menu Boczne z Licznikami
    st.sidebar.markdown("---")
    st.sidebar.subheader("Struktura lekcji")
    
    # Liczenie ukończonych sekcji
    completed_sections = [s['id'] for s in lesson['sections'] if progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)]
    
    section_options = []
    for s in lesson['sections']:
        is_done = progress.get(f"{lesson['lesson_metadata']['id']}_{s['id']}", False)
        section_options.append((s['title'], "✅" if is_done else "⭕"))
    
    selected_name = st.sidebar.radio("Sekcje:", [opt[0] for opt in section_options])
    current_section = next(s for s in lesson['sections'] if s['title'] == selected_name)
    
    # Wyświetlanie postępu w menu
    st.sidebar.markdown(f"**Postęp lekcji:** {len(completed_sections)}/{len(lesson['sections'])} ukończonych")

    # 3. Renderowanie treści głównej
    st.title(lesson['lesson_metadata']['title'])
    st.header(current_section['title'])
    
    # Obsługa bloków treści
    if current_section['type'] == 'dialog':
        for line in current_section['content']:
            st.write(f"**{line['speaker']}**: {line['text']}")
            
    elif current_section['type'] == 'vocabulary':
        for item in current_section['items']:
            st.write(f"✅ **{item['es']}** - {item['pl']}")
            
    elif current_section['type'] == 'grammar':
        st.info(current_section['content'])
        
    elif current_section['type'] == 'exercises':
        for i, ex in enumerate(current_section['items']):
            with st.expander(f"Ćwiczenie {i+1}: {ex['translation']}"):
                ans = st.text_input(ex['question'], key=f"ex_{i}")
                if ans:
                    if ans.strip().lower() == ex['answer'].lower():
                        st.success("¡Perfecto!")
                    else:
                        st.error(f"❌ Poprawnie: {ex['answer']}")

    # 4. Przycisk zaliczenia sekcji
    st.markdown("---")
    prog_key = f"{lesson['lesson_metadata']['id']}_{current_section['id']}"
    if not progress.get(prog_key, False):
        if st.button("Zakończ tę sekcję"):
            progress[prog_key] = True
            save_progress_data(progress)
            st.rerun()
    else:
        st.success("Sekcja ukończona!")

if __name__ == "__main__":
    main()
