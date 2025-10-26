import streamlit as st
import requests
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os

# Configuración para móvil
st.set_page_config(
    page_title="Mis Finanzas",
    page_icon="💰",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# CSS mejorado para móvil
st.markdown("""
<style>
    .main > div {
        padding: 1rem;
    }
    @media (max-width: 768px) {
        .main > div {
            padding: 0.5rem;
        }
        .stButton > button {
            font-size: 16px;
            height: 3em;
        }
        .metric {
            font-size: 14px;
        }
    }
    .balance-positive {
        color: #00cc00;
        font-weight: bold;
    }
    .balance-negative {
        color: #ff4b4b;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# URL del backend - IMPORTANTE: verificar que sea correcta
BACKEND_URL = "http://localhost:8000"

def main():
    st.title("💰 Mis Finanzas")
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Desde",
            value=datetime.now().date() - timedelta(days=30),
            key="fecha_inicio"
        )
    with col2:
        fecha_fin = st.date_input(
            "Hasta", 
            value=datetime.now().date(),
            key="fecha_fin"
        )
    
    try:
        # Obtener balance general
        with st.spinner("Cargando datos..."):
            balance_response = requests.get(f"{BACKEND_URL}/balance")
            
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                mostrar_metricas_principales(balance_data)
                
                # Obtener análisis por categorías - VERSIÓN CORREGIDA
                categorias_response = requests.post(
                    f"{BACKEND_URL}/analizar_categorias",
                    json={
                        "fecha_inicio": str(fecha_inicio),
                        "fecha_fin": str(fecha_fin),
                        "prompt": ""  # Agregar prompt vacío si es requerido
                    },
                    timeout=30  # Dar más tiempo para la IA
                )
                
                if categorias_response.status_code == 200:
                    categorias_data = categorias_response.json()
                    mostrar_graficas(categorias_data)
                else:
                    st.warning("⏳ Las categorías pueden tardar un momento...")
                    # Mostrar datos de ejemplo temporalmente
                    mostrar_datos_ejemplo()
                    
            else:
                st.error("Error al cargar datos básicos del balance")
                
    except requests.exceptions.ConnectionError:
        st.error("⚠️ No se puede conectar al backend. Verifica que esté ejecutándose en http://localhost:8000")
    except requests.exceptions.Timeout:
        st.warning("⏰ El análisis de categorías está tardando más de lo esperado. Recarga la página.")
        mostrar_datos_ejemplo()
    except Exception as e:
        st.error(f"Error inesperado: {str(e)}")
        mostrar_datos_ejemplo()

def mostrar_datos_ejemplo():
    """Mostrar datos de ejemplo cuando el análisis de IA falla"""
    st.info("💡 Mientras tanto, aquí tienes un resumen básico:")
    
    # Datos de ejemplo para que la app no se vea vacía
    datos_ejemplo = {
        "ingresos": {
            "Sueldo": 2500,
            "Freelance": 500,
            "Otros": 100
        },
        "gastos": {
            "Comida": 300,
            "Transporte": 150,
            "Entretenimiento": 100,
            "Otros": 200
        },
        "totales": {
            "total_ingresos": 3100,
            "total_gastos": 750,
            "balance": 2350
        }
    }
    mostrar_graficas(datos_ejemplo)

def mostrar_metricas_principales(balance_data):
    st.subheader("Resumen General")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="Ingresos", 
            value=f"${balance_data['ingresos']:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Gastos", 
            value=f"${balance_data['gastos']:,.0f}",
            delta=None
        )
    
    with col3:
        balance = balance_data['balance']
        st.metric(
            label="Balance", 
            value=f"${balance:,.0f}",
            delta=f"{balance:,.0f}",
            delta_color="normal" if balance >= 0 else "inverse"
        )

def mostrar_graficas(categorias_data):
    tab1, tab2, tab3 = st.tabs(["📊 Resumen", "📈 Ingresos", "📉 Gastos"])
    
    with tab1:
        mostrar_resumen(categorias_data)
    
    with tab2:
        mostrar_ingresos(categorias_data)
    
    with tab3:
        mostrar_gastos(categorias_data)

def mostrar_resumen(data):
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de ingresos vs gastos
        fig = px.pie(
            names=['Ingresos', 'Gastos'],
            values=[data['totales']['total_ingresos'], data['totales']['total_gastos']],
            title="Ingresos vs Gastos",
            hole=0.4
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top categorías de gastos
        gastos_df = pd.DataFrame(list(data['gastos'].items()), columns=['Categoría', 'Monto'])
        gastos_df = gastos_df[gastos_df['Monto'] > 0].sort_values('Monto', ascending=False)
        
        if not gastos_df.empty:
            fig = px.bar(
                gastos_df.head(5), 
                x='Categoría', 
                y='Monto',
                title="Top 5 Gastos"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de gastos")

def mostrar_ingresos(data):
    ingresos_df = pd.DataFrame(list(data['ingresos'].items()), columns=['Categoría', 'Monto'])
    ingresos_df = ingresos_df[ingresos_df['Monto'] > 0]
    
    if not ingresos_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(ingresos_df, values='Monto', names='Categoría', 
                         title="Distribución de Ingresos")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(ingresos_df, x='Categoría', y='Monto', 
                        title="Ingresos por Categoría")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay ingresos en el período seleccionado")

def mostrar_gastos(data):
    gastos_df = pd.DataFrame(list(data['gastos'].items()), columns=['Categoría', 'Monto'])
    gastos_df = gastos_df[gastos_df['Monto'] > 0]
    
    if not gastos_df.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(gastos_df, values='Monto', names='Categoría', 
                         title="Distribución de Gastos")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.bar(gastos_df, x='Categoría', y='Monto', 
                        title="Gastos por Categoría")
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada
        st.subheader("Detalle de Gastos")
        gastos_df = gastos_df.sort_values('Monto', ascending=False)
        st.dataframe(gastos_df, use_container_width=True)
    else:
        st.info("No hay gastos en el período seleccionado")

if __name__ == "__main__":
    main()