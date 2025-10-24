
# 🚀 Comparativo de Bombas

Aplicación web para análisis y comparación de datos de bombas industriales.

## 📋 Características

- **Dashboard Individual** (`dashboard_bomba04.py`): Análisis detallado de una bomba con umbrales configurables
- **Comparativo Múltiple** (`comparativo_bombas.py`): Comparación simultánea de múltiples bombas

## 🛠️ Instalación Local

```bash
pip install -r requirements.txt
```

## 🚀 Ejecutar Aplicaciones

### Dashboard Individual
```bash
streamlit run dashboard_bomba04.py
```

### Comparativo Múltiple  
```bash
streamlit run comparativo_bombas.py
```

## 📊 Formatos Soportados

- **Excel (.xlsx)**: Archivos de Excel con datos de sensores
- **CSV (.csv)**: Archivos CSV con separadores automáticos

## 🔧 Columnas Esperadas

- `Local TimeStamp` - Fecha y hora
- `Process Pressure (Bar)` - Presión del proceso
- `Process Temperature (°C)` - Temperatura del proceso  
- `Surface Temperature (°C)` - Temperatura de superficie
- `Velocity X/Y/Z (mm/s)` - Velocidades por eje
- `Acceleration X/Y/Z (g)` - Aceleraciones por eje

## 🌐 Despliegue

### Streamlit Community Cloud (Recomendado)
1. Sube el código a GitHub
2. Ve a [share.streamlit.io](https://share.streamlit.io/)
3. Conecta tu repositorio
4. ¡Listo!

### Vercel (Alternativo)
```bash
vercel --prod
```

## � Características Avanzadas

- **Normalización automática** de nombres de columnas
- **Detección inteligente** de codificación de archivos
- **Manejo de datos dispersos** vs continuos
- **Umbrales configurables** con alertas visuales
- **Exportación de KPIs** en CSV

