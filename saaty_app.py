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

# Встановлюємо формат відображення для Streamlit DataFrame
pd.set_option('display.float_format', '{:.3f}'.format)

num_criteria = st.number_input(
    "Кількість критеріїв:", 1, 9, value=st.session_state.num_criteria
)
num_alternatives = st.number_input(
    "Кількість альтернатив:", 1, 9, value=st.session_state.num_alternatives
)

# ✅ Підтримка оновлення при зміні кількості
if num_criteria != st.session_state.num_criteria:
    st.session_state.num_criteria = int(num_criteria)
    st.rerun()
if num_alternatives != st.session_state.num_alternatives:
    st.session_state.num_alternatives = int(num_alternatives)
    st.rerun()

# ------------------------------------------------
# 🏷️ Отримання назв з session_state
# ------------------------------------------------
criteria_names = st.session_state.get(
    "criteria_names", [f"Критерій {i+1}" for i in range(int(num_criteria))]
)
alternative_names = st.session_state.get(
    "alternative_names", [f"Альтернатива {j+1}" for j in range(int(num_alternatives))]
)
goal_name = st.session_state.get("goal_name", "ГОЛОВНА МЕТА")

# Перевіряємо відповідність кількості назв
if len(criteria_names) != num_criteria:
    criteria_names = [f"Критерій {i+1}" for i in range(int(num_criteria))]
if len(alternative_names) != num_alternatives:
    alternative_names = [f"Альтернатива {j+1}" for j in range(int(num_alternatives))]

# ------------------------------------------------
# 💾 Вкладка збереження / імпорту
# ------------------------------------------------
st.sidebar.header("💾 Збереження / Імпорт")
mode = st.sidebar.radio("Оберіть режим:", ["Зберегти матриці", "Імпортувати матриці"])

if mode == "Зберегти матриці":
    st.sidebar.markdown("#### 📤 Експортувати поточні матриці")
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
        b = BytesIO(json_str.encode("utf-8"))

        st.sidebar.download_button(
            label="⬇️ Завантажити JSON-файл",
            data=b,
            file_name=f"{filename}.json",
            mime="application/json",
        )
        st.sidebar.success(f"✅ Файл {filename}.json готовий до завантаження.")

elif mode == "Імпортувати матриці":
    st.sidebar.markdown("#### 📥 Завантажити готові матриці")
    uploaded_file = st.sidebar.file_uploader("Оберіть JSON-файл", type=["json"])

    if uploaded_file:
        try:
            imported = json.load(uploaded_file)
            st.sidebar.success("✅ Файл успішно прочитано!")

            if st.sidebar.button("📂 Імпортувати в застосунок"):
                st.session_state.goal_name = imported.get("goal_name", "ГОЛОВНА МЕТА")
                st.session_state.criteria_names = imported.get("criteria_names", [])
                st.session_state.alternative_names = imported.get("alternative_names", [])
                st.session_state.num_criteria = imported["num_criteria"]
                st.session_state.num_alternatives = imported["num_alternatives"]
                st.session_state.criteria_matrix = pd.DataFrame(imported["criteria_matrix"])
                st.session_state.alt_matrices = {
                    k: pd.DataFrame(v) for k, v in imported.get("alt_matrices", {}).items()
                }
                st.sidebar.success("✅ Матриці імпортовано! Оновлення застосунку...")
                st.rerun()

        except Exception as e:
            st.sidebar.error(f"❌ Помилка при імпорті: {e}")

# ------------------------------------------------
# 🎨 Ієрархічна діаграма
# ------------------------------------------------
st.markdown("## 🎯 Ієрархія задачі (візуалізація)")

dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")  # BT = стрілки знизу вгору

# Головна мета
dot.node("goal", goal_name, shape="box", style="filled", color="#a1c9f1")

# Альтернативи (внизу)
for alt in alternative_names:
    dot.node(alt, alt, shape="ellipse", style="filled", color="#fce8a6")

# Критерії (посередині)
for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="#b6fcb6")

# Стрілки
for crit in criteria_names:
    for alt in alternative_names:
        dot.edge(alt, crit)
    dot.edge(crit, "goal")

st.graphviz_chart(dot, use_container_width=True)

# ------------------------------------------------
# 📊 Матриця попарних порівнянь критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

if (
    "criteria_matrix" not in st.session_state
    or len(st.session_state.criteria_matrix) != num_criteria
    or list(st.session_state.criteria_matrix.columns) != criteria_names
    or list(st.session_state.criteria_matrix.index) != criteria_names
):
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names,
    )
else:
    # Оновлюємо назви без втрати значень
    st.session_state.criteria_matrix.columns = criteria_names
    st.session_state.criteria_matrix.index = criteria_names

criteria_df = st.data_editor(
    st.session_state.criteria_matrix.style.format("{:.3f}"), # Додаємо форматування для відображення
    key="criteria_editor",
    use_container_width=True,
)

# ------------------------------------------------
# 💾 Збереження змін у матриці критеріїв
# ------------------------------------------------
save_clicked = st.button("💾 Зберегти зміни в матриці критеріїв")

if save_clicked:
    edited_df = pd.DataFrame(criteria_df, columns=criteria_names, index=criteria_names).astype(float)
    
    for i in range(num_criteria):
        for j in range(num_criteria):
            if i == j:
                edited_df.iloc[i, j] = 1.000
            else:
                val = edited_df.iloc[i, j]
                if pd.notna(val) and val != 0:
                    
                    # Перевіряємо, чи число близьке до цілого (1-9)
                    if np.isclose(val, np.round(val)) and 1 <= np.round(val) <= 9:
                        val = float(np.round(val)) # Фіксуємо як точне ціле число (1, 2, 3...)
                        inv = round(1 / val, 3)    # Обернене округлюємо до 3 знаків
                    else:
                        # Якщо це обернене значення (1/N), зберігаємо його і округлюємо
                        val = round(val, 3)
                        
                        # Якщо обернене значення, розраховуємо зворотнє як ціле
                        # Перевіряємо, чи зворотнє число близьке до цілого (1-9)
                        if np.isclose(1 / val, np.round(1 / val)) and 1 <= np.round(1 / val) <= 9:
                             inv = float(np.round(1 / val))
                        else:
                            inv = round(1 / val, 3)
                    
                    edited_df.iloc[i, j] = val
                    
                    # Симетричний елемент: якщо поточне (i, j) = N, тоді (j, i) = 1/N
                    # Якщо поточне (i, j) = 1/N, тоді (j, i) = N
                    if edited_df.iloc[i, j] > 1:
                         edited_df.iloc[j, i] = round(1 / edited_df.iloc[i, j], 3)
                    elif edited_df.iloc[i, j] < 1:
                         # Розраховуємо обернене значення, щоб воно було цілим (якщо близьке)
                         inv_val = 1 / edited_df.iloc[i, j]
                         if np.isclose(inv_val, np.round(inv_val)) and 1 <= np.round(inv_val) <= 9:
                             edited_df.iloc[j, i] = float(np.round(inv_val))
                         else:
                             edited_df.iloc[j, i] = round(inv_val, 3)

    np.fill_diagonal(edited_df.values, 1.000)
    st.session_state.criteria_matrix = edited_df.copy() # Копіюємо оновлену матрицю

    col_sum = edited_df.sum(axis=0)
    norm_matrix = edited_df / col_sum
    weights = norm_matrix.mean(axis=1).round(3)

    result_df = edited_df.copy()
    result_df["Вектор пріоритетів"] = weights

    st.success("✅ Матриця критеріїв оновлена та округлена відповідно до правил Сааті!")
    st.dataframe(result_df.style.format("{:.3f}"), use_container_width=True)

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
            or list(st.session_state.alt_matrices[crit].index) != alternative_names
        ):
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names,
                index=alternative_names,
            )
        else:
            st.session_state.alt_matrices[crit].columns = alternative_names
            st.session_state.alt_matrices[crit].index = alternative_names

        alt_df = st.data_editor(
            st.session_state.alt_matrices[crit].style.format("{:.3f}"),
            key=f"matrix_{crit}",
            use_container_width=True,
        )

        save_alt = st.button(f"💾 Зберегти зміни ({crit})")

        if save_alt:
            edited_alt_df = pd.DataFrame(alt_df, columns=alternative_names, index=alternative_names).astype(float)
            
            for i in range(num_alternatives):
                for j in range(num_alternatives):
                    if i == j:
                        edited_alt_df.iloc[i, j] = 1.000
                    else:
                        val = edited_alt_df.iloc[i, j]
                        if pd.notna(val) and val != 0:
                            
                            # Перевіряємо, чи число близьке до цілого (1-9)
                            if np.isclose(val, np.round(val)) and 1 <= np.round(val) <= 9:
                                val = float(np.round(val)) # Фіксуємо як точне ціле число (1, 2, 3...)
                            else:
                                val = round(val, 3)
                            
                            edited_alt_df.iloc[i, j] = val

                            # Симетричний елемент:
                            if edited_alt_df.iloc[i, j] > 1:
                                edited_alt_df.iloc[j, i] = round(1 / edited_alt_df.iloc[i, j], 3)
                            elif edited_alt_df.iloc[i, j] < 1:
                                # Розраховуємо обернене значення, щоб воно було цілим (якщо близьке)
                                inv_val = 1 / edited_alt_df.iloc[i, j]
                                if np.isclose(inv_val, np.round(inv_val)) and 1 <= np.round(inv_val) <= 9:
                                    edited_alt_df.iloc[j, i] = float(np.round(inv_val))
                                else:
                                    edited_alt_df.iloc[j, i] = round(inv_val, 3)

            np.fill_diagonal(edited_alt_df.values, 1.000)
            st.session_state.alt_matrices[crit] = edited_alt_df.copy()
            st.success(f"✅ Матриця для {crit} оновлена та округлена!")
            st.dataframe(edited_alt_df.style.format("{:.3f}"), use_container_width=True)

# ------------------------------------------------
# 🧮 Розрахунок глобальних пріоритетів
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

if "criteria_matrix" in st.session_state and all(crit in st.session_state.alt_matrices for crit in criteria_names):
    
    try:
        criteria_weights = calc_weights(st.session_state.criteria_matrix)
        alt_weights = {crit: calc_weights(st.session_state.alt_matrices[crit]) for crit in criteria_names}

        global_priorities = pd.DataFrame(index=alternative_names)
        for crit, w in zip(criteria_names, criteria_weights):
            # Перевірка, щоб уникнути помилок, якщо матриці мають різну розмірність
            if len(alt_weights[crit]) == len(alternative_names):
                global_priorities[crit] = alt_weights[crit].values * w
            else:
                 st.warning(f"⚠️ Проблема з розмірністю матриці для критерію {crit}. Пропускаємо.")
                 global_priorities[crit] = np.nan
                 
        global_priorities.dropna(axis=1, how='all', inplace=True) # Видалити стовпці з NaN

        if not global_priorities.empty:
            global_priorities["Глоб. пріор."] = global_priorities.sum(axis=1)
            global_priorities = global_priorities.sort_values("Глоб. пріор.", ascending=False)

            st.dataframe(global_priorities.style.format("{:.3f}"), use_container_width=True)
            st.success("✅ Розрахунок завершено! Назви синхронізовані з редагованими.")
        else:
             st.error("❌ Неможливо розрахувати глобальні пріоритети. Перевірте розмірності матриць.")

    except Exception as e:
        st.error(f"❌ Помилка при розрахунку глобальних пріоритетів: {e}. Перевірте введені значення.")
else:
    st.warning("⚠️ Необхідно заповнити та зберегти Матрицю критеріїв та всі Матриці альтернатив для розрахунку.")
