import streamlit as st
import pandas as pd
import numpy as np
import graphviz
import json
from io import BytesIO

# =========================
# Налаштування сторінки
# =========================
st.set_page_config(page_title="Метод Сааті", layout="wide")
st.title("Метод Сааті — Ієрархія задачі")

# =========================
# Ініціалізація state
# =========================
ss = st.session_state
if "num_criteria" not in ss:        ss.num_criteria = 3
if "num_alternatives" not in ss:    ss.num_alternatives = 3
if "criteria_matrix" not in ss:     ss.criteria_matrix = pd.DataFrame()
if "alt_matrices" not in ss:        ss.alt_matrices = {}
if "goal_name" not in ss:           ss.goal_name = "ГОЛОВНА МЕТА"

# Кількість елементів
num_criteria = st.number_input("Кількість критеріїв:", 1, 9, value=ss.num_criteria)
num_alternatives = st.number_input("Кількість альтернатив:", 1, 9, value=ss.num_alternatives)

# Синхронізація кількостей
if int(num_criteria) != ss.num_criteria:
    ss.num_criteria = int(num_criteria)
    st.rerun()
if int(num_alternatives) != ss.num_alternatives:
    ss.num_alternatives = int(num_alternatives)
    st.rerun()

# Назви
criteria_names = [f"Критерій {i+1}" for i in range(ss.num_criteria)]
alternative_names = [f"Альтернатива {j+1}" for j in range(ss.num_alternatives)]
goal_name = ss.goal_name

# =========================
# Збереження / Імпорт
# =========================
st.sidebar.header("💾 Збереження / Імпорт")
mode = st.sidebar.radio("Оберіть режим:", ["Зберегти матриці", "Імпортувати матриці"])

if mode == "Зберегти матриці":
    filename = st.sidebar.text_input("Ім'я файлу (без .json):", "ahp_matrices")
    if st.sidebar.button("💾 Зберегти як JSON"):
        export_data = {
            "goal_name": goal_name,
            "criteria_names": criteria_names,
            "alternative_names": alternative_names,
            "num_criteria": ss.num_criteria,
            "num_alternatives": ss.num_alternatives,
            "criteria_matrix": ss.criteria_matrix.to_dict(),
            "alt_matrices": {k: v.to_dict() for k, v in ss.alt_matrices.items()},
        }
        st.sidebar.download_button(
            "⬇️ Завантажити JSON-файл",
            data=BytesIO(json.dumps(export_data, ensure_ascii=False, indent=2).encode("utf-8")),
            file_name=f"{filename}.json",
            mime="application/json",
        )
else:
    uploaded = st.sidebar.file_uploader("📥 Завантажити JSON", type=["json"])
    if uploaded:
        data = json.load(uploaded)
        ss.goal_name = data.get("goal_name", "ГОЛОВНА МЕТА")
        ss.criteria_matrix = pd.DataFrame(data["criteria_matrix"])
        ss.alt_matrices = {k: pd.DataFrame(v) for k, v in data.get("alt_matrices", {}).items()}
        ss.num_criteria = int(data["num_criteria"])
        ss.num_alternatives = int(data["num_alternatives"])
        st.sidebar.success("✅ Імпортовано. Оновлюю…")
        st.rerun()

# =========================
# Ієрархічна діаграма
# =========================
st.markdown("## 🎯 Ієрархія задачі (візуалізація)")
dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")
dot.node("goal", goal_name, shape="box", style="filled", color="#a1c9f1")
for c in criteria_names:
    dot.node(c, c, shape="box", style="filled", color="#b6fcb6")
    dot.edge(c, "goal")
for a in alternative_names:
    dot.node(a, a, shape="ellipse", style="filled", color="#fce8a6")
    for c in criteria_names:
        dot.edge(a, c)
st.graphviz_chart(dot, use_container_width=True)

# =========================
# Допоміжні функції
# =========================
RI_TABLE = {1:0, 2:0, 3:0.58, 4:0.90, 5:1.12, 6:1.24, 7:1.32, 8:1.41, 9:1.45, 10:1.49}

def enforce_symmetry(df: pd.DataFrame) -> pd.DataFrame:
    """A[i,j] = 1 / A[j,i], діагональ = 1."""
    edited = df.copy()
    n = len(edited)
    for i in range(n):
        edited.iloc[i, i] = 1.0
        for j in range(i+1, n):
            val = float(edited.iloc[i, j])
            if val == 0:
                # якщо випадково поставлено 0 — замінюємо одиницею
                val = 1.0
            edited.iloc[i, j] = round(val, 3)
            edited.iloc[j, i] = round(1.0 / val, 3)
    return edited

def calc_consistency(mat: pd.DataFrame):
    n = len(mat)
    eigvals = np.linalg.eigvals(mat.values.astype(float))
    lam_max = float(np.max(np.real(eigvals)))
    CI = (lam_max - n) / (n - 1) if n > 1 else 0.0
    RI = RI_TABLE.get(n, 1.49)
    CR = CI / RI if RI else 0.0
    return lam_max, CI, RI, CR

def calc_weights(mat: pd.DataFrame) -> pd.Series:
    col_sum = mat.sum(axis=0)
    norm = mat / col_sum
    return norm.mean(axis=1)

# =========================
# Матриця критеріїв
# =========================
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

# Ініціалізація / реіндексація
if ss.criteria_matrix.empty or len(ss.criteria_matrix) != ss.num_criteria:
    ss.criteria_matrix = pd.DataFrame(np.ones((ss.num_criteria, ss.num_criteria)),
                                      index=criteria_names, columns=criteria_names)
else:
    ss.criteria_matrix = ss.criteria_matrix.reindex(index=criteria_names,
                                                    columns=criteria_names,
                                                    fill_value=1.0)

criteria_df = st.data_editor(
    ss.criteria_matrix,
    key="criteria_editor",
    use_container_width=True
)

# Зберегти (симетрія застосовується одразу з першим кліком)
if st.button("💾 Зберегти зміни в матриці критеріїв"):
    edited = pd.DataFrame(criteria_df, index=criteria_names, columns=criteria_names).astype(float)
    ss.criteria_matrix = enforce_symmetry(edited).copy()
    st.success("✅ Симетричність застосовано.")
    st.rerun()

lam, ci, ri, cr = calc_consistency(ss.criteria_matrix)
st.markdown(f"**λₘₐₓ = {lam:.3f}**, **ІУ = {ci:.3f}**, **ВВУ = {ri:.3f}**, **ВУ = {cr*100:.1f}%**",
            unsafe_allow_html=True)
st.info("ℹ️ ВУ має бути < 20%.") if cr <= 0.2 else st.error("❌ ВУ > 20% — перевірте оцінки!")

# =========================
# Матриці альтернатив
# =========================
tabs = st.tabs(criteria_names)
for idx, (crit, tab) in enumerate(zip(criteria_names, tabs)):
    with tab:
        st.markdown(f"### ⚙️ Матриця альтернатив для **{crit}**")

        # ініціалізація / реіндексація
        if (crit not in ss.alt_matrices) or (len(ss.alt_matrices[crit]) != ss.num_alternatives):
            ss.alt_matrices[crit] = pd.DataFrame(np.ones((ss.num_alternatives, ss.num_alternatives)),
                                                 index=alternative_names, columns=alternative_names)
        else:
            ss.alt_matrices[crit] = ss.alt_matrices[crit].reindex(index=alternative_names,
                                                                   columns=alternative_names,
                                                                   fill_value=1.0)

        alt_df = st.data_editor(
            ss.alt_matrices[crit],
            key=f"alt_editor_{idx}",
            use_container_width=True
        )

        if st.button(f"💾 Зберегти ({crit})", key=f"save_alt_{idx}"):
            edited_alt = pd.DataFrame(alt_df, index=alternative_names, columns=alternative_names).astype(float)
            ss.alt_matrices[crit] = enforce_symmetry(edited_alt).copy()
            st.success(f"✅ Симетричність застосовано ({crit}).")
            st.rerun()

        lam_a, ci_a, ri_a, cr_a = calc_consistency(ss.alt_matrices[crit])
        st.markdown(f"**λₘₐₓ = {lam_a:.3f}**, **ІУ = {ci_a:.3f}**, **ВВУ = {ri_a:.3f}**, **ВУ = {cr_a*100:.1f}%**",
                    unsafe_allow_html=True)
        st.info("ℹ️ ВУ має бути < 20%.") if cr_a <= 0.2 else st.error("❌ ВУ > 20% — змініть оцінки!")

# =========================
# Глобальні пріоритети
# =========================
st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

criteria_w = calc_weights(ss.criteria_matrix)
alt_w = {c: calc_weights(ss.alt_matrices[c]) for c in criteria_names}

global_priorities = pd.DataFrame(index=alternative_names)
for c in criteria_names:
    global_priorities[c] = alt_w[c] * criteria_w[c]

global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
st.dataframe(global_priorities.style.format("{:.3f}"), use_container_width=True)
st.success("✅ Розрахунок завершено.")
