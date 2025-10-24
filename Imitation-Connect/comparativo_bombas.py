
import os
import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

st.set_page_config(page_title="Comparativo Bombas", layout="wide")
st.title("🔁 Comparativo de Bombas / Sensores")
st.caption("Carga 2+ archivos (CSV/Excel) con columnas estándar: Local TimeStamp, Pressure, Temperatures, Velocity X/Y/Z (mm/s), Acceleration X/Y/Z (g).")

# --- Helpers ---
def sniff_sep_and_enc(path_or_buf):
    # Returns sep, encoding
    # If buffer-like, read bytes
    if isinstance(path_or_buf, (str, os.PathLike)):
        with open(path_or_buf, "rb") as f:
            raw = f.read(8192)  # Read more bytes for better detection
    else:
        raw = path_or_buf.getvalue()
    
    # Extended list of encodings to try, including Windows and ISO variants
    encodings = [
        "utf-8", "utf-8-sig",  # UTF-8 with and without BOM
        "latin1", "iso-8859-1",  # Western European
        "cp1252", "windows-1252",  # Windows Western European
        "cp850", "cp437",  # DOS code pages
        "iso-8859-15",  # Western European with Euro symbol
        "utf-16", "utf-16le", "utf-16be"  # Unicode variants
    ]
    
    for enc in encodings:
        try:
            # Try to decode the sample
            sample = raw.decode(enc, errors="strict")
            # Detect separator
            semicolon_count = sample.count(";")
            comma_count = sample.count(",")
            tab_count = sample.count("\t")
            
            # Choose the most frequent delimiter
            if tab_count > max(semicolon_count, comma_count):
                sep = "\t"
            elif semicolon_count > comma_count:
                sep = ";"
            else:
                sep = ","
            
            return sep, enc
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue
    
    # If all fail, try with error handling
    try:
        sample = raw.decode("utf-8", errors="replace")
        sep = ";" if sample.count(";") > sample.count(",") else ","
        return sep, "utf-8"
    except:
        return ",", "utf-8"

def to_float_series(s):
    return pd.to_numeric(
        s.astype(str).str.replace(",", ".", regex=False).str.replace(" ", "", regex=False),
        errors="coerce"
    )

def normalize_column_names(df):
    """Normaliza nombres de columnas para que coincidan entre diferentes archivos"""
    column_mapping = {
        # Presión
        'Process Pres': 'Process Pressure (Bar)',
        'Process Pressure': 'Process Pressure (Bar)',
        'Pressure': 'Process Pressure (Bar)',
        'Pres': 'Process Pressure (Bar)',
        
        # Temperatura de proceso
        'Process Temp': 'Process Temperature (°C)',
        'Process Temperature': 'Process Temperature (°C)',
        'Temp': 'Process Temperature (°C)',
        
        # Temperatura de superficie - ya está bien
        'Surface Temperature (°C)': 'Surface Temperature (°C)',
        'Surface Temp': 'Surface Temperature (°C)',
        
        # Velocidades
        'Velocity X (mm/s)': 'Velocity X (mm/s)',
        'Velocity Y (mm/s)': 'Velocity Y (mm/s)',
        'Velocity Z (mm/s)': 'Velocity Z (mm/s)',
        'VelX': 'Velocity X (mm/s)',
        'VelY': 'Velocity Y (mm/s)',
        'VelZ': 'Velocity Z (mm/s)',
        
        # Aceleraciones
        'Acceleration X (g)': 'Acceleration X (g)',
        'Acceleration Y (g)': 'Acceleration Y (g)', 
        'Acceleration Z (g)': 'Acceleration Z (g)',
        'AccX': 'Acceleration X (g)',
        'AccY': 'Acceleration Y (g)',
        'AccZ': 'Acceleration Z (g)',
    }
    
    # Crear nuevo DataFrame con nombres normalizados
    df_normalized = df.copy()
    df_normalized = df_normalized.rename(columns=column_mapping)
    
    return df_normalized

def load_any(file, label_hint=None):
    name = getattr(file, "name", str(file))
    label = label_hint or name.rsplit("/",1)[-1]
    
    try:
        if isinstance(file, (str, os.PathLike)):
            if name.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(file, sheet_name=0)
            else:
                sep, enc = sniff_sep_and_enc(file)
                # Try multiple read attempts with different parameters
                try:
                    df = pd.read_csv(file, sep=sep, encoding=enc, engine="python")
                except UnicodeDecodeError:
                    # Fallback: try with error handling
                    df = pd.read_csv(file, sep=sep, encoding=enc, engine="python", encoding_errors="replace")
        else:
            # uploaded file
            if name.lower().endswith((".xlsx", ".xls")):
                df = pd.read_excel(file)
            else:
                sep, enc = sniff_sep_and_enc(file)
                try:
                    df = pd.read_csv(file, sep=sep, encoding=enc, engine="python")
                except UnicodeDecodeError:
                    # Reset file pointer and try with error handling
                    file.seek(0)
                    df = pd.read_csv(file, sep=sep, encoding=enc, engine="python", encoding_errors="replace")
    
    except Exception as e:
        st.error(f"Error cargando archivo {name}: {str(e)}")
        st.info(f"Intenta convertir el archivo a UTF-8 o usar un formato diferente.")
        raise
    
    # Normalize columns
    df.columns = [c.strip() for c in df.columns]
    ts_col = "Local TimeStamp" if "Local TimeStamp" in df.columns else df.columns[0]
    df[ts_col] = pd.to_datetime(df[ts_col], dayfirst=True, errors="coerce")
    
    # Normalizar nombres de columnas antes del procesamiento numérico
    df = normalize_column_names(df)
    
    for c in df.columns:
        if c == ts_col: continue
        df[c] = to_float_series(df[c])
    df = df.dropna(subset=[ts_col]).sort_values(ts_col)
    return df, ts_col, label

# --- Sidebar Inputs ---
st.sidebar.header("📁 Archivos")
uploads = st.sidebar.file_uploader("Sube CSV/XLSX (múltiples)", type=["csv","xlsx"], accept_multiple_files=True)

# Sugerir archivos locales (si existen en la carpeta del entorno)
defaults = []
for cand in ["Bomba 04.csv", "01001AD9.csv", "P1222 2S.csv", "Bomba 04-Data.xlsx"]:
    if os.path.exists(cand): defaults.append(cand)

use_defaults = st.sidebar.checkbox("Usar archivos locales detectados", value=True if defaults else False)
selected_defaults = []
if use_defaults and defaults:
    selected_defaults = st.sidebar.multiselect("Selecciona locales", defaults, default=defaults)

# Opciones de procesamiento
st.sidebar.header("🧪 Procesamiento")
resample_rule = st.sidebar.selectbox("Resampling (opcional)", ["None","15min","30min","1H","4H","1D"], index=0)
if resample_rule != "None":
    st.sidebar.warning("⚠️ Resampling puede crear puntos artificiales en datos dispersos")
    
norm = st.sidebar.selectbox("Normalización", ["ninguna","min-max (0-1)","z-score (media 0, σ1)"], index=0)

# Opción para manejo de datos dispersos
show_gaps_info = st.sidebar.checkbox("Mostrar información de gaps temporales", value=True)

# Cargar datasets
datasets = []
if uploads:
    for f in uploads:
        try:
            # Show file info for debugging
            file_info = f"Cargando: {f.name}"
            if not f.name.lower().endswith((".xlsx", ".xls")):
                sep, enc = sniff_sep_and_enc(f)
                file_info += f" (separador: '{sep}', codificación: {enc})"
            st.sidebar.info(file_info)
            
            df, ts_col, label = load_any(f)
            datasets.append((label, df, ts_col))
            st.sidebar.success(f"✅ {label}: {len(df)} filas")
            st.sidebar.caption(f"Columnas normalizadas: {', '.join([c for c in df.columns if c != ts_col][:4])}{'...' if len(df.columns) > 5 else ''}")
        except Exception as e:
            st.sidebar.error(f"❌ Error en {f.name}: {str(e)}")
            
if selected_defaults:
    for path in selected_defaults:
        try:
            # Show file info for debugging
            file_info = f"Cargando: {os.path.basename(path)}"
            if not path.lower().endswith((".xlsx", ".xls")):
                sep, enc = sniff_sep_and_enc(path)
                file_info += f" (separador: '{sep}', codificación: {enc})"
            st.sidebar.info(file_info)
            
            df, ts_col, label = load_any(path, label_hint=os.path.basename(path))
            datasets.append((label, df, ts_col))
            st.sidebar.success(f"✅ {label}: {len(df)} filas")
            st.sidebar.caption(f"Columnas normalizadas: {', '.join([c for c in df.columns if c != ts_col][:4])}{'...' if len(df.columns) > 5 else ''}")
        except Exception as e:
            st.sidebar.error(f"❌ Error en {path}: {str(e)}")

if len(datasets) < 2:
    st.info("Carga al menos **dos** archivos para comparar.")
    st.stop()

# Verificar que todos los datasets tienen datos válidos
valid_datasets = [(label, df, ts) for label, df, ts in datasets if len(df) > 0]
if len(valid_datasets) < len(datasets):
    st.warning(f"Se descartaron {len(datasets) - len(valid_datasets)} archivos sin datos válidos.")
datasets = valid_datasets

if len(datasets) < 2:
    st.error("No hay suficientes archivos con datos válidos para comparar.")
    st.stop()

# Intersección de rango temporal y columnas
all_cols = set()
for _, df, ts in datasets:
    all_cols |= set(df.columns) - {ts}

# Mostrar todas las columnas disponibles por archivo
with st.expander("🔍 Ver todas las columnas por archivo"):
    for label, df, ts in datasets:
        st.write(f"**{label}**:")
        cols = [col for col in df.columns if col != ts]
        st.write(", ".join(cols))
        st.write("---")

metrics = st.multiselect(
    "Selecciona métricas a comparar (líneas superpuestas)",
    options=sorted(all_cols),
    default=[c for c in ["Process Pressure (Bar)","Process Temperature (°C)","Surface Temperature (°C)","Velocity X (mm/s)","Velocity Y (mm/s)","Velocity Z (mm/s)","Acceleration X (g)","Acceleration Y (g)","Acceleration Z (g)"] if c in all_cols][:3]
)

# Mostrar rangos temporales individuales ANTES de la intersección
st.write("### 📅 Análisis Temporal por Dataset")
for label, df, ts in datasets:
    min_date = df[ts].min()
    max_date = df[ts].max()
    duration = max_date - min_date
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.write(f"**{label}**:")
        st.write(f"  - Período: {min_date.strftime('%Y-%m-%d %H:%M')} → {max_date.strftime('%Y-%m-%d %H:%M')}")
        st.write(f"  - Duración: {duration}")
        st.write(f"  - Total puntos: {len(df)}")
        
    with col2:
        # Mostrar distribución de fechas únicas por día
        daily_counts = df.groupby(df[ts].dt.date).size()
        st.write(f"Días con datos: {len(daily_counts)}")
        if len(daily_counts) > 0:
            st.write(f"Promedio puntos/día: {daily_counts.mean():.1f}")
        st.write("---")

# Rango de fechas global (intersección)
min_dt = max([df[ts].min() for _, df, ts in datasets])
max_dt = min([df[ts].max() for _, df, ts in datasets])

st.write(f"**Intersección temporal**: {min_dt} → {max_dt}")

# Convert pandas.Timestamp to Python datetime for st.slider compatibility
min_dt = min_dt.to_pydatetime() if hasattr(min_dt, 'to_pydatetime') else min_dt
max_dt = max_dt.to_pydatetime() if hasattr(max_dt, 'to_pydatetime') else max_dt

# Ofrecer opción de usar rango extendido en lugar de intersección
use_extended_range = st.checkbox("Usar rango extendido (unión en lugar de intersección)", value=False)

if use_extended_range:
    # Usar rango completo (unión)
    min_dt_extended = min([df[ts].min() for _, df, ts in datasets])
    max_dt_extended = max([df[ts].max() for _, df, ts in datasets])
    min_dt = min_dt_extended.to_pydatetime() if hasattr(min_dt_extended, 'to_pydatetime') else min_dt_extended
    max_dt = max_dt_extended.to_pydatetime() if hasattr(max_dt_extended, 'to_pydatetime') else max_dt_extended
    st.info(f"Usando rango extendido: {min_dt} → {max_dt}")

start, end = st.slider("Rango temporal", min_value=min_dt, max_value=max_dt, value=(min_dt, max_dt))

def prep(df, ts_col):
    original_count = len(df)
    
    # Convert datetime back to pandas timestamp for filtering
    start_ts = pd.Timestamp(start)
    end_ts = pd.Timestamp(end)
    out = df[(df[ts_col] >= start_ts) & (df[ts_col] <= end_ts)].copy()
    
    # Debug: mostrar pérdida de datos por filtro temporal
    after_filter_count = len(out)
    if after_filter_count != original_count:
        st.sidebar.write(f"  - Filtro temporal: {original_count} → {after_filter_count} puntos")
    
    out = out.set_index(ts_col)
    
    # Solo aplicar resampling si hay suficientes datos y está configurado
    if resample_rule != "None" and len(out) > 10:
        before_resample = len(out)
        # Usar dropna() para evitar rellenar con NaN y crear puntos artificiales
        out = out.resample(resample_rule).mean().dropna(how='all')
        after_resample = len(out)
        if after_resample != before_resample:
            st.sidebar.write(f"  - Resampling {resample_rule}: {before_resample} → {after_resample} puntos")
    elif resample_rule != "None" and len(out) <= 10:
        st.sidebar.warning(f"  - Resampling omitido: muy pocos datos ({len(out)} puntos)")
    
    return out

prepared = [(label, prep(df, ts)) for (label, df, ts) in datasets]

# Mostrar información de debug
st.sidebar.header("📊 Información Después del Filtrado")
for label, dfi in prepared:
    st.sidebar.write(f"**{label}**:")
    st.sidebar.write(f"  - Filas después del filtro: {len(dfi)}")
    
    if len(dfi) > 0:
        st.sidebar.write(f"  - Rango temporal final: {dfi.index.min()} a {dfi.index.max()}")
        
        # Safe frequency inference - needs at least 3 dates
        if len(dfi) >= 3:
            try:
                freq = pd.infer_freq(dfi.index) or 'Irregular'
                st.sidebar.write(f"  - Frecuencia aproximada: {freq}")
            except:
                st.sidebar.write(f"  - Frecuencia aproximada: No determinable")
        else:
            st.sidebar.write(f"  - Frecuencia aproximada: Insuficientes puntos para determinar")
    
    available_metrics = [m for m in metrics if m in dfi.columns and not dfi[m].isna().all()]
    st.sidebar.write(f"  - Métricas válidas: {len(available_metrics)}")
    
    # Advertencia si muy pocos puntos
    if 0 < len(dfi) <= 5:
        st.sidebar.warning(f"⚠️ Solo {len(dfi)} puntos - considera cambiar el rango temporal o resampling")
    elif len(dfi) == 0:
        st.sidebar.error("❌ Sin datos en el rango seleccionado")
    
    st.sidebar.write("---")

# Normalización por-métrica por-dataset
def normalize(series, mode):
    if mode == "min-max (0-1)":
        mn, mx = series.min(), series.max()
        return (series - mn) / (mx - mn) if pd.notna(mx) and mx != mn else series*0
    if mode == "z-score (media 0, σ1)":
        mu, sd = series.mean(), series.std()
        return (series - mu) / sd if sd and not np.isnan(sd) and sd != 0 else series*0
    return series

# Render: un gráfico por métrica con todas las bombas como líneas
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

for metric in metrics:
    fig = go.Figure()
    lines_added = 0
    
    for i, (label, dfi) in enumerate(prepared):
        if metric in dfi.columns:
            y = normalize(dfi[metric], norm)
            
            # Skip if all values are NaN
            if y.isna().all():
                continue
                
            # Detectar si los datos son continuos o dispersos
            time_diffs = dfi.index.to_series().diff().dt.total_seconds()
            median_diff = time_diffs.median()
            large_gaps = time_diffs > median_diff * 5  # Gaps 5x más grandes que la mediana
            
            if large_gaps.sum() > len(dfi) * 0.3:  # Si más del 30% son gaps grandes
                # Datos dispersos - solo marcadores
                mode = "markers"
                line_dict = dict(width=0)
                marker_dict = dict(size=8, color=colors[i % len(colors)], opacity=0.8)
                st.sidebar.info(f"  - {label}: Datos dispersos, mostrando solo puntos")
            else:
                # Datos continuos - líneas + marcadores pequeños
                mode = "lines+markers"
                line_dict = dict(width=2.5, color=colors[i % len(colors)])
                marker_dict = dict(size=4, opacity=0.7)
                st.sidebar.info(f"  - {label}: Datos continuos, mostrando líneas")
            
            fig.add_trace(go.Scatter(
                x=dfi.index, 
                y=y, 
                mode=mode, 
                name=label,
                line=line_dict,
                marker=marker_dict,
                connectgaps=False,  # No conectar a través de gaps grandes
                hovertemplate=f"<b>{label}</b><br>%{{x}}<br>%{{y:.3f}}<extra></extra>"
            ))
            lines_added += 1
    
    if lines_added == 0:
        st.warning(f"No hay datos válidos para la métrica '{metric}'")
        continue
        
    ytitle = metric + ("" if norm=="ninguna" else f" · {norm}")
    fig.update_layout(
        title=f"{metric} - Comparativo ({lines_added} datasets)",
        height=400,
        margin=dict(l=40,r=20,t=50,b=40),
        xaxis_title="Tiempo",
        yaxis_title=ytitle,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=1.02, 
            xanchor="center", 
            x=0.5
        ),
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# KPIs comparativos (último valor visible)
st.markdown("### 📊 KPIs comparativos (última muestra del rango)")
rows = []
for label, dfi in prepared:
    last = dfi.iloc[-1] if len(dfi) else None
    if last is None: continue
    row = {"Dataset": label, "Timestamp": dfi.index[-1]}
    for metric in metrics:
        if metric in dfi.columns:
            row[metric] = float(last[metric])
    rows.append(row)

if rows:
    kpi_df = pd.DataFrame(rows)
    st.dataframe(kpi_df, use_container_width=True)

# Export
st.download_button(
    "⬇️ Exportar KPIs CSV",
    data=kpi_df.to_csv(index=False).encode("utf-8"),
    file_name="comparativo_kpis.csv",
    mime="text/csv"
)

