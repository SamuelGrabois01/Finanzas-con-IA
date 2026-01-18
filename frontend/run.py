import subprocess
import sys

# Instalar dependencias si no están
try:
    import streamlit
    import plotly
    import pandas
    print("✅ Todas las dependencias están instaladas")
except ImportError as e:
    print(f"❌ Faltan dependencias: {e}")
    print("Instalando...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "plotly", "pandas", "requests"])
    print("✅ Dependencias instaladas")

# Ejecutar la app
print("🚀 Iniciando aplicación Streamlit...")
subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])