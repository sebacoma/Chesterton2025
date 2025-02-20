import streamlit as st
import pandas as pd
import numpy as np
import os

# Título de la app en Streamlit
st.write("""
# Reporte de Sellos Mecánicos SQM
""")

# Nombre del archivo de datos locales
file_name = "GOOGL_historical_data.csv"

# Comprobar si el archivo de datos existe
if os.path.exists(file_name):
    st.write("📂 Cargando datos desde archivo local...")
    tickerDf = pd.read_csv(file_name, index_col=0, parse_dates=True)
else:
    st.write("⚠️ No se encontró un archivo de datos. Generando datos ficticios...")
    
    # Crear datos sintéticos para simular precios históricos
    rng = pd.date_range(start="2010-05-31", end="2020-05-31", freq='D')
    close_prices = np.cumsum(np.random.randn(len(rng)) * 2 + 1000)  # Simulación de precios
    volumes = np.random.randint(100000, 5000000, size=len(rng))  # Simulación de volumen

    tickerDf = pd.DataFrame({"Close": close_prices, "Volume": volumes}, index=rng)

    # Guardar en CSV para futuras ejecuciones
    tickerDf.to_csv(file_name)
    st.write("✅ Datos generados y guardados en:", file_name)

# Mostrar los gráficos en Streamlit
st.write("### Precio de Cierre")
st.line_chart(tickerDf['Close'])

st.write("### Volumen de Operaciones")
st.line_chart(tickerDf['Volume'])
