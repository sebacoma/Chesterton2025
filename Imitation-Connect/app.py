from flask import Flask, render_template_string, jsonify
import os

app = Flask(__name__)

# HTML template mejorado
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🚀 Comparativo de Bombas - Análisis Industrial</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; min-height: 100vh; padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; text-align: center; }
        .hero { margin: 50px 0; }
        .hero h1 { font-size: 3rem; margin-bottom: 20px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .hero p { font-size: 1.2rem; opacity: 0.9; margin-bottom: 40px; }
        .apps-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin: 50px 0; }
        .app-card { 
            background: rgba(255,255,255,0.1); backdrop-filter: blur(10px);
            border-radius: 15px; padding: 30px; border: 1px solid rgba(255,255,255,0.2);
            transition: transform 0.3s ease;
        }
        .app-card:hover { transform: translateY(-5px); }
        .app-card h3 { font-size: 1.5rem; margin-bottom: 15px; }
        .app-card p { margin-bottom: 20px; opacity: 0.9; }
        .btn { 
            display: inline-block; padding: 12px 30px; background: #ff6b6b;
            color: white; text-decoration: none; border-radius: 25px;
            font-weight: bold; transition: all 0.3s ease;
        }
        .btn:hover { background: #ff5252; transform: scale(1.05); }
        .features { margin-top: 50px; }
        .features h2 { margin-bottom: 30px; }
        .feature-list { 
            display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
            gap: 20px; margin-top: 30px;
        }
        .feature { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="hero">
            <h1>🚀 Comparativo de Bombas</h1>
            <p>Análisis avanzado de datos de bombas industriales con visualización interactiva</p>
        </div>
        
        <div class="apps-grid">
            <div class="app-card">
                <h3>📊 Dashboard Individual</h3>
                <p>Análisis detallado de una bomba con umbrales configurables, alertas visuales y métricas en tiempo real.</p>
                <a href="https://share.streamlit.io/" class="btn" target="_blank">Desplegar Dashboard →</a>
                <p><small>Archivo: dashboard_bomba04.py</small></p>
            </div>
            
            <div class="app-card">
                <h3>🔄 Comparativo Múltiple</h3>
                <p>Comparación simultánea de múltiples bombas con normalización automática y análisis temporal.</p>
                <a href="https://share.streamlit.io/" class="btn" target="_blank">Desplegar Comparativo →</a>
                <p><small>Archivo: comparativo_bombas.py</small></p>
            </div>
        </div>
        
        <div class="features">
            <h2>✨ Características Principales</h2>
            <div class="feature-list">
                <div class="feature">
                    <h4>📈 Visualización Avanzada</h4>
                    <p>Gráficos interactivos con Plotly, umbrales configurables y alertas visuales</p>
                </div>
                <div class="feature">
                    <h4>🔧 Procesamiento Inteligente</h4>
                    <p>Normalización automática de columnas, detección de codificación y manejo de datos dispersos</p>
                </div>
                <div class="feature">
                    <h4>📊 Formatos Multiple</h4>
                    <p>Soporte para Excel (.xlsx) y CSV con detección automática de separadores</p>
                </div>
                <div class="feature">
                    <h4>🚨 Sistema de Alertas</h4>
                    <p>Umbrales personalizables con código de colores y notificaciones visuales</p>
                </div>
            </div>
        </div>
        
        <div style="margin-top: 50px; padding: 30px; background: rgba(255,255,255,0.1); border-radius: 15px;">
            <h3>🚀 Cómo Desplegar</h3>
            <p>1. Ve a <strong>Streamlit Community Cloud</strong></p>
            <p>2. Conecta el repositorio: <strong>sebacoma/Chesterton2025</strong></p>
            <p>3. Selecciona el archivo principal según la aplicación que quieras desplegar</p>
            <p>4. ¡Disfruta tu aplicación desplegada!</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return HTML_TEMPLATE

@app.route('/health')
def health():
    return jsonify({"status": "ok", "message": "Comparativo Bombas Landing Page"})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))