# =========================
# 📊 Матриця попарних порівнянь критеріїв
# =========================
st.markdown("## 📊 Матриця попарних порівнянь критеріїв")

# Ініціалізація або розширення
if ss.criteria_matrix.empty or len(ss.criteria_matrix) != ss.num_criteria:
    ss.criteria_matrix = pd.DataFrame(
        np.ones((ss.num_criteria, ss.num_criteria)),
        index=criteria_names, columns=criteria_names
    )
else:
    ss.criteria_matrix = ss.criteria_matrix.reindex(
        index=criteria_names, columns=criteria_names, fill_value=1.0
    )

criteria_df = st.data_editor(
    ss.criteria_matrix,
    key="criteria_editor",
    use_container_width=True
)

def enforce_full_symmetry(df: pd.DataFrame) -> pd.DataFrame:
    """Забезпечує повну симетрію матриці навіть при неповних введеннях."""
    df = df.copy().fillna(1.0)
    n = len(df)
    for i in range(n):
        df.iloc[i, i] = 1.0
        for j in range(i + 1, n):
            try:
                val = float(df.iloc[i, j])
                if val <= 0:  # уникаємо 0 або від’ємних
                    val = 1.0
            except Exception:
                val = 1.0
            df.iloc[i, j] = round(val, 3)
            df.iloc[j, i] = round(1.0 / val, 3)
    return df

if st.button("💾 Зберегти зміни в матриці критеріїв"):
    edited_df = pd.DataFrame(criteria_df, index=criteria_names, columns=criteria_names).astype(float)
    edited_df = enforce_full_symmetry(edited_df)
    ss.criteria_matrix = edited_df
    st.success("✅ Повна симетричність застосована до всієї матриці.")
    st.rerun()

lam, ci, ri, cr = calc_consistency(ss.criteria_matrix)
st.markdown(
    f"**λₘₐₓ = {lam:.3f}**, **ІУ = {ci:.3f}**, **ВВУ = {ri:.3f}**, **ВУ = {cr*100:.1f}%**",
    unsafe_allow_html=True
)
if cr <= 0.2:
    st.info("ℹ️ ВУ < 20% — узгодженість прийнятна.")
else:
    st.error("❌ ВУ > 20% — перевірте оцінки!")
