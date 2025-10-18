import streamlit as st
import graphviz

st.title("Метод Сааті — Ієрархія задачі")

# Введення кількості критеріїв і альтернатив
num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=10, value=3)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=10, value=3)

# Створення графа
dot = graphviz.Digraph()

# Рівень 1 — Мета
dot.node("Goal", "GOAL / TEST", shape="box", style="filled", color="lightblue")

# Рівень 2 — Критерії
criteria_nodes = []
for i in range(num_criteria):
    name = f"C{i+1}"
    dot.node(name, f"Criterion {i+1}", shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", name)
    criteria_nodes.append(name)

# Рівень 3 — Альтернативи
alt_nodes = []
for j in range(num_alternatives):
    name = f"A{j+1}"
    dot.node(name, f"Alternative {j+1}", shape="box", style="filled", color="lightyellow")
    alt_nodes.append(name)

# Зв'язки критеріїв з альтернативами
for c in criteria_nodes:
    for a in alt_nodes:
        dot.edge(c, a)

# Відображення діаграми
st.graphviz_chart(dot)

# Додаткова кнопка
if st.button("Обчислити"):
    st.success("Тут пізніше буде розрахунок вагових коефіцієнтів AHP.")
