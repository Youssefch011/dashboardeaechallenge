import streamlit as st
import pandas as pd
import plotly.express as px
import math

st.set_page_config(
    page_title="EAE Challenge PMO",
    page_icon="📊",
    layout="wide"
)

# LOAD DATA
bd1 = pd.read_excel("BDEAECHALLENGE.xlsx", sheet_name="BD1")
bd3 = pd.read_excel("BDEAECHALLENGE.xlsx", sheet_name="BD3 (profesorado)")
bd4 = pd.read_csv("BD4(Dispo_Prof).csv")

for df in [bd1, bd3, bd4]:
    df.columns = df.columns.str.strip().str.upper()

bd1["HORAS"] = (
    bd1["HORAS"].astype(str)
    .str.replace(",", ".", regex=False)
    .str.extract(r"(\d+\.?\d*)")[0]
)

bd1["HORAS"] = pd.to_numeric(bd1["HORAS"], errors="coerce").fillna(0)

area_col = [c for c in bd4.columns if "AREA" in c and "CONOCIMIENTO" in c][0]

# KPIs
total_professors = bd3["NOMBRE"].nunique()

accredited_professors = bd3[
    bd3["ACREDITADO"].astype(str).str.upper().isin(["SI", "SÍ", "YES"])
]["NOMBRE"].nunique()

programs = bd1["PROGRAMA"].nunique()
assigned_hours = int(bd1["HORAS"].sum())

# HEADER
st.title("📊 Academic Scheduling & PMO Platform")
st.write("Coordinator view, Professor Plan, and Module Detail dashboard.")

tab1, tab2, tab3 = st.tabs([
    "📊 Coordinator Dashboard",
    "👨‍🏫 Professor Plan",
    "📚 Module Detail"
])

# =====================================================
# TAB 1 — COORDINATOR DASHBOARD
# =====================================================

with tab1:
    st.subheader("📊 Coordinator Dashboard")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Professors", total_professors)
    col2.metric("Accredited Professors", accredited_professors)
    col3.metric("Programs", programs)
    col4.metric("Assigned Hours", assigned_hours)

    st.divider()

    area_data = (
        bd4.groupby(area_col)["NOMBRE"]
        .nunique()
        .reset_index()
        .sort_values("NOMBRE", ascending=True)
    )
    area_data.columns = ["Knowledge Area", "Total Professors"]

    st.subheader("📚 Professors by Knowledge Area")

    fig_area = px.bar(
        area_data,
        x="Total Professors",
        y="Knowledge Area",
        orientation="h",
        text="Total Professors",
        title="Teaching Capacity by Knowledge Area"
    )
    fig_area.update_traces(textposition="outside")
    fig_area.update_layout(height=600)
    st.plotly_chart(fig_area, use_container_width=True)

    st.subheader("🌊 Dynamic Knowledge Area Wave")

    wave_frames = []
    for frame in range(20):
        temp = area_data.copy()
        temp["Wave Value"] = temp["Total Professors"] + [
            math.sin((i + frame) / 2) * 2 for i in range(len(temp))
        ]
        temp["Frame"] = frame
        wave_frames.append(temp)

    wave_df = pd.concat(wave_frames)

    fig_wave = px.line(
        wave_df,
        x="Knowledge Area",
        y="Wave Value",
        animation_frame="Frame",
        markers=True,
        title="Animated Teaching Capacity Wave"
    )
    fig_wave.update_layout(height=450, xaxis_tickangle=-45)
    st.plotly_chart(fig_wave, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        st.subheader("🌍 Professors by Language")

        language_data = (
            bd3.groupby("IDIOMA")["NOMBRE"]
            .nunique()
            .reset_index()
        )
        language_data.columns = ["Language", "Total Professors"]

        fig_lang = px.pie(
            language_data,
            names="Language",
            values="Total Professors",
            hole=0.45,
            title="Language Distribution"
        )
        st.plotly_chart(fig_lang, use_container_width=True)

    with col6:
        st.subheader("🏫 Classes by Modality")

        modality_data = (
            bd1.groupby("MODALIDAD")
            .size()
            .reset_index(name="Total Classes")
        )

        fig_modality = px.pie(
            modality_data,
            names="MODALIDAD",
            values="Total Classes",
            title="Modality Distribution"
        )
        st.plotly_chart(fig_modality, use_container_width=True)

    st.divider()
    st.subheader("👨‍🏫 Top 20 Professor Workload")

    workload = (
        bd4.groupby("NOMBRE")
        .size()
        .reset_index(name="Assigned Slots")
        .sort_values("Assigned Slots", ascending=False)
    )

    fig_workload = px.bar(
        workload.head(20),
        x="Assigned Slots",
        y="NOMBRE",
        orientation="h",
        title="Top 20 Professors by Assigned Slots"
    )
    st.plotly_chart(fig_workload, use_container_width=True)

# =====================================================
# TAB 2 — PROFESSOR PLAN
# =====================================================

with tab2:
    st.subheader("👨‍🏫 Professor Plan")

    selected_professor = st.selectbox(
        "Select a professor",
        options=sorted(bd4["NOMBRE"].dropna().unique())
    )

    prof_data = bd4[bd4["NOMBRE"] == selected_professor]

    colA, colB, colC = st.columns(3)
    colA.metric("Assigned Slots", len(prof_data))
    colB.metric("Knowledge Areas", prof_data[area_col].nunique())

    if "MES" in prof_data.columns:
        colC.metric("Active Months", prof_data["MES"].nunique())
    else:
        colC.metric("Records", len(prof_data))

    # Accreditation Status
    st.divider()
    st.subheader("🎓 Accreditation Status")

    if "ACREDITADO" in bd3.columns:
        prof_accreditation = bd3[
            bd3["NOMBRE"] == selected_professor
        ][["NOMBRE", "ACREDITADO"]].drop_duplicates()

        if not prof_accreditation.empty:
            accreditation_value = prof_accreditation["ACREDITADO"].iloc[0]
            accreditation_clean = str(accreditation_value).upper()

            if accreditation_clean in ["SI", "SÍ", "YES"]:
                st.success(f"✅ {selected_professor} is ACCREDITED")
            else:
                st.error(f"❌ {selected_professor} is NOT accredited")

            st.dataframe(prof_accreditation, use_container_width=True)
        else:
            st.warning("No accreditation information found.")

    col7, col8 = st.columns(2)

    with col7:
        st.write("### Monthly Workload")

        if "MES" in prof_data.columns:
            month_data = (
                prof_data.groupby("MES")
                .size()
                .reset_index(name="Assigned Slots")
            )

            fig_month = px.bar(
                month_data,
                x="MES",
                y="Assigned Slots",
                title=f"Monthly Workload - {selected_professor}"
            )
            st.plotly_chart(fig_month, use_container_width=True)
        else:
            st.info("No month column available.")

    with col8:
        st.write("### Professor Knowledge Area Distribution")

        prof_area = (
            prof_data.groupby(area_col)
            .size()
            .reset_index(name="Records")
        )

        fig_prof_area = px.pie(
            prof_area,
            names=area_col,
            values="Records",
            hole=0.45,
            title=f"Knowledge Areas - {selected_professor}"
        )
        st.plotly_chart(fig_prof_area, use_container_width=True)

    st.write("### Professor Planning Data")
    st.dataframe(prof_data, use_container_width=True)

    st.divider()
    st.subheader("🟢 Professor Availability by Module")

    if all(col in prof_data.columns for col in ["MES", "HORARIO", area_col]):
        selected_module_prof = st.selectbox(
            "Select module / knowledge area for this professor",
            options=sorted(prof_data[area_col].dropna().unique())
        )

        module_prof_data = prof_data[prof_data[area_col] == selected_module_prof]

        availability_data = (
            module_prof_data.groupby(["MES", "HORARIO"])
            .size()
            .reset_index(name="Availability Slots")
        )

        fig_availability = px.density_heatmap(
            availability_data,
            x="MES",
            y="HORARIO",
            z="Availability Slots",
            color_continuous_scale="Greens",
            title=f"Availability Heatmap - {selected_professor} | {selected_module_prof}"
        )
        fig_availability.update_layout(height=500)
        st.plotly_chart(fig_availability, use_container_width=True)

        st.write("### Module Availability Details")
        st.dataframe(module_prof_data, use_container_width=True)
    else:
        st.info("Not enough columns to create availability by module chart.")

# =====================================================
# TAB 3 — MODULE DETAIL
# =====================================================

with tab3:
    st.subheader("📚 Module Detail Dashboard")

    selected_module = st.selectbox(
        "Select a module / knowledge area",
        options=sorted(bd4[area_col].dropna().unique())
    )

    module_data = bd4[bd4[area_col] == selected_module]

    colM1, colM2, colM3 = st.columns(3)
    colM1.metric("Available Professors", module_data["NOMBRE"].nunique())
    colM2.metric("Total Availability Records", len(module_data))

    if "MES" in module_data.columns:
        colM3.metric("Active Months", module_data["MES"].nunique())
    else:
        colM3.metric("Records", len(module_data))

    st.divider()

    colM4, colM5 = st.columns(2)

    with colM4:
        st.write("### Professors Available for This Module")

        module_professors = (
            module_data.groupby("NOMBRE")
            .size()
            .reset_index(name="Availability Slots")
            .sort_values("Availability Slots", ascending=False)
        )

        fig_module_prof = px.bar(
            module_professors.head(20),
            x="Availability Slots",
            y="NOMBRE",
            orientation="h",
            title=f"Top Professors Available - {selected_module}"
        )
        st.plotly_chart(fig_module_prof, use_container_width=True)

    with colM5:
        st.write("### Availability by Month")

        if "MES" in module_data.columns:
            module_month = (
                module_data.groupby("MES")
                .size()
                .reset_index(name="Availability Slots")
            )

            fig_module_month = px.bar(
                module_month,
                x="MES",
                y="Availability Slots",
                title=f"Monthly Availability - {selected_module}"
            )
            st.plotly_chart(fig_module_month, use_container_width=True)
        else:
            st.info("No month column available.")

    st.write("### Module Availability Heatmap")

    if all(col in module_data.columns for col in ["MES", "HORARIO"]):
        module_heatmap = (
            module_data.groupby(["MES", "HORARIO"])
            .size()
            .reset_index(name="Availability Slots")
        )

        fig_module_heatmap = px.density_heatmap(
            module_heatmap,
            x="MES",
            y="HORARIO",
            z="Availability Slots",
            color_continuous_scale="Blues",
            title=f"Availability Heatmap - {selected_module}"
        )
        fig_module_heatmap.update_layout(height=500)
        st.plotly_chart(fig_module_heatmap, use_container_width=True)
    else:
        st.info("Not enough columns for heatmap.")

    st.write("### Module Detail Table")
    st.dataframe(module_data, use_container_width=True)

    st.divider()
    st.subheader("📌 Classes by Language")

    lang_classes = (
        bd1.groupby("IDIOMA")
        .size()
        .reset_index(name="Total Classes")
    )

    fig_class_lang = px.bar(
        lang_classes,
        x="IDIOMA",
        y="Total Classes",
        title="Classes by Language"
    )
    st.plotly_chart(fig_class_lang, use_container_width=True)