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

# Редагування користувачем
edited = st.data_editor(
    st.session_state.criteria_matrix.style.format("{:.3f}"),
    key="criteria_editor",
    use_container_width=True
)

# ------------------------------------------------
# Кнопка "Зберегти зміни"
# ------------------------------------------------
if st.button("💾 Зберегти зміни в матриці критеріїв"):
    prev = st.session_state.criteria_matrix.copy()

    for i in range(num_criteria):
        for j in range(num_criteria):
            if i == j:
                edited.iloc[i, j] = 1.000
            elif edited.iloc[i, j] != prev.iloc[i, j]:
                val = float(edited.iloc[i, j])
                if pd.notna(val) and val != 0:
                    inv = round(1 / val, 3)

                    # Коригуємо похибку 9.009 → 9.000
                    if abs(inv - round(inv)) < 0.01:
                        inv = float(f"{round(inv):.3f}")
                    if abs(val - round(val)) < 0.01:
                        val = float(f"{round(val):.3f}")

                    edited.iloc[i, j] = val
                    edited.iloc[j, i] = inv

    np.fill_diagonal(edited.values, 1.000)
    edited = edited.astype(float)
    st.session_state.criteria_matrix = edited
    st.success("✅ Матриця оновлена! Симетричні значення збережено (n ↔ 1/n).")

st.caption("🔒 Діагональ = 1.000. Щоб оновити симетрію — натисніть **«💾 Зберегти зміни»**.")

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

        edited_alt = st.data_editor(
            st.session_state.alt_matrices[crit].style.format("{:.3f}"),
            key=f"matrix_{crit}",
            use_container_width=True
        )

        if st.button(f"💾 Зберегти зміни ({crit})"):
            prev_alt = st.session_state.alt_matrices[crit].copy()

            for i in range(num_alternatives):
                for j in range(num_alternatives):
                    if i == j:
                        edited_alt.iloc[i, j] = 1.000
                    elif edited_alt.iloc[i, j] != prev_alt.iloc[i, j]:
                        val = float(edited_alt.iloc[i, j])
                        if pd.notna(val) and val != 0:
                            inv = round(1 / val, 3)

                            # Коригуємо похибку 9.009 → 9.000
                            if abs(inv - round(inv)) < 0.01:
                                inv = float(f"{round(inv):.3f}")
                            if abs(val - round(val)) < 0.01:
                                val = float(f"{round(val):.3f}")

                            edited_alt.iloc[i, j] = val
                            edited_alt.iloc[j, i] = inv

            np.fill_diagonal(edited_alt.values, 1.000)
            edited_alt = edited_alt.astype(float)
            st.session_state.alt_matrices[crit] = edited_alt
            st.success(f"✅ Матриця для критерію {crit} оновлена!")

# ------------------------------------------------
# Розрахунок
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

st.success("✅ Тепер симетричні значення оновлюються тільки після натискання кнопки «Зберегти».")
