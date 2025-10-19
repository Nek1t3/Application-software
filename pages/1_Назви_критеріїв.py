import streamlit as st

st.title("✏️ Редагування назв критеріїв та альтернатив")

num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=9, value=3)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=9, value=3)

criteria_names = []
for i in range(num_criteria):
    name = st.text_input(f"Назва критерію {i+1}:", st.session_state.get(f"crit_{i}", f"Критерій {i+1}"))
    criteria_names.append(name)
    st.session_state[f"crit_{i}"] = name

alternative_names = []
for j in range(num_alternatives):
    name = st.text_input(f"Назва альтернативи {j+1}:", st.session_state.get(f"alt_{j}", f"Альтернатива {j+1}"))
    alternative_names.append(name)
    st.session_state[f"alt_{j}"] = name

st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

st.success("✅ Назви збережено! Перейдіть на головну сторінку, щоб побачити оновлену діаграму.")
