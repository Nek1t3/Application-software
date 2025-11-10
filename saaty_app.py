import streamlit as st
import pandas as pd
import numpy as np
import graphviz
import json
from io import BytesIO

# ------------------------------------------------
# 🔧 Налаштування сторінки
# ------------------------------------------------
st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# ------------------------------------------------
# 📦 Ініціалізація session_state
# ------------------------------------------------
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3
if "criteria_matrix" not in st.session_state:
    st.session_state.criteria_matrix = pd.DataFrame()
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

num_criteria = st.number_input("Кількість критеріїв:", 1, 9, value=st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", 1, 9, value=st.session_state.num_alternatives)

if num_criteria != st.session_state.num_criteria:
    st.session_state.num_criteria = int(num_criteria)
    st.rerun()
if num_alternatives != st.session_state.num_alternatives:
    st.session_state.num_alternatives = int(num_alternatives)
    st.rerun()

# ------------------------------------------------
# 🏷️ Назви
# ------------------------------------------------
criteria_names = [f"Критерій {i+1}" for i in range(int(num_criteria))]
alternative_names = [f"Альтернатива {j+1}" for j in range(int(num_alternatives))]
goal_name = st.session_state.get("goal_name", "ГОЛОВНА МЕТА")

# ------------------------------------------------
# 💾 Бокова вкладка — Збереження / Імпорт
# ------------------------------------------------
st.sidebar.header("💾 Збереження / Імпорт")
mode = st.sidebar.radio("Оберіть режим:", ["Зберегти матриці", "Імпортувати матриці"])

if mode == "Зберегти матриці":
    filename = st.sidebar.text_input("Ім'я файлу (без .json):", "ahp_matrices")
    if st.sidebar.button("💾 Зберегти як JSON"):
        export_data = {
            "goal_name": goal_name,
            "criteria_names": criteria_names,
            "alternative_names": alternative_names,
            "num_criteria": st.session_state.num_criteria,
            "num_alternatives": st.session_state.num_alternatives,
            "criteria_matrix": st.session_state.criteria_matrix.to_dict(),
            "alt_matrices": {k: v.to_dict() for k, v in st.session_state.alt_matrices.items()},
        }
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.sidebar.download_button(
            label="⬇️ Завантажити JSON-файл",
            data=BytesIO(json_str.encode("utf-8")),
            file_name=f"{filename}.json",
            mime="application/json",
        )

elif mode == "Імпортувати матриці":
    uploaded_file = st.sidebar.file_uploader("📥 Завантажити JSON", type=["json"])
    if uploaded_file:
        imported = json.load(uploaded_file)
        st.session_state.goal_name = imported.get("goal_name", "ГОЛОВНА МЕТА")
        st.session_state.criteria_matrix = pd.DataFrame(imported["criteria_matrix"])
        st.session_state.alt_matrices = {k: pd.DataFrame(v) for k, v in imported.get("alt_matrices", {}).items()}
        st.session_state.num_criteria = imported["num_criteria"]
        st.session_state.num_alternatives = imported["num_alternatives"]
        st.sidebar.success("✅ Імпортовано, оновлення...")
        st.rerun()

# ------------------------------------------------
# 🎨 Ієрархічна діаграма
# ------------------------------------------------
st.markdown("## 🎯 Ієрархія задачі (візуалізація)")
dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")
dot.node("goal", goal_name, shape="box", style="filled", color="#a1c9f1")

for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="#b6fcb6")
    dot.edge(crit, "goal")

for alt in alternative_names:
    dot.node(alt, alt, shape="ellipse", style="filled", color="#fce8a6")
    for crit in criteria_names:
        dot.edge(alt, crit)

st.graphviz_chart(dot, use_container_width=True)

# ------------------------------------------------
# 🧮 Функції
# ------------------------------------------------
RI_table = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24,
             7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}

def enforce_symmetry(df):
    edited = df.copy()
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):
            val = edited.iloc[i, j]
            if val != 0:
                edited.iloc[j, i] = round(1 / val, 3)
    np.fill_diagonal(edited.values, 1.0)
    return edited

def calc_consistency(matrix):
    n = len(matrix)
    eigvals, _ = np.linalg.eig(matrix)
    lambda_max = np.max(np.real(eigvals))
    CI = (lambda_max - n) / (n - 1)
    RI = RI_table.get(n, 1.49)
    CR = CI / RI if RI != 0 else 0
    return lambda_max, CI, RI, CR

def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    return norm.mean(axis=1)

# ------------------------------------------------
# 📊 Матриця критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if st.session_state.criteria_matrix.empty or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)), columns=criteria_names, index=criteria_names
    )
else:
    st.session_state.criteria_matrix = st.session_state.criteria_matrix.reindex(
        index=criteria_names, columns=criteria_names, fill_value=1
    )

criteria_df = st.data_editor(st.session_state.criteria_matrix, key="criteria_edit", use_container_width=True)

# кнопка збереження
if st.button("💾 Зберегти зміни в матриці критеріїв"):
    edited_df = pd.DataFrame(criteria_df).astype(float)
    edited_df = enforce_symmetry(edited_df)
    st.session_state.criteria_matrix = edited_df
    st.success("✅ Симетричність застосовано.")
    # без rerun — миттєве оновлення
    criteria_df = edited_df

lambda_max, CI, RI, CR = calc_consistency(st.session_state.criteria_matrix)
st.markdown(f"**λₘₐₓ = {lambda_max:.3f}**, **ІУ = {CI:.3f}**, **ВВУ = {RI:.3f}**, **ВУ = {CR*100:.1f}%**", unsafe_allow_html=True)
if CR > 0.2:
    st.error("❌ ВУ > 20% — матриця неузгоджена!")
else:
    st.success("✅ Узгодженість прийнятна.")

# ------------------------------------------------
# ⚙️ Матриці альтернатив
# ------------------------------------------------
tabs = st.tabs(criteria_names)
for crit, tab in zip(criteria_names, tabs):
    with tab:
        st.markdown(f"### ⚙️ Матриця альтернатив для **{crit}**")

        if crit not in st.session_state.alt_matrices or len(st.session_state.alt_matrices[crit]) != num_alternatives:
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names, index=alternative_names
            )
        alt_df = st.data_editor(st.session_state.alt_matrices[crit], key=f"alt_{crit}", use_container_width=True)

        if st.button(f"💾 Зберегти ({crit})"):
            df = pd.DataFrame(alt_df).astype(float)
            df = enforce_symmetry(df)
            st.session_state.alt_matrices[crit] = df
            st.success(f"✅ Матриця {crit} оновлена.")

        lam, ci, ri, cr = calc_consistency(st.session_state.alt_matrices[crit])
        st.markdown(f"**λₘₐₓ = {lam:.3f}**, **ІУ = {ci:.3f}**, **ВВУ = {ri:.3f}**, **ВУ = {cr*100:.1f}%**", unsafe_allow_html=True)
        if cr > 0.2:
            st.error("❌ Неузгоджена матриця!")
        else:
            st.success("✅ Узгоджена матриця!")

# ------------------------------------------------
# 🧮 Глобальні пріоритети
# ------------------------------------------------
st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

criteria_weights = calc_weights(st.session_state.criteria_matrix)
alt_weights = {crit: calc_weights(st.session_state.alt_matrices[crit]) for crit in criteria_names}

global_priorities = pd.DataFrame(index=alternative_names)
for crit, w in zip(criteria_names, criteria_weights):
    global_priorities[crit] = alt_weights[crit] * w

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
st.dataframe(global_priorities.style.format("{:.3f}"), use_container_width=True)
st.success("✅ Розрахунок завершено.")
