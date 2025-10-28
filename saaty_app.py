import streamlit as st
import graphviz
import pandas as pd
import numpy as np

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

# синхронізація довжин
criteria_names = (criteria_names + [f"Критерій {i+1}" for i in range(len(criteria_names), num_criteria)])[:num_criteria]
alternative_names = (alternative_names + [f"Альтернатива {j+1}" for j in range(len(alternative_names), num_alternatives)])[:num_alternatives]

st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

# ------------------------------------------------
# Граф
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
# Хелпер для стилю перегляду (сіра діагональ)
# ------------------------------------------------
def style_diagonal(df: pd.DataFrame):
    n = df.shape[0]
    # побудуємо матрицю стилів (n*n)
    styles = np.array([["" for _ in range(n)] for __ in range(n)])
    for i in range(n):
        styles[i, i] = "background-color: #eeeeee; color: #666666; font-weight: 600;"
    return df.style.set_precision(3).set_table_styles([
        {"selector": "th", "props": "font-weight: 600;"},
    ]).apply(lambda _: styles, axis=None)

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриці попарних порівнянь")
st.markdown("### 🧩 Матриця критеріїв")

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

# --- оптимізоване дзеркальне оновлення + фіксація діагоналі ---
diff = (edited_matrix != prev_matrix)
if diff.any().any():
    changed = np.where(diff)
    for i, j in zip(changed[0], changed[1]):
        if i == j:
            # діагональ завжди = 1
            edited_matrix.iloc[i, j] = 1.0
        else:
            val = edited_matrix.iloc[i, j]
            if pd.notna(val) and val != 0:
                try:
                    edited_matrix.iloc[j, i] = round(1 / float(val), 3)
                except Exception:
                    edited_matrix.iloc[j, i] = 1.0

# гарантуємо 1 на діагоналі
np.fill_diagonal(edited_matrix.values, 1.0)
# округлення для охайного вигляду
edited_matrix = edited_matrix.astype(float).round(3)

st.session_state.criteria_matrix = edited_matrix
st.caption("🔒 Діагональ логічно зафіксована = 1.0. Зміни у будь-якій клітинці автоматично оновлюють дзеркальну (aᵢⱼ ↔ 1/aⱼᵢ).")

with st.expander("👁️ Перегляд матриці критеріїв із підсвіченою діагоналлю"):
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

    with st.expander(f"⚙️ Матриця альтернатив для критерію: {crit}"):
        prev_alt = st.session_state.alt_matrices[crit].copy()
        edited_alt = st.data_editor(
            prev_alt,
            key=f"matrix_{crit}",
            use_container_width=True,
            num_rows="dynamic"
        )

        diff_alt = (edited_alt != prev_alt)
        if diff_alt.any().any():
            changed = np.where(diff_alt)
            for i, j in zip(changed[0], changed[1]):
                if i == j:
                    edited_alt.iloc[i, j] = 1.0
                else:
                    val = edited_alt.iloc[i, j]
                    if pd.notna(val) and val != 0:
                        try:
                            edited_alt.iloc[j, i] = round(1 / float(val), 3)
                        except Exception:
                            edited_alt.iloc[j, i] = 1.0

        np.fill_diagonal(edited_alt.values, 1.0)
        edited_alt = edited_alt.astype(float).round(3)

        st.session_state.alt_matrices[crit] = edited_alt
        st.caption("🔒 Діагональ логічно зафіксована = 1.0.")

        with st.expander("👁️ Перегляд матриці альтернатив із підсвіченою діагоналлю"):
            st.dataframe(style_diagonal(st.session_state.alt_matrices[crit]), use_container_width=True)

st.success("✅ Матриці оновлено. Симетрія працює, діагональ фіксується та виділяється в перегляді.")
