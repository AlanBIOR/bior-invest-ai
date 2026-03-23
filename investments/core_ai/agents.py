import os
from google import genai  # <-- CAMBIO: Nueva librería oficial 2026
from dotenv import load_dotenv

load_dotenv()

# 1. Configuración del Cliente
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("¡Falta la GEMINI_API_KEY en el archivo .env!")

# Inicializamos el cliente moderno
client = genai.Client(api_key=GEMINI_API_KEY)

def ask_financial_agent(user_question, portfolio_context):
    """Envía la pregunta y el contexto usando el SDK moderno."""
    
    prompt_completo = f"{portfolio_context}\n\nPregunta del usuario por chat: {user_question}"
    
    try:
        # 2. Llamada al modelo 2.5-flash (el que confirmamos en tu lista)
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt_completo
        )
        
        return response.text
        
    except Exception as e:
        print(f"Error crítico en Gemini API: {e}")
        return "Disculpa, el asesor de BIOR Invest AI está experimentando interrupciones técnicas. Por favor, intenta de nuevo en un momento."