import streamlit as st
import graphviz
import pandas as pd
import numpy as np

# ------------------------------------------------
# Налаштування сторінки
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

criteria_names = st.session_state.get("criteria_names", [f"Критерій {i+1}" for i in range(num_criteria)])
criteria_names = (criteria_names + [f"Критерій {i+1}" for i in range(len(criteria_names), num_criteria)])[:num_criteria]
st.session_state.criteria_names = criteria_names

# ------------------------------------------------
# Побудова графу
# ------------------------------------------------
dot = graphviz.Digraph()
dot.attr(size="15,8", ratio="fill", rankdir="TB")
dot.node("Goal", "ГОЛОВНА МЕТА", shape="box", style="filled", color="lightblue")

for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", crit)

st.graphviz_chart(dot, width=1500, height=500)

# ------------------------------------------------
# Матриця попарних порівнянь критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")
st.info("⚠️ Діагональ не можна змінювати — вона завжди дорівнює 1 (сірі клітинки).")

# ініціалізація
if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

prev_matrix = st.session_state.criteria_matrix.copy()

# редагування
edited_matrix = st.data_editor(
    prev_matrix,
    key="criteria_editor",
    use_container_width=True,
    num_rows="dynamic"
)

# логіка дзеркальності та блокування діагоналі
for i in range(num_criteria):
    for j in range(num_criteria):
        val = edited_matrix.iloc[i, j]

        # якщо користувач намагається змінити діагональ
        if i == j:
            if val != 1:
                edited_matrix.iloc[i, j] = 1.0

        # якщо змінилась не-діагональна комірка
        elif edited_matrix.iloc[i, j] != prev_matrix.iloc[i, j]:
            if pd.notna(val) and val != 0:
                try:
                    edited_matrix.iloc[j, i] = round(1 / float(val))
                except Exception:
                    edited_matrix.iloc[j, i] = 1.0

# гарантуємо, що діагональ = 1 і округлення до цілих
np.fill_diagonal(edited_matrix.values, 1.0)
edited_matrix = edited_matrix.astype(float).round(0)

st.session_state.criteria_matrix = edited_matrix

# ------------------------------------------------
# Візуальна підсвітка діагоналі
# ------------------------------------------------
def style_diagonal(df: pd.DataFrame):
    n = df.shape[0]
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    for i in range(n):
        styles.iloc[i, i] = "background-color: #dddddd; color: #333333; font-weight: 600;"
    return (
        df.style
        .format(precision=0)
        .apply(lambda _: styles, axis=None)
        .set_table_styles([{"selector": "th", "props": "font-weight: 600; text-align: center;"}])
    )

# показуємо одну таблицю (з підсвіченою діагоналлю)
st.dataframe(style_diagonal(st.session_state.criteria_matrix), use_container_width=True)

st.success("✅ Готово: діагональ сірого кольору, фіксована = 1, симетрія підтримується.")
