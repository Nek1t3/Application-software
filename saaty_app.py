import streamlit as st
import graphviz

st.title("Метод Сааті — Ієрархія задачі")

num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=10, value=3)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=10, value=3)

dot = graphviz.Digraph()
dot.attr(size="10,24")  # збільшуємо вертикальний розмір

dot.node("Goal", "GOAL / TEST", shape="box", style="filled", color="lightblue")

criteria_nodes = []
for i in range(num_criteria):
    name = f"C{i+1}"
    dot.node(name, f"Criterion {i+1}", shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", name)
    criteria_nodes.append(name)

alt_nodes = []
for j in range(num_alternatives):
    name = f"A{j+1}"
    dot.node(name, f"Alternative {j+1}", shape="box", style="filled", color="lightyellow")
    alt_nodes.append(name)

for c in criteria_nodes:
    for a in alt_nodes:
        dot.edge(c, a)

# Збільшений розмір відображення
st.graphviz_chart(dot, width=1000, height=2400)
