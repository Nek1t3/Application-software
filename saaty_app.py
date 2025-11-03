import streamlit as st
import graphviz
import pandas as pd
import numpy as np

# ------------------------------------------------
# Налаштування
# ------------------------------------------------
st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# ------------------------------------------------
# Кількість критеріїв і альтернатив
# ------------------------------------------------
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3

num_criteria = st.number_input("Кількість критеріїв:", 1, 9, st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", 1, 9, st.session_state.num_alternatives)

st.session_state.num_criteria = num_criteria
st.session_state.num_alternatives = num_alternatives

criteria_names = [f"Критерій {i+1}" for i in range(num_criteria)]
alternative_names = [f"Альтернатива {j+1}" for j in range(num_alternatives)]

# ------------------------------------------------
# Побудова графу
# ------------------------------------------------
dot = graphviz.Digraph()
dot.attr(size="15,8", ratio="fill", rankdir="TB")
dot.node("Goal", "ГОЛОВНА МЕТА", shape="box", style="filled", color="lightblue")

for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", crit)
    for alt in alternative_names:
        dot.node(alt, alt, shape="box", style="filled", color="lightyellow")
        dot.edge(crit, alt)

st.graphviz_chart(dot, width=1500, height=700)

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

prev = st.session_state.criteria_matrix.copy()
edited = st.data_editor(
    prev.style.format("{:.2f}"),  # 🔹 дві цифри після коми у відображенні
    key="criteria_editor",
    use_container_width=True
)

for i in range(num_criteria):
    for j in range(num_criteria):
        if i == j:
            edited.iloc[i, j] = 1.00
        elif edited.iloc[i, j] != prev.iloc[i, j]:
            val = edited.iloc[i, j]
            if pd.notna(val) and val != 0:
                try:
                    edited.iloc[j, i] = round(1 / float(val), 2)  # 🔹 тепер до двох знаків
                except Exception:
                    edited.iloc[j, i] = 1.00

np.fill_diagonal(edited.values, 1.00)
edited = edited.astype(float)
st.session_state.criteria_matrix = edited.round(2)

st.caption("🔒 Діагональ фіксована = 1.00, усі значення округлені до двох десяткових.")

# ------------------------------------------------
# Матриці альтернатив
# ------------------------------------------------
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

tabs = st.tabs(criteria_names)

for tab, crit in zip(tabs, criteria_names):
    with tab:
        st.markdown(f"### ⚙️ Матриця альтернатив для критерію **{crit}**")

        if crit not in st.session_state.alt_matrices or len(st.session_state.alt_matrices[crit]) != num_alternatives:
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names,
                index=alternative_names
            )

        prev_alt = st.session_state.alt_matrices[crit].copy()
        edited_alt = st.data_editor(
            prev_alt.style.format("{:.2f}"),
            key=f"matrix_{crit}",
            use_container_width=True
        )

        for i in range(num_alternatives):
            for j in range(num_alternatives):
                if i == j:
                    edited_alt.iloc[i, j] = 1.00
                elif edited_alt.iloc[i, j] != prev_alt.iloc[i, j]:
                    val = edited_alt.iloc[i, j]
                    if pd.notna(val) and val != 0:
                        try:
                            edited_alt.iloc[j, i] = round(1 / float(val), 2)
                        except Exception:
                            edited_alt.iloc[j, i] = 1.00

        np.fill_diagonal(edited_alt.values, 1.00)
        st.session_state.alt_matrices[crit] = edited_alt.round(2)

# ------------------------------------------------
# РОЗРАХУНОК МЕТОДУ СААТІ
# ------------------------------------------------
st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

def calc_weights(matrix):
    """Нормалізуємо матрицю і повертаємо ваги"""
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

# Ваги критеріїв
criteria_weights = calc_weights(st.session_state.criteria_matrix)

# Локальні ваги альтернатив
alt_weights = {}
for crit in criteria_names:
    alt_weights[crit] = calc_weights(st.session_state.alt_matrices[crit])

# Фінальні глобальні ваги
global_priorities = pd.DataFrame(index=alternative_names)
for crit, w in zip(criteria_names, criteria_weights):
    global_priorities[crit] = alt_weights[crit] * w

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
global_priorities = global_priorities.sort_values("Глоб. пріор.", ascending=False)

# Форматування кольорів
def color_rank(row):
    if row.name == global_priorities.index[0]:
        return ["background-color: #b6fcb6"] * len(row)
    elif row.name == global_priorities.index[1]:
        return ["background-color: #fce8a6"] * len(row)
    elif row.name == global_priorities.index[2]:
        return ["background-color: #fcb6b6"] * len(row)
    else:
        return [""] * len(row)

st.dataframe(
    global_priorities.style.format("{:.3f}").apply(color_rank, axis=1),
    use_container_width=True,
)

st.success("✅ Розрахунок завершено! Усі значення відображаються з двома десятковими знаками (6.00, 9.00 і т.д.).")
