from flask import Flask, render_template_string
import subprocess
import threading
import time
import requests
import os

app = Flask(__name__)

# HTML template que embebe la app de Streamlit
IFRAME_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Comparativo Bombas</title>
    <style>
        body { margin: 0; padding: 0; }
        iframe { width: 100vw; height: 100vh; border: none; }
    </style>
</head>
<body>
    <iframe src="https://{{ streamlit_url }}" frameborder="0"></iframe>
</body>
</html>
"""

@app.route('/')
def index():
    return """
    <h1>🚀 Comparativo de Bombas</h1>
    <p>Esta aplicación se ejecuta mejor en Streamlit Community Cloud.</p>
    <p><a href="https://share.streamlit.io/" target="_blank">Desplegar en Streamlit Cloud →</a></p>
    <h2>Archivos de tu proyecto:</h2>
    <ul>
        <li>dashboard_bomba04.py - Dashboard individual</li>
        <li>comparativo_bombas.py - Comparativo múltiple</li>
    </ul>
    <p>Sube estos archivos a GitHub y conecta con Streamlit Cloud para el mejor rendimiento.</p>
    """

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))