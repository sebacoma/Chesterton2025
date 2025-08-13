import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
from pathlib import Path
import json
import re

# ── Config página ─────────────────────────────────────
st.set_page_config(
    page_title="Chesterton SQM Dashboard",
    page_icon="🔧",
    layout="wide",
)

# ── Login ligero (users.json en la misma carpeta) ─────
USERS_FILE = Path(__file__).with_name("users.json")

@st.cache_data
def load_users(path=USERS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)["users"]

def authenticate(u, p, users):
    for usr in users:
        if usr["username"] == u and usr["password"] == p:
            return True, usr.get("name", u)
    return False, None

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.sidebar.header("🔒 Iniciar sesión")
    u = st.sidebar.text_input("Usuario")
    p = st.sidebar.text_input("Contraseña", type="password")
    if st.sidebar.button("Ingresar"):
        ok, name = authenticate(u, p, load_users())
        if ok:
            st.session_state.authenticated = True
            st.sidebar.success(f"¡Bienvenido, {name}!")
            st.rerun()
        else:
            st.sidebar.error("Credenciales inválidas")
    st.stop()

if st.sidebar.button("Cerrar sesión"):
    st.session_state.authenticated = False
    st.rerun()

# ── Encabezado ────────────────────────────────────────
st.title("🔧 Taller de Reparación de Sellos ")

# ── Carga y limpieza de datos ─────────────────────────
@st.cache_data
def load_data(xlsx, sheet="TallerReparación{recepción}"):
    df = pd.read_excel(xlsx, sheet_name=sheet)
    df.columns = df.columns.str.strip()            # limpia espacios

    # 1️ renombres estándar
    df = df.rename(
        columns={
            "SC": "Código SC",
            "Modelo": "Modelo",
            "Posible Falla": "Posible Falla",
            "Tipo de Reparacion": "Tipo de Reparación",
            # acepta "Column 1" 𝘰 "CheckList" → "Checklist OK"
            "Column 1": "Checklist OK",
            "CheckList": "Checklist OK",
            # acepta tanda*, Tanda*, etc. → "Tanda"
            **{c: "Tanda" for c in df.columns if re.match(r"^tanda\*?$", c, re.I)}
        }
    )

    # normaliza texto
    for col in ["Tipo de Reparación", "Posible Falla"]:
        if col in df:
            df[col] = (
                df[col]
                .replace(["0", 0], pd.NA)
                .str.strip()
                .str.capitalize()
                .str.replace(r"\s+", " ", regex=True)
            )

    # checklist a booleano si existe
    if "Checklist OK" in df:
        df["Checklist OK"] = df["Checklist OK"].fillna("").astype(str).str.lower() == "x"
    else:
        df["Checklist OK"] = False  # evita KeyError si faltara

    # asegúrate de que Tanda sea texto
    if "Tanda" in df:
        df["Tanda"] = df["Tanda"].astype(str).str.strip()
    else:
        df["Tanda"] = ""

    return df

# archivo por defecto o cargado
default_xlsx = Path(__file__).with_name("Chesterton_SQM-2.xlsx")
uploaded = st.sidebar.file_uploader("📤 Subir Excel", type=["xlsx"])

if uploaded:
    df = load_data(uploaded)
elif default_xlsx.exists():
    df = load_data(default_xlsx)
    st.sidebar.success("Usando archivo local `Chesterton_SQM.xlsx`")
else:
    st.error("Sube un Excel con la hoja `TallerReparación{recepción}`.")
    st.stop()

# ── Filtros ───────────────────────────────────────────
with st.sidebar:
    st.header("Filtros")
    tanda_sel = st.multiselect("Tanda", sorted(df["Tanda"].unique()),
                               default=list(df["Tanda"].unique()))
    tipo_sel = st.multiselect("Tipo de reparación",
                              sorted(df["Tipo de Reparación"].dropna().unique()),
                              default=list(df["Tipo de Reparación"].dropna().unique()))
    falla_sel = st.multiselect("Posible falla",
                               sorted(df["Posible Falla"].dropna().unique()),
                               default=list(df["Posible Falla"].dropna().unique()))
    solo_check = st.checkbox("Solo checklist ✓")

mask = (
    df["Tanda"].isin(tanda_sel)
    & df["Tipo de Reparación"].isin(tipo_sel)
    & df["Posible Falla"].isin(falla_sel)
)
if solo_check:
    mask &= df["Checklist OK"]

filtered = df[mask]

# ── Tarjetas KPI rectangulares ────────────────────────
def kpi_card(label, value, color):
    st.markdown(
        f"""
        <div style="
            padding:0.75rem 1rem;
            border-radius:0.5rem;
            background:{color};
            color:white;
            font-weight:600;
            text-align:center;">
            {label}<br><span style="font-size:1.8rem">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

k1, k2, k3 = st.columns(3)
with k1: kpi_card("Registros", len(filtered), "#6c63ff")
with k2: kpi_card("Tipos de reparación", filtered["Tipo de Reparación"].nunique(), "#00b894")
with k3: kpi_card("Tipos de falla", filtered["Posible Falla"].nunique(), "#fd9644")

# ── Plotly torta ──────────────────────────────────────
pie_df = (
    filtered["Tipo de Reparación"]
    .value_counts()
    .rename_axis("Tipo")
    .reset_index(name="Registros")
)
fig = px.pie(pie_df, names="Tipo", values="Registros", hole=0.4)
fig.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig, use_container_width=True)

# ── Barra fallas ──────────────────────────────────────
st.subheader("Distribución de posibles fallas")
bar = (
    alt.Chart(filtered)
    .mark_bar()
    .encode(
        x=alt.X("Posible Falla:N", sort="-y", title=None),
        y=alt.Y("count()", title="Registros"),
        tooltip=["Posible Falla", alt.Tooltip("count()", title="Registros")]
    )
)
st.altair_chart(bar, use_container_width=True)

# ── Heatmap ───────────────────────────────────────────
st.subheader("Cruce: Tipo de reparación × Posible falla")
cross = (
    filtered.groupby(["Tipo de Reparación", "Posible Falla"])
    .size()
    .reset_index(name="Registros")
)
heat = (
    alt.Chart(cross)
    .mark_rect()
    .encode(
        x=alt.X("Posible Falla:N", title=None),
        y=alt.Y("Tipo de Reparación:N", title=None),
        color=alt.Color("Registros:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["Tipo de Reparación", "Posible Falla", "Registros"],
    )
)
st.altair_chart(heat, use_container_width=True)

# ── Tabla ─────────────────────────────────────────────
st.subheader("Tabla detallada")
st.dataframe(filtered, use_container_width=True, height=400)
