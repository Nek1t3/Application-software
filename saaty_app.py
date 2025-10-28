import streamlit as st
import graphviz
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

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
alternative_names = st.session_state.get("alternative_names", [f"Альтернатива {j+1}" for j in range(num_alternatives)])
criteria_names = (criteria_names + [f"Критерій {i+1}" for i in range(len(criteria_names), num_criteria)])[:num_criteria]
alternative_names = (alternative_names + [f"Альтернатива {j+1}" for j in range(len(alternative_names), num_alternatives)])[:num_alternatives]
st.session_state.criteria_names = criteria_names
st.session_state.alternative_names = alternative_names

# ------------------------------------------------
# Граф
# ------------------------------------------------
dot = graphviz.Digraph()
dot.attr(size="15,8", ratio="fill", rankdir="TB")
dot.node("Goal", "ГОЛОВНА МЕТА", shape="box", style="filled", color="lightblue")
for crit in criteria_names:
    dot.node(crit, crit, shape="box", style="filled", color="lightgreen")
    dot.edge("Goal", crit)
    for alt in alternative_names:
        dot.node(alt, alt, shape="box", style="filled", color="lightyellow")
        dot.edge(crit, alt)
st.graphviz_chart(dot, width=1500, height=800)

# ------------------------------------------------
# Матриця критеріїв
# ------------------------------------------------
st.markdown("---")
st.markdown("## 📊 Матриці попарних порівнянь")
st.markdown("### 🧩 Матриця критеріїв")

if "criteria_matrix" not in st.session_state or len(st.session_state.criteria_matrix) != num_criteria:
    st.session_state.criteria_matrix = pd.DataFrame(
        np.ones((num_criteria, num_criteria)),
        columns=criteria_names,
        index=criteria_names
    )

# --- AGGRID побудова ---
matrix_df = st.session_state.criteria_matrix.copy().round(3)
matrix_df.reset_index(inplace=True)
matrix_df.rename(columns={"index": "Критерії ↓ / Критерії →"}, inplace=True)

gb = GridOptionsBuilder.from_dataframe(matrix_df)
gb.configure_default_column(editable=True)

# Діагональ блокуємо
for i, row_name in enumerate(criteria_names):
    col_name = criteria_names[i]
    gb.configure_column(col_name, cellStyle={"color": "gray"} if i == matrix_df.columns.get_loc(col_name) - 1 else None)

# Опції сітки
grid_options = gb.build()
grid_response = AgGrid(
    matrix_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    theme="balham",
    fit_columns_on_grid_load=True,
    enable_enterprise_modules=False,
    height=300,
    allow_unsafe_jscode=True,
)

# --- обробка змін ---
edited_df = pd.DataFrame(grid_response["data"])
edited_df.set_index("Критерії ↓ / Критерії →", inplace=True)

# Симетрія + блокування діагоналі
for i in range(num_criteria):
    for j in range(num_criteria):
        if i == j:
            edited_df.iloc[i, j] = 1.0
        else:
            val = edited_df.iloc[i, j]
            if pd.notna(val) and val != 0:
                try:
                    edited_df.iloc[j, i] = round(1 / float(val), 3)
                except Exception:
                    edited_df.iloc[j, i] = 1.0

st.session_state.criteria_matrix = edited_df
st.caption("🔒 Діагональ зафіксована (не редагується). Симетрія оновлюється автоматично.")

# ------------------------------------------------
# Матриці альтернатив
# ------------------------------------------------
if "alt_matrices" not in st.session_state:
    st.session_state.alt_matrices = {}

for crit in criteria_names:
    if crit not in st.session_state.alt_matrices or len(st.session_state.alt_matrices[crit]) != num_alternatives:
        st.session_state.alt_matrices[crit] = pd.DataFrame(
            np.ones((num_alternatives, num_alternatives)),
            columns=alternative_names,
            index=alternative_names
        )

    with st.expander(f"⚙️ Матриця альтернатив для критерію: {crit}"):
        alt_df = st.session_state.alt_matrices[crit].copy().round(3)
        alt_df.reset_index(inplace=True)
        alt_df.rename(columns={"index": "Альтернативи ↓ / →"}, inplace=True)

        gb2 = GridOptionsBuilder.from_dataframe(alt_df)
        gb2.configure_default_column(editable=True)
        grid_options2 = gb2.build()

        grid_response2 = AgGrid(
            alt_df,
            gridOptions=grid_options2,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            theme="balham",
            fit_columns_on_grid_load=True,
            height=300,
            allow_unsafe_jscode=True,
        )

        edited_alt_df = pd.DataFrame(grid_response2["data"])
        edited_alt_df.set_index("Альтернативи ↓ / →", inplace=True)

        for i in range(num_alternatives):
            for j in range(num_alternatives):
                if i == j:
                    edited_alt_df.iloc[i, j] = 1.0
                else:
                    val = edited_alt_df.iloc[i, j]
                    if pd.notna(val) and val != 0:
                        try:
                            edited_alt_df.iloc[j, i] = round(1 / float(val), 3)
                        except Exception:
                            edited_alt_df.iloc[j, i] = 1.0

        st.session_state.alt_matrices[crit] = edited_alt_df
        st.caption("🔒 Діагональ зафіксована (не редагується). Симетрія оновлюється автоматично.")

st.success("✅ Матриці оновлено. Симетрія працює, діагональ не редагується.")
