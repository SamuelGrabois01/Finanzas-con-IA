from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()

# 👇 Modelo del cuerpo JSON
class AnalisisRequest(BaseModel):
    prompt: str

@app.post("/analizar")
async def analizar_datos(request: AnalisisRequest):
    prompt = request.prompt
    print(f"📩 Prompt recibido: {prompt}")

    # Aquí haces la llamada a Gemini o lo que necesites
    return {"respuesta": f"Procesé el prompt: {prompt}"}