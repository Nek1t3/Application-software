import streamlit as st
import graphviz

st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# Кількість критеріїв та альтернатив
num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=9, value=3)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=9, value=3)

# Отримання назв із session_state (якщо є)
criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(num_criteria)])
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(num_alternatives)])

# Побудова графу
dot = graphviz.Digraph()
dot.attr(size="10,12", ratio="fill", rankdir="TB")

# Рівень 1 — Мета
dot.node("Goal", "ГОЛОВНА МЕТА", shape="box", style="filled", color="lightblue")

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
st.graphviz_chart(dot, width=1000, height=1200)

st.info("💡 Щоб змінити назви критеріїв та альтернатив, відкрийте сторінку **«Назви критеріїв»** у меню ліворуч.")
