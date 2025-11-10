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
    st.session_state.criteria_matrix,  # Подаємо чистий DataFrame
    key="criteria_editor",
    use_container_width=True,
    # Встановлюємо формат лише для ВІДОБРАЖЕННЯ, якщо це можливо в нових версіях (але краще форматувати дані при збереженні)
    # У нових версіях streamlit можна використовувати column_config для форматування
)

# ------------------------------------------------
# 💾 Збереження змін у матриці критеріїв
# ------------------------------------------------
save_clicked = st.button("💾 Зберегти зміни в матриці критеріїв")

if save_clicked:
    edited_df = pd.DataFrame(criteria_df, columns=criteria_names, index=criteria_names).astype(float)
    prev = st.session_state.criteria_matrix.copy()
    
    # Використовуємо лише один трикутник матриці (верхній) для оновлення
    for i in range(num_criteria):
        for j in range(i, num_criteria): # Починаємо j з i
            if i == j:
                edited_df.iloc[i, j] = 1.0
                continue
            
            # Перевіряємо, чи змінилася комірка (i, j) (верхній трикутник)
            if edited_df.iloc[i, j] != prev.iloc[i, j]:
                val = edited_df.iloc[i, j]
                
                # Це ціле число (напр., 3, 5, 7)
                if val > 1: 
                    # Округлюємо його, щоб виправити помилки (напр. 3.003 -> 3.0)
                    if np.isclose(val, np.round(val)):
                        val = float(np.round(val))
                    
                    edited_df.iloc[i, j] = val
                    edited_df.iloc[j, i] = round(1 / val, 3) # Розраховуємо дріб
                
                # Це дріб (напр., 1/3, 1/5, 1/7)
                elif val < 1:
                    val = round(val, 3) # Округлюємо дріб до 3 знаків
                    edited_df.iloc[i, j] = val
                    
                    # Розраховуємо зворотне і перевіряємо, чи воно близьке до цілого
                    inv_val = 1 / val
                    if np.isclose(inv_val, np.round(inv_val)):
                        edited_df.iloc[j, i] = float(np.round(inv_val)) # Зберігаємо як 3.0, 7.0 і т.д.
                    else:
                        edited_df.iloc[j, i] = round(inv_val, 3)

            # Перевіряємо, чи змінилася комірка (j, i) (нижній трикутник)
            elif edited_df.iloc[j, i] != prev.iloc[j, i]:
                val = edited_df.iloc[j, i]

                # Це ціле число (напр., 3, 5, 7)
                if val > 1:
                    if np.isclose(val, np.round(val)):
                        val = float(np.round(val))
                    
                    edited_df.iloc[j, i] = val
                    edited_df.iloc[i, j] = round(1 / val, 3) # Розраховуємо дріб

                # Це дріб (напр., 1/3, 1/5, 1/7)
                elif val < 1:
                    val = round(val, 3) # Округлюємо дріб
                    edited_df.iloc[j, i] = val
                    
                    inv_val = 1 / val
                    if np.isclose(inv_val, np.round(inv_val)):
                        edited_df.iloc[i, j] = float(np.round(inv_val)) # Робимо цілим
                    else:
                        edited_df.iloc[i, j] = round(inv_val, 3)

    np.fill_diagonal(edited_df.values, 1.000)
    st.session_state.criteria_matrix = edited_df

    col_sum = edited_df.sum(axis=0)
    norm_matrix = edited_df / col_sum
    weights = norm_matrix.mean(axis=1).round(3)

    result_df = edited_df.copy()
    result_df["Вектор пріоритетів"] = weights

    st.success("✅ Матриця критеріїв оновлена та коректно округлена!")
    st.dataframe(result_df.style.format("{:.3f}"), use_container_width=True)
    st.rerun() # Примусово оновлюємо сторінку, щоб data_editor підтягнув чисті дані

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
            st.session_state.alt_matrices[crit],
            key=f"matrix_{crit}",
            use_container_width=True,
        )

        save_alt = st.button(f"💾 Зберегти зміни ({crit})")

        if save_alt:
            edited_alt_df = pd.DataFrame(alt_df, columns=alternative_names, index=alternative_names).astype(float)
            prev_alt = st.session_state.alt_matrices[crit].copy()

            # Логіка, аналогічна до матриці критеріїв
            for i in range(num_alternatives):
                for j in range(i, num_alternatives): # Починаємо j з i
                    if i == j:
                        edited_alt_df.iloc[i, j] = 1.0
                        continue
                    
                    # Перевіряємо, чи змінилася комірка (i, j) (верхній трикутник)
                    if edited_alt_df.iloc[i, j] != prev_alt.iloc[i, j]:
                        val = edited_alt_df.iloc[i, j]
                        
                        if val > 1: 
                            if np.isclose(val, np.round(val)):
                                val = float(np.round(val))
                            edited_alt_df.iloc[i, j] = val
                            edited_alt_df.iloc[j, i] = round(1 / val, 3)
                        
                        elif val < 1:
                            val = round(val, 3) 
                            edited_alt_df.iloc[i, j] = val
                            inv_val = 1 / val
                            if np.isclose(inv_val, np.round(inv_val)):
                                edited_alt_df.iloc[j, i] = float(np.round(inv_val))
                            else:
                                edited_alt_df.iloc[j, i] = round(inv_val, 3)

                    # Перевіряємо, чи змінилася комірка (j, i) (нижній трикутник)
                    elif edited_alt_df.iloc[j, i] != prev_alt.iloc[j, i]:
                        val = edited_alt_df.iloc[j, i]

                        if val > 1:
                            if np.isclose(val, np.round(val)):
                                val = float(np.round(val))
                            edited_alt_df.iloc[j, i] = val
                            edited_alt_df.iloc[i, j] = round(1 / val, 3)

                        elif val < 1:
                            val = round(val, 3)
                            edited_alt_df.iloc[j, i] = val
                            inv_val = 1 / val
                            if np.isclose(inv_val, np.round(inv_val)):
                                edited_alt_df.iloc[i, j] = float(np.round(inv_val))
                            else:
                                edited_alt_df.iloc[i, j] = round(inv_val, 3)

            np.fill_diagonal(edited_alt_df.values, 1.000)
            st.session_state.alt_matrices[crit] = edited_alt_df
            st.success(f"✅ Матриця для {crit} оновлена!")
            st.dataframe(edited_alt_df.style.format("{:.3f}"), use_container_width=True)
            st.rerun() # Примусове оновлення

# ------------------------------------------------
# 🧮 Розрахунок глобальних пріоритетів
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    # Перевірка на нульові суми, щоб уникнути ділення на нуль
    if (col_sum == 0).any():
        st.warning("Помилка: сума стовпця нульова. Неможливо нормалізувати.")
        return pd.Series(np.nan, index=matrix.index)
    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

# Перевіряємо, чи всі матриці існують
criteria_ready = "criteria_matrix" in st.session_state
alts_ready = all(crit in st.session_state.alt_matrices for crit in criteria_names)

if criteria_ready and alts_ready and len(criteria_names) > 0 and len(alternative_names) > 0:
    
    try:
        criteria_weights = calc_weights(st.session_state.criteria_matrix)
        
        # Перевірка, чи ваги критеріїв розрахувалися
        if criteria_weights.isnull().any():
            st.error("❌ Не вдалося розрахувати ваги критеріїв. Перевірте матрицю критеріїв.")
        else:
            alt_weights_dict = {}
            all_alts_calculated = True
            
            for crit in criteria_names:
                weights = calc_weights(st.session_state.alt_matrices[crit])
                if weights.isnull().any():
                    st.error(f"❌ Не вдалося розрахувати ваги для альтернатив за критерієм '{crit}'.")
                    all_alts_calculated = False
                    break
                alt_weights_dict[crit] = weights

            if all_alts_calculated:
                # Створюємо DataFrame з вагами альтернатив
                alt_weights_df = pd.DataFrame(alt_weights_dict)
                
                # Множимо ваги альтернатив на ваги критеріїв
                # (alt_weights_df - (N_alt x N_crit), criteria_weights - (N_crit x 1))
                global_priorities_vec = alt_weights_df.dot(criteria_weights)
                
                # Додаємо розрахунки до DataFrame для відображення
                final_df = alt_weights_df.copy()
                final_df['Ваги крит. (Wk)'] = criteria_weights
                
                # Створюємо підсумковий DataFrame
                global_priorities_display = pd.DataFrame({
                    "Глоб. пріор.": global_priorities_vec
                })
                global_priorities_display = global_priorities_display.sort_values("Глоб. пріор.", ascending=False)
                
                st.markdown("### 1. Ваги альтернатив по кожному критерію (W_ij)")
                st.dataframe(alt_weights_df.style.format("{:.3f}"), use_container_width=True)
                
                st.markdown("### 2. Ваги критеріїв (W_j)")
                st.dataframe(criteria_weights.to_frame(name="Вага").style.format("{:.3f}"), use_container_width=True)

                st.markdown("### 3. Глобальні пріоритети (W_i)")
                st.dataframe(global_priorities_display.style.format("{:.3f}"), use_container_width=True)
                
                st.success("✅ Розрахунок завершено!")

    except Exception as e:
        st.error(f"❌ Помилка при розрахунку глобальних пріоритетів: {e}. Перевірте введені значення.")
else:
    st.warning("⚠️ Необхідно заповнити та зберегти Матрицю критеріїв та всі Матриці альтернатив для розрахунку.")
