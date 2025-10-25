import streamlit as st
import graphviz
import pandas as pd
import numpy as np


st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# --- Вибір кількості критеріїв та альтернатив ---
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3

num_criteria = st.number_input("Кількість критеріїв:", min_value=1, max_value=9, value=st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", min_value=1, max_value=9, value=st.session_state.num_alternatives)

st.session_state.num_criteria = num_criteria
st.session_state.num_alternatives = num_alternatives

# --- Отримання назв або створення стандартних ---
criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(num_criteria)])
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(num_alternatives)])
goal_name = st.session_state.get("goal_name", "ГОЛОВНА МЕТА")

# --- Синхронізація довжин списків ---
if len(criteria_names) < num_criteria:
    for i in range(len(criteria_names), num_criteria):
        criteria_names.append(f"Критерій {i+1}")
elif len(criteria_names) > num_criteria:
    criteria_names = criteria_names[:num_criteria]

if len(alternative_names) < num_alternatives:
    for j in range(len(alternative_names), num_alternatives):
        alternative_names.append(f"Альтернатива {j+1}")
elif len(alternative_names) > num_alternatives:
    alternative_names = alternative_names[:num_alternatives]

st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

# --- Побудова графу ---
dot = graphviz.Digraph()
dot.attr(size="15,8", ratio="fill", rankdir="TB")
dot.node("Goal", goal_name, shape="box", style="filled", color="lightblue")

criteria_nodes = []
for i, crit_name in enumerate(criteria_names):
    node_id = f"C{i+1}"
    dot.node(node_id, crit_name, shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", node_id)
    criteria_nodes.append(node_id)

alt_nodes = []
for j, alt_name in enumerate(alternative_names):
    node_id = f"A{j+1}"
    dot.node(node_id, alt_name, shape="box", style="filled", color="lightyellow")
    alt_nodes.append(node_id)

for c in criteria_nodes:
    for a in alt_nodes:
        dot.edge(c, a)

st.graphviz_chart(dot, width=1500, height=800)

st.info("💡 Щоб змінити назви критеріїв, альтернатив або головної мети — відкрий сторінку **«Назви критеріїв»** у меню ліворуч.")

# ============================================================
# === МАТРИЦІ ПОПАРНИХ ПОРІВНЯНЬ =============================
# ============================================================

st.markdown("---")
st.markdown("## 📊 Матриці попарних порівнянь")

num_criteria = st.session_state.num_criteria
num_alternatives = st.session_state.num_alternatives
criteria_names = st.session_state.criteria_names
alternative_names = st.session_state.alternative_names

# --- Ініціалізація матриці критеріїв ---
if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

st.markdown("### 🧩 Матриця критеріїв")
prev_matrix = st.session_state.criteria_matrix.copy()

# показуємо користувачу
edited_matrix = st.data_editor(
    prev_matrix,
    key="criteria_matrix_editor",
    use_container_width=True,
    num_rows="dynamic"
)

# --- Автоматичне дзеркальне оновлення ---
for i in range(num_criteria):
    for j in range(num_criteria):
        if i == j:
            edited_matrix.iloc[i, j] = 1.0  # фіксуємо діагональ
        elif edited_matrix.iloc[i, j] != prev_matrix.iloc[i, j]:
            val = edited_matrix.iloc[i, j]
            if val == 0:
                val = 1e-9
            try:
                edited_matrix.iloc[j, i] = round(1 / float(val), 4)
            except Exception:
                pass

st.session_state.criteria_matrix = edited_matrix

# --- Матриці альтернатив ---
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

        # фіксуємо діагональ і дзеркальні значення
        for i in range(num_alternatives):
            for j in range(num_alternatives):
                if i == j:
                    edited_alt.iloc[i, j] = 1.0
                elif edited_alt.iloc[i, j] != prev_alt.iloc[i, j]:
                    val = edited_alt.iloc[i, j]
                    if val == 0:
                        val = 1e-9
                    try:
                        edited_alt.iloc[j, i] = round(1 / float(val), 4)
                    except Exception:
                        pass

        st.session_state.alt_matrices[crit] = edited_alt

st.success("✅ Матриці оновлено. Діагональ зафіксовано, симетрія підтримується автоматично.")
