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
st.title("Метод Сааті — Ієрархия задачі")

# ------------------------------------------------
# 📈 Таблиця випадкової узгодженості (ВВУ / RI)
# ------------------------------------------------
# (n: ВВУ) для n = 1...10
RI_TABLE = {
    1: 0, 2: 0, 3: 0.58, 4: 0.9, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41, 9: 1.45, 10: 1.49
}

# ------------------------------------------------
# 🧮 Функції розрахунку
# ------------------------------------------------
def calc_weights(matrix):
    col_sum = matrix.sum(axis=0)
    if (col_sum == 0).any():
        st.warning("Помилка: сума стовпця нульова. Неможливо нормалізувати.")
        return pd.Series(np.nan, index=matrix.index)
    if not np.all(np.isfinite(col_sum)) or (col_sum == 0).all():
        st.error("Помилка в даних матриці (NaN/Inf або нульові стовпці). Розрахунок неможливий.")
        return pd.Series(np.nan, index=matrix.index)

    norm = matrix / col_sum
    weights = norm.mean(axis=1)
    return weights

def calculate_consistency(matrix):
    """
    Розраховує Lambda Max, Індекс Узгодженості (ІУ/CI) та Відношення Узгодженості (ВУ/CR).
    """
    n = len(matrix)
    if n < 3:
        return n, 0, 0 # Для n=1, 2 узгодженість завжди ідеальна

    weights = calc_weights(matrix)
    if weights.isnull().any():
        return np.nan, np.nan, np.nan # Помилка при розрахунку ваг

    aw_vector = matrix.dot(weights)
    consist_vector = aw_vector / weights
    
    lambda_max = consist_vector.mean()
    
    ci = (lambda_max - n) / (n - 1)
    
    ri = RI_TABLE.get(n)
    if ri == 0:
        cr = 0 # Уникнення ділення на нуль (хоча n < 3 вже оброблено)
    else:
        cr = ci / ri
        
    return lambda_max, ci, cr

# ------------------------------------------------
# 📦 Ініціалізація session_state
# ------------------------------------------------
if "num_criteria" not in st.session_state:
    st.session_state.num_criteria = 3
if "num_alternatives" not in st.session_state:
    st.session_state.num_alternatives = 3
if "alt_consistency" not in st.session_state:
    st.session_state.alt_consistency = {}

num_criteria = st.number_input(
    "Кількість критеріїв:", 1, 10, value=st.session_state.num_criteria # Збільшено до 10, як на фото
)
num_alternatives = st.number_input(
    "Кількість альтернатив:", 1, 9, value=st.session_state.num_alternatives
)

# ✅ Підтримка оновлення при зміні кількості
if num_criteria != st.session_state.num_criteria:
    st.session_state.num_criteria = int(num_criteria)
    # При зміні кількості, видаляємо старі ваги та узгодженість
    if "criteria_weights_display" in st.session_state:
        del st.session_state.criteria_weights_display
    if "criteria_consistency" in st.session_state:
        del st.session_state.criteria_consistency
    st.rerun()
if num_alternatives != st.session_state.num_alternatives:
    st.session_state.num_alternatives = int(num_alternatives)
    # Скидаємо розрахунки узгодженості для альтернатив
    st.session_state.alt_consistency = {}
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
            label="⬇️ Завантажити JSON-файл", data=b, file_name=f"{filename}.json", mime="application/json"
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
                # Скидаємо всі розрахунки
                if "criteria_weights_display" in st.session_state:
                    del st.session_state.criteria_weights_display
                if "criteria_consistency" in st.session_state:
                    del st.session_state.criteria_consistency
                st.session_state.alt_consistency = {}
                st.sidebar.success("✅ Матриці імпортовано! Оновлення застосунку...")
                st.rerun()

        except Exception as e:
            st.sidebar.error(f"❌ Помилка при імпорті: {e}")

# ... (Код для 🎨 Ієрархічна діаграма ... залишається без змін) ...
st.markdown("## 🎯 Ієрархія задачі (візуалізація)")
dot = graphviz.Digraph()
dot.attr(rankdir="BT", size="8,6")
dot.node("goal", goal_name, shape="box", style="filled", color="#a1c9f1")
for alt in alternative_names:
    dot.node(alt, alt, shape="ellipse", style="filled", color="#fce8a6")
for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="#b6fcb6")
for crit in criteria_names:
    for alt in alternative_names:
        dot.edge(alt, crit)
    dot.edge(crit, "goal")
st.graphviz_chart(dot, use_container_width=True)

# ------------------------------------------------
# 📊 Матриця попарних порівнянь критеріїв
# ------------------------------------------------
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

# 1. Ініціалізуємо матрицю, ТІЛЬКИ ЯКЩО її немає або змінився РОЗМІР
if (
    "criteria_matrix" not in st.session_state
    or len(st.session_state.criteria_matrix) != num_criteria
):
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names,
    )
    if "criteria_weights_display" in st.session_state:
        del st.session_state.criteria_weights_display
    if "criteria_consistency" in st.session_state:
        del st.session_state.criteria_consistency

# 2. ЗАВЖДИ оновлюємо назви колонок/індексів (це не руйнує дані)
st.session_state.criteria_matrix.columns = criteria_names
st.session_state.criteria_matrix.index = criteria_names

criteria_df = st.data_editor(
    st.session_state.criteria_matrix,
    key="criteria_editor",
    use_container_width=True,
)

# ------------------------------------------------
# 💾 Збереження змін у матриці критеріїв
# ------------------------------------------------
save_clicked = st.button("💾 Зберегти зміни в матриці критеріїв")

if save_clicked:
    edited_df = pd.DataFrame(criteria_df, columns=criteria_names, index=criteria_names).astype(float)
    
    # --- НОВА ПЕРЕВІРКА НА > 9 ---
    if (edited_df > 9).any().any():
        st.error("🚨 **Помилка: Введено числа, більші за 9.**\n\nМетод Сааті використовує шкалу від 1 (однакова важливість) до 9 (абсолютна перевага). Будь ласка, виправте введені значення.")
    else:
        # --- СТАРА ЛОГІКА ЗБЕРЕЖЕННЯ (тепер всередині 'else') ---
        prev = st.session_state.criteria_matrix.copy()
        
        for i in range(num_criteria):
            for j in range(i, num_criteria): 
                if i == j:
                    edited_df.iloc[i, j] = 1.0
                    continue
                if edited_df.iloc[i, j] != prev.iloc[i, j]:
                    val = edited_df.iloc[i, j]
                    if val > 1: 
                        if np.isclose(val, np.round(val)): val = float(np.round(val))
                        edited_df.iloc[i, j] = val
                        edited_df.iloc[j, i] = round(1 / val, 3)
                    elif val < 1:
                        val = round(val, 3) 
                        edited_df.iloc[i, j] = val
                        inv_val = 1 / val
                        if np.isclose(inv_val, np.round(inv_val)):
                            edited_df.iloc[j, i] = float(np.round(inv_val))
                        else:
                            edited_df.iloc[j, i] = round(inv_val, 3)
                elif edited_df.iloc[j, i] != prev.iloc[j, i]:
                    val = edited_df.iloc[j, i]
                    if val > 1:
                        if np.isclose(val, np.round(val)): val = float(np.round(val))
                        edited_df.iloc[j, i] = val
                        edited_df.iloc[i, j] = round(1 / val, 3)
                    elif val < 1:
                        val = round(val, 3)
                        edited_df.iloc[j, i] = val
                        inv_val = 1 / val
                        if np.isclose(inv_val, np.round(inv_val)):
                            edited_df.iloc[i, j] = float(np.round(inv_val))
                        else:
                            edited_df.iloc[i, j] = round(inv_val, 3)

        np.fill_diagonal(edited_df.values, 1.000)
        st.session_state.criteria_matrix = edited_df

        # 1. Розраховуємо ваги
        weights = calc_weights(edited_df)
        st.session_state.criteria_weights_display = weights.round(3)
        
        # 2. Розраховуємо узгодженість
        lambda_max, ci, cr = calculate_consistency(edited_df)
        st.session_state.criteria_consistency = {"lambda": lambda_max, "ci": ci, "cr": cr}
        
        st.success("✅ Матриця критеріїв оновлена та коректно округлена!")


# --- Постійне відображення матриці + ваг + узгодженості ---
if "criteria_weights_display" in st.session_state:
    if len(st.session_state.criteria_weights_display) == len(st.session_state.criteria_matrix):
        st.markdown("### Матриця критеріїв з вектором пріоритетів")
        display_df = st.session_state.criteria_matrix.copy()
        display_df["Вектор пріоритетів"] = st.session_state.criteria_weights_display
        st.dataframe(display_df.style.format("{:.3f}"), use_container_width=True)
    else:
        del st.session_state.criteria_weights_display
        if "criteria_consistency" in st.session_state:
            del st.session_state.criteria_consistency

# --- БЛОК ВІДОБРАЖЕННЯ УЗГОДЖЕНОСТІ КРИТЕРІЇВ ---
if "criteria_consistency" in st.session_state:
    st.markdown("#### 🔬 Аналіз узгодженості критеріїв")
    cons_data = st.session_state.criteria_consistency
    
    col1, col2, col3 = st.columns(3)
    col1.metric("λ max (Лямбда)", f"{cons_data['lambda']:.3f}")
    col2.metric("Індекс Узгодженості (ІУ)", f"{cons_data['ci']:.3f}")
    col3.metric("Відношення Узгодженості (ВУ)", f"{cons_data['cr']:.1%}") # {cons_data['cr']:.3f}
    
    if cons_data['cr'] > 0.20:
        st.error("🚨 **Увага! ВУ > 20%**\n\nУзгодженість матриці низька. Це означає, що ваші судження суперечливі. Будь ласка, перегляньте та змініть значення в матриці.")
    elif np.isnan(cons_data['cr']):
        st.warning("Не вдалося розрахувати узгодженість. Перевірте, чи немає нулів у стовпцях матриці.")
    else:
        st.success("✅ **ВУ ≤ 20%**\n\nУзгодженість матриці в межах норми.")


# ------------------------------------------------
# ⚙️ Матриці альтернатив
# ------------------------------------------------
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

st.markdown("---")
st.markdown("## ⚙️ Матриці альтернатив по кожному критерію")

tabs = st.tabs(criteria_names)
for tab, crit in zip(tabs, criteria_names):
    with tab:
        st.markdown(f"### Порівняння альтернатив за критерієм **{crit}**")

        if (
            crit not in st.session_state.alt_matrices
            or len(st.session_state.alt_matrices[crit]) != num_alternatives
        ):
            st.session_state.alt_matrices[crit] = pd.DataFrame(
                np.ones((num_alternatives, num_alternatives)),
                columns=alternative_names,
                index=alternative_names,
            )
            if crit in st.session_state.alt_consistency:
                del st.session_state.alt_consistency[crit]

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
            
            # --- НОВА ПЕРЕВІРКА НА > 9 ---
            if (edited_alt_df > 9).any().any():
                st.error(f"🚨 **Помилка: Введено числа, більші за 9, у матриці для '{crit}'.**\n\nБудь ласка, використовуйте лише значення від 1 до 9.")
            else:
                # --- СТАРА ЛОГІКА ЗБЕРЕЖЕННЯ (тепер всередині 'else') ---
                prev_alt = st.session_state.alt_matrices[crit].copy()

                for i in range(num_alternatives):
                    for j in range(i, num_alternatives):
                        if i == j:
                            edited_alt_df.iloc[i, j] = 1.0
                            continue
                        if edited_alt_df.iloc[i, j] != prev_alt.iloc[i, j]:
                            val = edited_alt_df.iloc[i, j]
                            if val > 1: 
                                if np.isclose(val, np.round(val)): val = float(np.round(val))
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
                        elif edited_alt_df.iloc[j, i] != prev_alt.iloc[j, i]:
                            val = edited_alt_df.iloc[j, i]
                            if val > 1:
                                if np.isclose(val, np.round(val)): val = float(np.round(val))
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
                
                # --- Розрахунок узгодженості для матриці альтернатив ---
                lambda_max, ci, cr = calculate_consistency(edited_alt_df)
                st.session_state.alt_consistency[crit] = {"lambda": lambda_max, "ci": ci, "cr": cr}
                
                st.success(f"✅ Матриця для {crit} оновлена!")
                
                # Показуємо оновлену матрицю відразу
                st.dataframe(edited_alt_df.style.format("{:.3f}"), use_container_width=True)

        # --- БЛОК ВІДОБРАЖЕННЯ УЗГОДЖЕНОСТІ АЛЬТЕРНАТИВ ---
        if crit in st.session_state.alt_consistency:
            st.markdown(f"#### 🔬 Аналіз узгодженості для **{crit}**")
            cons_data = st.session_state.alt_consistency[crit]
            
            col1, col2, col3 = st.columns(3)
            col1.metric("λ max (Лямбда)", f"{cons_data['lambda']:.3f}")
            col2.metric("Індекс Узгодженості (ІУ)", f"{cons_data['ci']:.3f}")
            col3.metric("Відношення Узгодженості (ВУ)", f"{cons_data['cr']:.1%}")
            
            if cons_data['cr'] > 0.20:
                st.error(f"🚨 **Увага! ВУ > 20%**\n\nУзгодженість матриці для '{crit}' низька. Перегляньте ваші порівняння.")
            elif np.isnan(cons_data['cr']):
                st.warning("Не вдалося розрахувати узгодженість. Перевірте, чи немає нулів у стовпцях матриці.")
            else:
                st.success(f"✅ **ВУ ≤ 20%**\n\nУзгодженість матриці для '{crit}' в межах норми.")


# ------------------------------------------------
# 🧮 Розрахунок глобальних пріоритетів
# ------------------------------------------------
st.markdown("---")
st.markdown("## 🧮 Розрахунок глобальних пріоритетів")

# ... (Код розрахунку ... залишається без змін) ...
criteria_ready = "criteria_matrix" in st.session_state
alts_ready = all(crit in st.session_state.alt_matrices for crit in criteria_names)

if criteria_ready and alts_ready and len(criteria_names) > 0 and len(alternative_names) > 0:
    try:
        criteria_weights = calc_weights(st.session_state.criteria_matrix)
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
                alt_weights_df = pd.DataFrame(alt_weights_dict)
                alt_weights_df = alt_weights_df.reindex(index=alternative_names, columns=criteria_names)
                criteria_weights = criteria_weights.reindex(index=criteria_names)
                global_priorities_vec = alt_weights_df.dot(criteria_weights)
                global_priorities_display = pd.DataFrame({
                    "Глоб. пріор.": global_priorities_vec
                }, index=alternative_names)
                global_priorities_display = global_priorities_display.sort_values("Глоб. пріор.", ascending=False)
                
                st.markdown("### 1. Ваги альтернатив по кожному критерію (W_ij)")
                st.dataframe(alt_weights_df.style.format("{:.3f}"), use_container_width=True)
                st.markdown("### 2. Глобальні пріоритети (W_i)")
                st.dataframe(global_priorities_display.style.format("{:.3f}"), use_container_width=True)
                st.success("✅ Розрахунок завершено!")
    except Exception as e:
        st.error(f"❌ Помилка при розрахунку глобальних пріоритетів: {e}. Перевірте введені значення.")
else:
    st.warning("⚠️ Необхідно заповнити та зберегти Матрицю критеріїв та всі Матриці альтернатив для розрахунку.")
