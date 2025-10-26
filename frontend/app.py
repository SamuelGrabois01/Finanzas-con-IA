import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
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
</style>
""", unsafe_allow_html=True)

# URL del backend
BACKEND_URL = "https://finanzas-con-ia.onrender.com"

def main():
    st.title("💰 Mis Finanzas")
    
    # Filtros de fecha
    col1, col2 = st.columns(2)
    with col1:
        fecha_inicio = st.date_input(
            "Desde",
            value=datetime.now().date() - timedelta(days=30)
        )
    with col2:
        fecha_fin = st.date_input(
            "Hasta", 
            value=datetime.now().date()
        )
    
    try:
        # Obtener balance general
        with st.spinner("Cargando datos..."):
            balance_response = requests.get(f"{BACKEND_URL}/balance")
            
            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                mostrar_metricas_principales(balance_data)
                
                # Obtener análisis por categorías
                categorias_response = requests.post(
                    f"{BACKEND_URL}/analizar_categorias",
                    json={
                        "fecha_inicio": str(fecha_inicio),
                        "fecha_fin": str(fecha_fin)
                    },
                    timeout=30
                )
                
                if categorias_response.status_code == 200:
                    categorias_data = categorias_response.json()
                    mostrar_graficas(categorias_data)
                else:
                    st.warning("⚠️ Las gráficas no están disponibles temporalmente")
                    mostrar_datos_ejemplo()
                    
            else:
                st.error("Error al cargar datos básicos")
                
    except requests.exceptions.ConnectionError:
        st.error("⚠️ No se puede conectar al backend.")
    except Exception as e:
        st.error(f"Error: {str(e)}")
        mostrar_datos_ejemplo()

def mostrar_datos_ejemplo():
    """Mostrar datos de ejemplo cuando falla la conexión"""
    st.info("💡 Mostrando datos de ejemplo:")
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
        st.metric("Ingresos", f"${balance_data['ingresos']:,.0f}")
    with col2:
        st.metric("Gastos", f"${balance_data['gastos']:,.0f}")
    with col3:
        balance = balance_data['balance']
        st.metric("Balance", f"${balance:,.0f}", 
                 delta_color="normal" if balance >= 0 else "inverse")

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
        fig = go.Figure(data=[go.Pie(
            labels=['Ingresos', 'Gastos'],
            values=[data['totales']['total_ingresos'], data['totales']['total_gastos']],
            hole=0.4
        )])
        fig.update_layout(title_text="Ingresos vs Gastos")
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Top categorías de gastos (sin pandas)
        gastos_items = [(k, v) for k, v in data['gastos'].items() if v > 0]
        gastos_items.sort(key=lambda x: x[1], reverse=True)
        
        if gastos_items:
            categorias = [item[0] for item in gastos_items[:5]]
            montos = [item[1] for item in gastos_items[:5]]
            
            fig = go.Figure(data=[go.Bar(x=categorias, y=montos)])
            fig.update_layout(title_text="Top 5 Gastos")
            st.plotly_chart(fig, use_container_width=True)

def mostrar_ingresos(data):
    ingresos_items = [(k, v) for k, v in data['ingresos'].items() if v > 0]
    
    if ingresos_items:
        col1, col2 = st.columns(2)
        
        with col1:
            categorias = [item[0] for item in ingresos_items]
            montos = [item[1] for item in ingresos_items]
            
            fig = go.Figure(data=[go.Pie(labels=categorias, values=montos)])
            fig.update_layout(title_text="Distribución de Ingresos")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[go.Bar(x=categorias, y=montos)])
            fig.update_layout(title_text="Ingresos por Categoría")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay ingresos en el período seleccionado")

def mostrar_gastos(data):
    gastos_items = [(k, v) for k, v in data['gastos'].items() if v > 0]
    
    if gastos_items:
        col1, col2 = st.columns(2)
        
        with col1:
            categorias = [item[0] for item in gastos_items]
            montos = [item[1] for item in gastos_items]
            
            fig = go.Figure(data=[go.Pie(labels=categorias, values=montos)])
            fig.update_layout(title_text="Distribución de Gastos")
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = go.Figure(data=[go.Bar(x=categorias, y=montos)])
            fig.update_layout(title_text="Gastos por Categoría")
            st.plotly_chart(fig, use_container_width=True)
        
        # Tabla detallada (sin pandas)
        st.subheader("Detalle de Gastos")
        gastos_items.sort(key=lambda x: x[1], reverse=True)
        
        # Mostrar como tabla simple
        for categoria, monto in gastos_items:
            st.write(f"**{categoria}:** ${monto:,.0f}")
    else:
        st.info("No hay gastos en el período seleccionado")

if __name__ == "__main__":
    main()
