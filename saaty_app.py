import streamlit as st
import graphviz

st.title("Метод Сааті — Ієрархія задачі")

# Кількість критеріїв та альтернатив
num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=9, value=3)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=9, value=3)

st.subheader("Назви критеріїв")
criteria_names = []
for i in range(num_criteria):
    name = st.text_input(f"Назва критерію {i+1}:", f"Критерій {i+1}")
    criteria_names.append(name)

st.subheader("Назви альтернатив")
alternative_names = []
for j in range(num_alternatives):
    name = st.text_input(f"Назва альтернативи {j+1}:", f"Альтернатива {j+1}")
    alternative_names.append(name)

# Побудова графу
dot = graphviz.Digraph()
dot.attr(size="10,24", ratio="fill", rankdir="TB")

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
st.graphviz_chart(dot, width=1000, height=2400)
