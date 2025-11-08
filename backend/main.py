from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware  # ← NUEVO
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import requests
from datetime import datetime, date

# Cargar variables del .env
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Inicializar FastAPI
app = FastAPI()

# ✅ CONFIGURACIÓN CORS - AGREGAR ESTO
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permitir todos los orígenes
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- MODELOS ----------
class AnalisisRequest(BaseModel):
    prompt: str
    fecha_inicio: str = None  # YYYY-MM-DD
    fecha_fin: str = None     # YYYY-MM-DD

# ---------- FUNCIONES ----------
def leer_json():
    try:
        with open("finanzas.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Archivo finanzas.json no encontrado")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Error al leer el archivo JSON")

def filtrar_por_fecha(movimientos, fecha_inicio=None, fecha_fin=None):
    filtrados = []
    fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if fecha_inicio else None
    fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if fecha_fin else None
    for m in movimientos:
        fecha_mov = datetime.strptime(m["fecha"], "%Y-%m-%d").date()
        if fecha_inicio_dt and fecha_mov < fecha_inicio_dt:
            continue
        if fecha_fin_dt and fecha_mov > fecha_fin_dt:
            continue
        filtrados.append(m)
    return filtrados

# ---------- ENDPOINTS ----------
@app.get("/balance")
def obtener_balance():
    data = leer_json()
    ingresos = sum(m["monto"] for m in data["movimientos"] if m["tipo"].lower() == "ingreso")
    gastos = sum(m["monto"] for m in data["movimientos"] if m["tipo"].lower() == "gasto")
    balance = ingresos - gastos
    return {"ingresos": ingresos, "gastos": gastos, "balance": balance}

@app.post("/analizar")
async def analizar_datos(request: AnalisisRequest):
    try:
        data = leer_json()
        prompt = request.prompt

        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"Analiza este JSON de finanzas y responde a la siguiente instrucción: {prompt}\n\n{json.dumps(data, ensure_ascii=False)}"
                        }
                    ]
                }
            ]
        }

        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            json=payload
        )

        if not response.ok:
            raise HTTPException(status_code=500, detail="Error en la API de Gemini")

        result = response.json()
        texto = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "No se recibió respuesta del modelo.")
        )

        return {"respuesta": texto}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/analizar_categorias")
async def analizar_categorias(request: AnalisisRequest):
    """Clasifica los movimientos en categorías y devuelve un JSON con totales, filtrando por fecha si se indica"""
    try:
        data = leer_json()
        # Filtrar por fechas opcionales
        movimientos_filtrados = filtrar_por_fecha(
            data["movimientos"],
            request.fecha_inicio,
            request.fecha_fin
        )
        data_filtrada = data.copy()
        data_filtrada["movimientos"] = movimientos_filtrados

        prompt = f"""
Eres un analista financiero. Clasifica los movimientos en categorías y devuelve un JSON válido
con esta estructura exacta, sin explicaciones: (En gastos Tiendita o parecidos van en comida)

{{
  "ingresos": {{
    "Sueldo": 0,
    "Monto inicial": 0,
    "Regalos": 0,
    "Prestamos recibidos": 0,
    "Ventas": 0,
    "Otros": 0
  }},
  "gastos": {{
    "Comida": 0,
    "Transporte": 0,
    "Telefonía": 0,
    "Entretenimiento": 0,
    "Gimnasio": 0,
    "Hogar": 0,
    "Tarjeta de Crédito": 0,
    "Otros": 0
  }},
  "totales": {{
    "total_ingresos": 0,
    "total_gastos": 0,
    "balance": 0
  }}
}}

Aquí están los movimientos a analizar:
{json.dumps(data_filtrada, ensure_ascii=False, indent=2)}
"""

        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"

        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            params={"key": GEMINI_API_KEY},
            json=payload
        )

        result = response.json()
        texto = (
            result.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        # Intentamos convertir a JSON
        try:
            categorias_json = json.loads(texto)
        except json.JSONDecodeError:
            inicio = texto.find("{")
            fin = texto.rfind("}") + 1
            categorias_json = json.loads(texto[inicio:fin])

        return categorias_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# main.py (agrega esto al final)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)