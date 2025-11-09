import streamlit as st
import pandas as pd
import numpy as np
import graphviz

# ------------------------------------------------
# Налаштування
# ------------------------------------------------
st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# ------------------------------------------------
# Початкові параметри
# ------------------------------------------------
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3

num_criteria = st.number_input("Кількість критеріїв:", 1, 9, value=st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", 1, 9, value=st.session_state.num_alternatives)

criteria_names = [f"Критерій {i+1}" for i in range(int(num_criteria))]
alternative_names = [f"Альтернатива {j+1}" for j in range(int(num_alternatives))]

if num_criteria != st.session_state.num_criteria:
    st.session_state.num_criteria = int(num_criteria)
    st.rerun()  # ✅ новий стабільний метод

if num_alternatives != st.session_state.num_alternatives:
    st.session_state.num_alternatives = int(num_alternatives)
    st.rerun()



# ------------------------------------------------
# 🎯 Ієрархічна діаграма (стрілки вгору)
# ------------------------------------------------
st.markdown("## 🎨 Ієрархія задачі (візуалізація)")

dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")  # BT — напрямок стрілок знизу вгору

# Головна мета
dot.node("goal", "ГОЛОВНА МЕТА", shape="box", style="filled", color="#a1c9f1")

# Альтернативи (внизу)
for alt in alternative_names:
    dot.node(alt, alt, shape="ellipse", style="filled", color="#fce8a6")

# Критерії (посередині)
for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="#b6fcb6")

# Стрілки від альтернатив до критеріїв
for crit in criteria_names:
    for alt in alternative_names:
        dot.edge(alt, crit)

# Стрілки від критеріїв до головної мети
for crit in criteria_names:
    dot.edge(crit, "goal")

st.graphviz_chart(dot, use_container_width=True)

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

criteria_df = st.data_editor(
    st.session_state.criteria_matrix,
    key="criteria_editor",
    use_container_width=True,
)

# ------------------------------------------------
# Кнопка "Зберегти зміни"
# ------------------------------------------------
save_clicked = st.button("💾 Зберегти зміни в матриці критеріїв")

if save_clicked:
    edited_df = pd.DataFrame(criteria_df, columns=criteria_names, index=criteria_names).astype(float)
    prev = st.session_state.criteria_matrix.copy()

    for i in range(num_criteria):
        for j in range(num_criteria):
            if i == j:
                edited_df.iloc[i, j] = 1.000
            elif edited_df.iloc[i, j] != prev.iloc[i, j]:
                val = float(edited_df.iloc[i, j])
                if pd.notna(val) and val != 0:
                    val = round(val, 3)
                    inv = round(1 / val, 3)
                    if abs(val - round(val)) < 0.015:
                        val = float(f"{round(val):.3f}")
                    if abs(inv - round(inv)) < 0.015:
                        inv = float(f"{round(inv):.3f}")
                    edited_df.iloc[i, j] = val
                    edited_df.iloc[j, i] = inv

    np.fill_diagonal(edited_df.values, 1.000)
    st.session_state.criteria_matrix = edited_df
    st.success("✅ Матриця критеріїв оновлена! Симетричні значення застосовані.")
    st.dataframe(edited_df.style.format("{:.3f}"), use_container_width=True)

st.caption("🔒 Діагональ = 1.000. Натисни «💾 Зберегти зміни», щоб оновити симетрію.")

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

        alt_df = st.data_editor(
            st.session_state.alt_matrices[crit],
            key=f"matrix_{crit}",
            use_container_width=True,
        )

        save_alt = st.button(f"💾 Зберегти зміни ({crit})")

        if save_alt:
            edited_alt_df = pd.DataFrame(alt_df, columns=alternative_names, index=alternative_names).astype(float)
            prev_alt = st.session_state.alt_matrices[crit].copy()

            for i in range(num_alternatives):
                for j in range(num_alternatives):
                    if i == j:
                        edited_alt_df.iloc[i, j] = 1.000
                    elif edited_alt_df.iloc[i, j] != prev_alt.iloc[i, j]:
                        val = float(edited_alt_df.iloc[i, j])
                        if pd.notna(val) and val != 0:
                            val = round(val, 3)
                            inv = round(1 / val, 3)
                            if abs(val - round(val)) < 0.015:
                                val = float(f"{round(val):.3f}")
                            if abs(inv - round(inv)) < 0.015:
                                inv = float(f"{round(inv):.3f}")
                            edited_alt_df.iloc[i, j] = val
                            edited_alt_df.iloc[j, i] = inv

            np.fill_diagonal(edited_alt_df.values, 1.000)
            st.session_state.alt_matrices[crit] = edited_alt_df
            st.success(f"✅ Матриця для {crit} оновлена! Симетричні значення застосовано.")
            st.dataframe(edited_alt_df.style.format("{:.3f}"), use_container_width=True)

# ------------------------------------------------
# Розрахунок глобальних пріоритетів
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

criteria_weights = calc_weights(st.session_state.criteria_matrix)
alt_weights = {crit: calc_weights(st.session_state.alt_matrices[crit]) for crit in criteria_names}

global_priorities = pd.DataFrame(index=alternative_names)
for crit, w in zip(criteria_names, criteria_weights):
    global_priorities[crit] = alt_weights[crit] * w

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
global_priorities = global_priorities.sort_values("Глоб. пріор.", ascending=False)

# ------------------------------------------------
# Відображення результатів без кольорів
# ------------------------------------------------
st.dataframe(
    global_priorities.style.format("{:.3f}"),
    use_container_width=True,
)

st.success("✅ Розрахунок завершено! Таблиця без кольорового підсвічування.")
