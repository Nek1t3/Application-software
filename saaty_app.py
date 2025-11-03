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
# Матриця критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

prev = st.session_state.criteria_matrix.copy()
edited = st.data_editor(prev.style.format("{:.2f}"), key="criteria_editor", use_container_width=True)

# --- дзеркальне оновлення + округлення до цілого ---
for i in range(num_criteria):
    for j in range(num_criteria):
        if i == j:
            edited.iloc[i, j] = 1.00
        elif edited.iloc[i, j] != prev.iloc[i, j]:
            val = edited.iloc[i, j]
            if pd.notna(val) and val != 0:
                try:
                    inv = 1 / float(val)
                    edited.iloc[j, i] = float(round(inv))  # 🔹 округлюємо до найближчого цілого
                except Exception:
                    edited.iloc[j, i] = 1.00

np.fill_diagonal(edited.values, 1.00)
edited = edited.astype(float)
st.session_state.criteria_matrix = edited.round(2)

st.caption("🔒 Діагональ фіксована = 1.00, інверсія округлюється до найближчого цілого (1–9).")

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
        edited_alt = st.data_editor(prev_alt.style.format("{:.2f}"), key=f"matrix_{crit}", use_container_width=True)

        for i in range(num_alternatives):
            for j in range(num_alternatives):
                if i == j:
                    edited_alt.iloc[i, j] = 1.00
                elif edited_alt.iloc[i, j] != prev_alt.iloc[i, j]:
                    val = edited_alt.iloc[i, j]
                    if pd.notna(val) and val != 0:
                        try:
                            inv = 1 / float(val)
                            edited_alt.iloc[j, i] = float(round(inv))  # 🔹 тільки цілі
                        except Exception:
                            edited_alt.iloc[j, i] = 1.00

        np.fill_diagonal(edited_alt.values, 1.00)
        st.session_state.alt_matrices[crit] = edited_alt.round(2)

# ------------------------------------------------
# Функція для розрахунку
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

# ------------------------------------------------
# Розрахунок глобальних пріоритетів
# ------------------------------------------------
st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

criteria_weights = calc_weights(st.session_state.criteria_matrix)
alt_weights = {crit: calc_weights(st.session_state.alt_matrices[crit]) for crit in criteria_names}

global_priorities = pd.DataFrame(index=alternative_names)
for crit, w in zip(criteria_names, criteria_weights):
    global_priorities[crit] = alt_weights[crit] * w

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
global_priorities = global_priorities.sort_values("Глоб. пріор.", ascending=False)

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

st.success("✅ Оновлено: усі зворотні значення тепер округлюються до цілого (наприклад, 7.14 → 7.00).")
