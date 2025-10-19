import streamlit as st

st.title("✏️ Редагування назв критеріїв та альтернатив")

# Отримуємо кількість з session_state (тільки для відображення)
num_criteria = st.session_state.get("num_criteria", 3)
num_alternatives = st.session_state.get("num_alternatives", 3)

st.caption(f"🔢 Кількість критеріїв: {num_criteria} | Кількість альтернатив: {num_alternatives}")
st.markdown("---")

# Поле для головної мети
st.subheader("🏁 Назва головної мети")
st.session_state.goal_name = st.text_input("Введіть назву мети:", st.session_state.get("goal_name", "ГОЛОВНА МЕТА"))

# Назви критеріїв
st.subheader("🎯 Назви критеріїв")
criteria_names = []
for i in range(num_criteria):
    name = st.text_input(f"Назва критерію {i+1}:", st.session_state.get(f"crit_{i}", f"Критерій {i+1}"))
    criteria_names.append(name)
    st.session_state[f"crit_{i}"] = name

# Назви альтернатив
st.subheader("⚙️ Назви альтернатив")
alternative_names = []
for j in range(num_alternatives):
    name = st.text_input(f"Назва альтернативи {j+1}:", st.session_state.get(f"alt_{j}", f"Альтернатива {j+1}"))
    alternative_names.append(name)
    st.session_state[f"alt_{j}"] = name

# Збереження в session_state
st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

st.success("✅ Назви збережено! Перейдіть на головну сторінку, щоб побачити оновлену діаграму.")
