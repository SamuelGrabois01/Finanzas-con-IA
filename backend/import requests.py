import requests
import os

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

response = requests.get(
    "https://generativelanguage.googleapis.com/v1/models",
    params={"key": GEMINI_API_KEY}
)

print(response.status_code)
print(response.json())