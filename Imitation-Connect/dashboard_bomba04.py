
import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Bomba 04 - Dashboard", layout="wide")

st.title(" Dashboard de Condición")
st.caption("Fuente: archivo Excel con series temporales de presión, temperatura, vibración y aceleración.")
DEFAULT_FILE = "Bomba 04-Data.xlsx"

# --- Sidebar ---
st.sidebar.header("⚙️ Configuración")
uploaded = st.sidebar.file_uploader("Sube el archivo Excel (.xlsx)", type=["xlsx"])

# Permitir elegir hoja
sheet_name = st.sidebar.text_input("Nombre de la hoja", value="Data")

# Rango de fechas (se ajustará tras cargar)
date_range = None

def load_data(file):
    # Leer Excel
    df = pd.read_excel(file, sheet_name=sheet_name)

    # Normalizar nombres
    df.columns = [c.strip() for c in df.columns]

    # Parseo de fecha/hora
    ts_col = "Local TimeStamp" if "Local TimeStamp" in df.columns else df.columns[0]
    df[ts_col] = pd.to_datetime(df[ts_col], dayfirst=True, errors="coerce")

    # Convertir columnas numéricas que vienen con coma decimal
    def to_num(s):
        if isinstance(s, str):
            s = s.replace(",", ".")
        return pd.to_numeric(s, errors="coerce")

    for c in df.columns:
        if c == ts_col: 
            continue
        df[c] = df[c].apply(to_num)

    # Derivados: Velocity RMS vectorial y Acceleration Peak
    vel_cols = [c for c in df.columns if c.lower().startswith("velocity")]
    acc_cols = [c for c in df.columns if c.lower().startswith("acceleration")]

    if vel_cols:
        # Vector RMS = sqrt(Vx^2 + Vy^2 + Vz^2)
        df["Velocity RMS (vector)"] = np.sqrt(np.nansum([np.square(df[c]) for c in vel_cols], axis=0))

    if acc_cols:
        df["Acceleration Peak (max axis)"] = np.nanmax(df[acc_cols].values, axis=1)

    # Ordenar por tiempo y filtrar NaT
    df = df.dropna(subset=[ts_col]).sort_values(ts_col)

    return df, ts_col, vel_cols, acc_cols

# Cargar datos
source = uploaded if uploaded is not None else (DEFAULT_FILE if os.path.exists(DEFAULT_FILE) else None)
if source is None:
    st.info("Sube un archivo .xlsx para comenzar.")
    st.stop()

df, ts_col, vel_cols, acc_cols = load_data(source)

min_date, max_date = df[ts_col].min(), df[ts_col].max()
st.sidebar.write(f"📅 Rango: **{min_date}** a **{max_date}**")

start, end = st.sidebar.date_input(
    "Filtrar por fecha",
    value=(min_date.date(), max_date.date()),
    min_value=min_date.date(), max_value=max_date.date()
)
# Aplicar filtro
mask = (df[ts_col] >= pd.to_datetime(start)) & (df[ts_col] <= pd.to_datetime(end) + pd.Timedelta(days=1))
df = df.loc[mask]

# --- Controles de Umbrales ---
st.sidebar.header("🚨 Umbrales de Alerta")
st.sidebar.caption("Define valores límite para cada parámetro")

# Umbrales para cada gráfico
threshold_pressure = st.sidebar.number_input(
    "Process Pressure (Bar)", 
    min_value=0.0, max_value=20.0, value=None, step=0.1,
    help="Umbral de alerta para presión del proceso"
)

threshold_process_temp = st.sidebar.number_input(
    "Process Temperature (°C)", 
    min_value=0.0, max_value=100.0, value=None, step=1.0,
    help="Umbral de alerta para temperatura del proceso"
)

threshold_surface_temp = st.sidebar.number_input(
    "Surface Temperature (°C)", 
    min_value=0.0, max_value=100.0, value=None, step=1.0,
    help="Umbral de alerta para temperatura de superficie"
)

threshold_acceleration = st.sidebar.number_input(
    "Acceleration Peak (g)", 
    min_value=0.0, max_value=50.0, value=None, step=0.1,
    help="Umbral de alerta para pico de aceleración"
)

threshold_velocity = st.sidebar.number_input(
    "Velocity RMS (mm/s)", 
    min_value=0.0, max_value=100.0, value=None, step=0.1,
    help="Umbral de alerta para velocidad RMS"
)

# Helper para trazas estilo "área suave"
def line_area(fig, x, y, name, yaxis_title=None, threshold=None, height=320, margin=None):
    """Add a line + shaded band trace to a Plotly figure and apply a clean layout.

    Parameters:
    - fig: go.Figure instance
    - x, y: data
    - name: trace name
    - yaxis_title: string for y-axis label
    - threshold: optional horizontal threshold to draw
    - height: figure height in px (default larger for more space)
    - margin: dict to override margins (l,r,t,b). If None, use sensible defaults.
    """
    
    # Si hay umbral, separar datos en normales y por encima del umbral
    if threshold is not None:
        y_series = pd.Series(y)
        mask_over = y_series > threshold
        
        # Crear arrays para datos normales y excedidos
        y_normal = y_series.where(~mask_over, np.nan)
        y_over = y_series.where(mask_over, np.nan)
        
        # Traza principal (valores normales)
        fig.add_trace(go.Scatter(
            x=x, y=y_normal, mode="lines",
            name=name, line=dict(width=2, color='blue'),
            hovertemplate="%{x}<br>%{y:.2f}<extra>"+name+"</extra>"
        ))
        
        # Traza para valores que superan el umbral (rojo)
        fig.add_trace(go.Scatter(
            x=x, y=y_over, mode="lines+markers",
            name=f"{name} (⚠️ Sobre umbral)", 
            line=dict(width=3, color='red'),
            marker=dict(size=6, color='red'),
            hovertemplate="%{x}<br>%{y:.2f} (ALERTA)<extra>"+name+"</extra>"
        ))
    else:
        # Traza normal sin umbral
        fig.add_trace(go.Scatter(
            x=x, y=y, mode="lines",
            name=name, line=dict(width=2),
            hovertemplate="%{x}<br>%{y:.2f}<extra>"+name+"</extra>"
        ))
    
    # Banda (desviación móvil) para simular área de variación
    if len(y) > 5:
        s = pd.Series(y).rolling(window=20, min_periods=1)
        y_low = s.mean() - s.std()
        y_high = s.mean() + s.std()
        fig.add_traces([
            go.Scatter(x=x, y=y_high, mode="lines", line=dict(width=0), showlegend=False, hoverinfo="skip"),
            go.Scatter(x=x, y=y_low, mode="lines", line=dict(width=0), fill="tonexty", 
                      name=f"{name} (±1σ)", fillcolor="rgba(128,128,128,0.1)", hoverinfo="skip")
        ])
    
    # Línea de umbral
    if threshold is not None:
        fig.add_hline(
            y=threshold, 
            line_dash="dash", 
            line_color="red",
            annotation_text=f"🚨 Umbral: {threshold}", 
            annotation_position="top left",
            annotation=dict(bgcolor="rgba(255,255,255,0.8)")
        )

    # sensible default margins if none provided
    if margin is None:
        margin = dict(l=40, r=20, t=40, b=40)

    fig.update_layout(
        margin=margin,
        height=height,
        xaxis_title=None,
        yaxis_title=yaxis_title,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        template="simple_white"
    )
    return fig

# ----- LAYOUT -----
# Gráficos organizados verticalmente, cada uno ocupando todo el ancho

# 1) Process Pressure
if "Process Pressure (Bar)" in df.columns:
    st.subheader("Process Pressure")
    fig = go.Figure()
    fig = line_area(fig, df[ts_col], df["Process Pressure (Bar)"], "Process Pressure", 
                   yaxis_title="bar", threshold=threshold_pressure, height=400)
    st.plotly_chart(fig, use_container_width=True)

# 2) Process Temperature
if "Process Temperature (°C)" in df.columns:
    st.subheader("Process Temperature")
    fig = go.Figure()
    fig = line_area(fig, df[ts_col], df["Process Temperature (°C)"], "Process Temperature", 
                   yaxis_title="°C", threshold=threshold_process_temp, height=400)
    st.plotly_chart(fig, use_container_width=True)

# 3) Surface Temperature
if "Surface Temperature (°C)" in df.columns:
    st.subheader("Surface Temperature")
    fig = go.Figure()
    fig = line_area(fig, df[ts_col], df["Surface Temperature (°C)"], "Surface Temperature", 
                   yaxis_title="°C", threshold=threshold_surface_temp, height=400)
    st.plotly_chart(fig, use_container_width=True)

# 4) Acceleration Peak
target_col = "Acceleration Peak (max axis)" if "Acceleration Peak (max axis)" in df.columns else (acc_cols[0] if acc_cols else None)
if target_col is not None:
    st.subheader("Acceleration Peak")
    fig = go.Figure()
    fig = line_area(fig, df[ts_col], df[target_col], "Acceleration Peak", 
                   yaxis_title="g", threshold=threshold_acceleration, height=400)
    st.plotly_chart(fig, use_container_width=True)

# 5) Velocity RMS (vector)
target_col = "Velocity RMS (vector)" if "Velocity RMS (vector)" in df.columns else (vel_cols[0] if vel_cols else None)
if target_col is not None:
    st.subheader("Velocity RMS")
    fig = go.Figure()
    fig = line_area(fig, df[ts_col], df[target_col], "Velocity RMS", 
                   yaxis_title="mm/s", threshold=threshold_velocity, height=400)
    st.plotly_chart(fig, use_container_width=True)

# Tabla de últimos valores
st.markdown("### Últimos valores")
tail_cols = [c for c in ["Process Pressure (Bar)", "Process Temperature (°C)", "Surface Temperature (°C)", "Velocity RMS (vector)", "Acceleration Peak (max axis)"] if c in df.columns]
st.dataframe(df[[ts_col]+tail_cols].tail(20).reset_index(drop=True))
