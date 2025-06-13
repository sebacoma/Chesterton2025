import streamlit as st
import pandas as pd
import altair as alt
from pathlib import Path

st.set_page_config(
    page_title="Chesterton SQM Dashboard",
    page_icon="🔧",
    layout="wide",
)

st.title("🔧 Taller de Reparación de Sellos SQM")
st.caption("Fuente: hoja **TallerReparación{recepción}**")

@st.cache_data  
def load_data(path_or_file, sheet="TallerReparación{recepción}"):
    """Lee Excel o archivo subido y devuelve DataFrame limpio."""
    if isinstance(path_or_file, Path) or isinstance(path_or_file, str):
        df = pd.read_excel(path_or_file, sheet_name=sheet)
    else:  
        df = pd.read_excel(path_or_file, sheet_name=sheet)


    df = df.rename(
        columns={
            "SC": "Código SC",
            "Modelo": "Modelo",
            "Posible Falla": "Posible Falla",
            "Tipo de Reparacion": "Tipo de Reparación",
            "Column 1": "Checklist OK",
        }
    )

    for col in ["Tipo de Reparación", "Posible Falla"]:
        df[col] = df[col].replace(["0", 0], pd.NA)

    for col in ["Tipo de Reparación", "Posible Falla"]:
        df[col] = (
            df[col]
            .str.strip()
            .str.capitalize()
            .str.replace(r"\s+", " ", regex=True)
        )

    df["Checklist OK"] = df["Checklist OK"].fillna("").astype(str).str.lower() == "x"
    return df


def kpi_card(col_name, value, color):
    """Dibuja una tarjeta KPI usando markdown + CSS inline."""
    st.markdown(
        f"""
        <div style="
            padding:0.75rem 1rem;
            border-radius:0.5rem;
            background:{color};
            color:white;
            font-weight:600;
            text-align:center;
            ">
            {col_name}<br><span style="font-size:1.75rem">{value}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


default_path = Path(__file__).with_name("Chesterton_SQM-2.xlsx")
uploaded_file = st.sidebar.file_uploader(
    "📤 Subir archivo Excel con los datos", type=["xlsx"]
)
if uploaded_file:
    df = load_data(uploaded_file)
elif default_path.exists():
    df = load_data(default_path)
    st.sidebar.success("Usando archivo local `Chesterton_SQM.xlsx`")
else:
    st.error(
        "No se encontró el archivo por defecto. Sube un Excel con la hoja "
        "`TallerReparación{recepción}`."
    )
    st.stop()


with st.sidebar:
    st.header("Filtros")
    tipo_reparacion = st.multiselect(
        "Tipo de reparación", sorted(df["Tipo de Reparación"].dropna().unique()),
        default=list(df["Tipo de Reparación"].dropna().unique()),
    )
    falla = st.multiselect(
        "Posible falla", sorted(df["Posible Falla"].dropna().unique()),
        default=list(df["Posible Falla"].dropna().unique()),
    )
    solo_check = st.checkbox("Mostrar solo registros con checklist ✓", value=False)

mask = (
    df["Tipo de Reparación"].isin(tipo_reparacion)
    & df["Posible Falla"].isin(falla)
)
if solo_check:
    mask &= df["Checklist OK"]

filtered = df[mask]


total_registros = len(filtered)
tipos_unicos = filtered["Tipo de Reparación"].nunique()
fallas_unicas = filtered["Posible Falla"].nunique()

kpi_cols = st.columns(3)
kpi_card("Registros", total_registros, "#6c63ff")
kpi_card("Tipos de reparación", tipos_unicos, "#00b894")
kpi_card("Tipos de falla", fallas_unicas, "#fd9644")

###############################################################################
#  Visualizaciones
###############################################################################
import plotly.express as px


pie_tipo = (
    filtered["Tipo de Reparación"]
    .value_counts()                                
    .rename_axis("Tipo de Reparación")             
    .reset_index(name="Registros")                 
)


fig = px.pie(
    pie_tipo,
    names="Tipo de Reparación",
    values="Registros",
    hole=0.4,                
)
fig.update_traces(textposition="inside", textinfo="percent+label")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Distribución de posibles fallas")
bar_falla = (
    alt.Chart(filtered)
    .mark_bar()
    .encode(
        y=alt.Y("count()", title="Número de registros"),
        x=alt.X("Posible Falla:N", sort="-y", title=None),
        tooltip=["Posible Falla", alt.Tooltip("count()", title="Registros")],
    )
)
st.altair_chart(bar_falla, use_container_width=True)

st.subheader("Cruce: Tipo de reparación × Posible falla")
heat_data = (
    filtered.groupby(["Tipo de Reparación", "Posible Falla"])
    .size()
    .reset_index(name="Registros")
)
heatmap = (
    alt.Chart(heat_data)
    .mark_rect()
    .encode(
        x=alt.X("Posible Falla:N", title=None),
        y=alt.Y("Tipo de Reparación:N", title=None),
        color=alt.Color("Registros:Q", scale=alt.Scale(scheme="blues")),
        tooltip=["Tipo de Reparación", "Posible Falla", "Registros"],
    )
)
st.altair_chart(heatmap, use_container_width=True)

st.subheader("Tabla detallada")
st.dataframe(filtered, use_container_width=True, height=400)
