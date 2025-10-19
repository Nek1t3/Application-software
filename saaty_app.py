import streamlit as st
import graphviz

st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# --- Вибір кількості критеріїв та альтернатив ---
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3

num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=9, value=st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=9, value=st.session_state.num_alternatives)

# Оновлюємо session_state, якщо змінились значення
st.session_state.num_criteria = num_criteria
st.session_state.num_alternatives = num_alternatives

# --- Отримуємо назви або створюємо стандартні ---
criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(num_criteria)])
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(num_alternatives)])
goal_name = st.session_state.get("goal_name", "ГОЛОВНА МЕТА")

# --- 🔄 Синхронізація довжини списків назв ---
# Якщо критеріїв стало більше — додаємо нові назви
if len(criteria_names) < num_criteria:
    for i in range(len(criteria_names), num_criteria):
        criteria_names.append(f"Критерій {i+1}")
# Якщо стало менше — обрізаємо список
elif len(criteria_names) > num_criteria:
    criteria_names = criteria_names[:num_criteria]

# Те саме для альтернатив
if len(alternative_names) < num_alternatives:
    for j in range(len(alternative_names), num_alternatives):
        alternative_names.append(f"Альтернатива {j+1}")
elif len(alternative_names) > num_alternatives:
    alternative_names = alternative_names[:num_alternatives]

# Оновлюємо у session_state
st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

# --- Побудова графу ---
dot = graphviz.Digraph()
dot.attr(size="15,8", ratio="fill", rankdir="TB")

# Рівень 1 — Мета
dot.node("Goal", goal_name, shape="box", style="filled", color="lightblue")

# Рівень 2 — Критерії
criteria_nodes = []
for i, crit_name in enumerate(criteria_names):
    node_id = f"C{i+1}"
    dot.node(node_id, crit_name, shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", node_id)
    criteria_nodes.append(node_id)

# Рівень 3 — Альтернативи
alt_nodes = []
for j, alt_name in enumerate(alternative_names):
    node_id = f"A{j+1}"
    dot.node(node_id, alt_name, shape="box", style="filled", color="lightyellow")
    alt_nodes.append(node_id)

# Зв’язки критеріїв з альтернативами
for c in criteria_nodes:
    for a in alt_nodes:
        dot.edge(c, a)

# Відображення
st.graphviz_chart(dot, width=1500, height=800)

st.info("💡 Щоб змінити назви критеріїв, альтернатив або головної мети — відкрий сторінку **«Назви критеріїв»** у меню ліворуч.")
