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

st.graphviz_chart(dot, width=1500, height=800)

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриці попарних порівнянь")
st.markdown("### 🧩 Матриця критеріїв")
st.info("⚠️ Діагональні елементи не можна змінювати — вони завжди рівні 1.")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

prev_matrix = st.session_state.criteria_matrix.copy()
edited_matrix = st.data_editor(
    prev_matrix,
    key="criteria_editor",
    use_container_width=True,
    num_rows="dynamic"
)

# --- Дзеркальне оновлення + фіксація діагоналі ---
for i in range(num_criteria):
    for j in range(num_criteria):
        val = edited_matrix.iloc[i, j]

        # якщо користувач змінює діагональ → повертаємо 1
        if i == j:
            if val != 1:
                edited_matrix.iloc[i, j] = 1.0

        # якщо змінилась комірка → оновлюємо дзеркальну
        elif edited_matrix.iloc[i, j] != prev_matrix.iloc[i, j]:
            if pd.notna(val) and val != 0:
                try:
                    edited_matrix.iloc[j, i] = round(1 / float(val))
                except Exception:
                    edited_matrix.iloc[j, i] = 1.0

# гарантуємо, що діагональ = 1 і всі значення округлені до цілих
np.fill_diagonal(edited_matrix.values, 1.0)
edited_matrix = edited_matrix.astype(float).round(0)

st.session_state.criteria_matrix = edited_matrix

# --- Відображення з підсвіченою діагоналлю ---
def style_diagonal(df: pd.DataFrame):
    n = df.shape[0]
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for i in range(n):
        styles.iloc[i, i] = "background-color: #dddddd; color: #333333; font-weight: 600;"
    return (
        df.style
        .format(precision=0)
        .apply(lambda _: styles, axis=None)
        .set_table_styles(
            [{"selector": "th", "props": "font-weight: 600; text-align: center;"}]
        )
    )

st.dataframe(style_diagonal(st.session_state.criteria_matrix), use_container_width=True)

# ------------------------------------------------
# Матриці альтернатив
# ------------------------------------------------
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

for crit in criteria_names:
    if crit not in st.session_state.alt_matrices or len(st.session_state.alt_matrices[crit]) != num_alternatives:
        st.session_state.alt_matrices[crit] = pd.DataFrame(
            np.ones((num_alternatives, num_alternatives)),
            columns=alternative_names,
            index=alternative_names
        )

    st.markdown(f"### ⚙️ Матриця альтернатив для критерію: {crit}")
    prev_alt = st.session_state.alt_matrices[crit].copy()
    edited_alt = st.data_editor(
        prev_alt,
        key=f"matrix_{crit}",
        use_container_width=True,
        num_rows="dynamic"
    )

    for i in range(num_alternatives):
        for j in range(num_alternatives):
            val = edited_alt.iloc[i, j]
            if i == j:
                if val != 1:
                    edited_alt.iloc[i, j] = 1.0
            elif edited_alt.iloc[i, j] != prev_alt.iloc[i, j]:
                if pd.notna(val) and val != 0:
                    try:
                        edited_alt.iloc[j, i] = round(1 / float(val))
                    except Exception:
                        edited_alt.iloc[j, i] = 1.0

    np.fill_diagonal(edited_alt.values, 1.0)
    edited_alt = edited_alt.astype(float).round(0)
    st.session_state.alt_matrices[crit] = edited_alt

    st.dataframe(style_diagonal(st.session_state.alt_matrices[crit]), use_container_width=True)

st.success("✅ Матриці оновлено. Діагональ фіксована, підсвічена і відображається як 1.")
