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

num_criteria = st.number_input("Кількість критеріїв:", 1, 9, value=st.session_state.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", 1, 9, value=st.session_state.num_alternatives)

if num_criteria != st.session_state.num_criteria:
    st.session_state.num_criteria = int(num_criteria)
    st.rerun()
if num_alternatives != st.session_state.num_alternatives:
    st.session_state.num_alternatives = int(num_alternatives)
    st.rerun()

# ------------------------------------------------
# 🏷️ Отримання назв
# ------------------------------------------------
criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(int(num_criteria))])
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(int(num_alternatives))])
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
            "criteria_matrix": st.session_state.get("criteria_matrix", pd.DataFrame()).to_dict(),
            "alt_matrices": {k: v.to_dict() for k, v in st.session_state.get("alt_matrices", {}).items()},
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
        st.session_state.criteria_names = imported.get("criteria_names", [])
        st.session_state.alternative_names = imported.get("alternative_names", [])
        st.session_state.num_criteria = imported["num_criteria"]
        st.session_state.num_alternatives = imported["num_alternatives"]
        st.session_state.criteria_matrix = pd.DataFrame(imported["criteria_matrix"])
        st.session_state.alt_matrices = {k: pd.DataFrame(v) for k, v in imported.get("alt_matrices", {}).items()}
        st.sidebar.success("✅ Імпортовано, оновлення...")
        st.rerun()

# ------------------------------------------------
# 🎨 Ієрархічна діаграма
# ------------------------------------------------
st.markdown("## 🎯 Ієрархія задачі (візуалізація)")

dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")

dot.node("goal", goal_name, shape="box", style="filled", color="#a1c9f1")
for alt in alternative_names:
    dot.node(alt, alt, shape="ellipse", style="filled", color="#fce8a6")
for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="#b6fcb6")
    for alt in alternative_names:
        dot.edge(alt, crit)
    dot.edge(crit, "goal")

st.graphviz_chart(dot, use_container_width=True)

# ------------------------------------------------
# 📊 Матриця критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if (
    "criteria_matrix" not in st.session_state
    or len(st.session_state.criteria_matrix) != num_criteria
    or list(st.session_state.criteria_matrix.columns) != criteria_names
):
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)), columns=criteria_names, index=criteria_names
    )
else:
    st.session_state.criteria_matrix.columns = criteria_names
    st.session_state.criteria_matrix.index = criteria_names

criteria_df = st.data_editor(st.session_state.criteria_matrix, key="criteria_editor", use_container_width=True)

# ------------------------------------------------
# 🧮 Функції узгодженості
# ------------------------------------------------
RI_table = {1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24,
             7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49}


def calc_consistency(matrix):
    n = len(matrix)
    eigvals, _ = np.linalg.eig(matrix)
    lambda_max = np.max(np.real(eigvals))
    CI = (lambda_max - n) / (n - 1)
    RI = RI_table.get(n, 1.49)
    CR = CI / RI if RI != 0 else 0
    return lambda_max, CI, RI, CR


def enforce_symmetry(df):
    """Коректно оновлює симетрію A[i][j] = 1 / A[j][i] без скидання."""
    edited = df.copy()
    n = len(df)
    for i in range(n):
        for j in range(i + 1, n):  # ✅ лише верхній трикутник
            if edited.iloc[i, j] != 0:
                edited.iloc[j, i] = round(1 / edited.iloc[i, j], 3)
            elif edited.iloc[j, i] != 0:
                edited.iloc[i, j] = round(1 / edited.iloc[j, i], 3)
    np.fill_diagonal(edited.values, 1.0)
    return edited

# ------------------------------------------------
# 💾 Збереження змін і перевірка ВУ
# ------------------------------------------------
save_clicked = st.button("💾 Зберегти зміни в матриці критеріїв")

if save_clicked:
    edited_df = pd.DataFrame(criteria_df, columns=criteria_names, index=criteria_names).astype(float)
    edited_df = enforce_symmetry(edited_df)
    st.session_state.criteria_matrix = edited_df
    st.success("✅ Матриця оновлена! Симетричність забезпечено.")

lambda_max, CI, RI, CR = calc_consistency(st.session_state.criteria_matrix)
st.markdown(
    f"**λ<sub>max</sub> = {lambda_max:.3f}**, **ІУ = {CI:.3f}**, **ВВУ = {RI:.3f}**, **ВУ = {CR*100:.1f}%**",
    unsafe_allow_html=True,
)
if CR > 0.2:
    st.error("❌ ВУ > 20% — матриця неузгоджена, перевірте оцінки!")
else:
    st.success("✅ ВУ < 20% — узгодженість прийнятна.")

# ------------------------------------------------
# ⚙️ Матриці альтернатив
# ------------------------------------------------
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

tabs = st.tabs(criteria_names)
for tab, crit in zip(tabs, criteria_names):
    with tab:
        st.markdown(f"### ⚙️ Матриця альтернатив для критерію **{crit}**")

        if (
            crit not in st.session_state.alt_matrices
            or len(st.session_state.alt_matrices[crit]) != num_alternatives
            or list(st.session_state.alt_matrices[crit].columns) != alternative_names
        ):
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names, index=alternative_names
            )
        else:
            st.session_state.alt_matrices[crit].columns = alternative_names
            st.session_state.alt_matrices[crit].index = alternative_names

        alt_df = st.data_editor(st.session_state.alt_matrices[crit], key=f"matrix_{crit}", use_container_width=True)

        save_alt = st.button(f"💾 Зберегти зміни ({crit})")
        if save_alt:
            edited_alt_df = pd.DataFrame(alt_df, columns=alternative_names, index=alternative_names).astype(float)
            edited_alt_df = enforce_symmetry(edited_alt_df)
            st.session_state.alt_matrices[crit] = edited_alt_df
            st.success(f"✅ Матриця для {crit} оновлена! Симетричність забезпечено.")

        lam, ci, ri, cr = calc_consistency(st.session_state.alt_matrices[crit])
        st.markdown(
            f"**λ<sub>max</sub> = {lam:.3f}**, **ІУ = {ci:.3f}**, **ВВУ = {ri:.3f}**, **ВУ = {cr*100:.1f}%**",
            unsafe_allow_html=True,
        )
        if cr > 0.2:
            st.error("❌ ВУ > 20% — матриця неузгоджена, змініть оцінки!")
        else:
            st.success("✅ ВУ < 20% — узгодженість прийнятна.")

# ------------------------------------------------
# 🧮 Глобальні пріоритети
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    return norm.mean(axis=1)


st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

criteria_weights = calc_weights(st.session_state.criteria_matrix)
alt_weights = {crit: calc_weights(st.session_state.alt_matrices[crit]) for crit in criteria_names}

global_priorities = pd.DataFrame(index=alternative_names)
for crit, w in zip(criteria_names, criteria_weights):
    global_priorities[crit] = alt_weights[crit] * w

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
global_priorities = global_priorities.sort_values("Глоб. пріор.", ascending=False)

st.dataframe(global_priorities.style.format("{:.3f}"), use_container_width=True)
st.success("✅ Розрахунок завершено.")
