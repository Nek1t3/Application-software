import streamlit as st
import graphviz
import pandas as pd
import numpy as np

# ------------------------------------------------
# Налаштування сторінки
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

criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(num_criteria)])
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(num_alternatives)])

criteria_names = (criteria_names + [f"Критерій {i+1}" for i in range(len(criteria_names), num_criteria)])[:num_criteria]
alternative_names = (alternative_names + [f"Альтернатива {j+1}" for j in range(len(alternative_names), num_alternatives)])[:num_alternatives]

st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

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
# Функція для стилізації діагоналі
# ------------------------------------------------
def style_diagonal(df: pd.DataFrame):
    n = df.shape[0]
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for i in range(n):
        styles.iloc[i, i] = "background-color: #dddddd; color: #333333; font-weight: 600;"
    return (
        df.style
        .format(precision=0)
        .apply(lambda _: styles, axis=None)
        .set_table_styles([{"selector": "th", "props": "font-weight: 600; text-align: center;"}])
    )

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")
st.info("⚠️ Діагональ не можна змінювати — вона завжди дорівнює 1 (сірі клітинки).")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

matrix = st.session_state.criteria_matrix.copy()

# редагування значень у таблиці через Streamlit input-поля
for i in range(num_criteria):
    cols = st.columns(num_criteria)
    for j in range(num_criteria):
        if i == j:
            cols[j].markdown(f"<div style='background-color:#dddddd;padding:8px;text-align:center;'>1</div>", unsafe_allow_html=True)
            matrix.iloc[i, j] = 1.0
        else:
            val = cols[j].number_input(
                f"{criteria_names[i]} / {criteria_names[j]}",
                value=float(matrix.iloc[i, j]),
                step=1.0,
                key=f"{i}_{j}",
                format="%.0f"
            )
            # якщо змінено — дзеркально оновлюємо
            if val != matrix.iloc[i, j]:
                try:
                    matrix.iloc[i, j] = val
                    matrix.iloc[j, i] = round(1 / val)
                except ZeroDivisionError:
                    matrix.iloc[i, j] = 1.0
                    matrix.iloc[j, i] = 1.0

# оновлення стану
np.fill_diagonal(matrix.values, 1.0)
matrix = matrix.astype(float).round(0)
st.session_state.criteria_matrix = matrix

# відображення з підсвіченою діагоналлю
st.dataframe(style_diagonal(matrix), use_container_width=True)

# ------------------------------------------------
# Матриці альтернатив (вкладки)
# ------------------------------------------------
st.markdown("---")
st.markdown("## 🧮 Матриці попарних порівнянь альтернатив")

if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

tabs = st.tabs([f"{crit}" for crit in criteria_names])

for tab, crit in zip(tabs, criteria_names):
    with tab:
        st.markdown(f"### ⚙️ Матриця альтернатив для критерію: **{crit}**")

        if crit not in st.session_state.alt_matrices or len(st.session_state.alt_matrices[crit]) != num_alternatives:
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names,
                index=alternative_names
            )

        alt_matrix = st.session_state.alt_matrices[crit].copy()

        for i in range(num_alternatives):
            cols = st.columns(num_alternatives)
            for j in range(num_alternatives):
                if i == j:
                    cols[j].markdown(f"<div style='background-color:#dddddd;padding:8px;text-align:center;'>1</div>", unsafe_allow_html=True)
                    alt_matrix.iloc[i, j] = 1.0
                else:
                    val = cols[j].number_input(
                        f"{alternative_names[i]} / {alternative_names[j]}",
                        value=float(alt_matrix.iloc[i, j]),
                        step=1.0,
                        key=f"{crit}_{i}_{j}",
                        format="%.0f"
                    )
                    if val != alt_matrix.iloc[i, j]:
                        try:
                            alt_matrix.iloc[i, j] = val
                            alt_matrix.iloc[j, i] = round(1 / val)
                        except ZeroDivisionError:
                            alt_matrix.iloc[i, j] = 1.0
                            alt_matrix.iloc[j, i] = 1.0

        np.fill_diagonal(alt_matrix.values, 1.0)
        alt_matrix = alt_matrix.astype(float).round(0)
        st.session_state.alt_matrices[crit] = alt_matrix

        st.dataframe(style_diagonal(alt_matrix), use_container_width=True)

st.success("✅ Усі матриці оновлено. Діагоналі зафіксовані = 1, симетрія підтримується.")
