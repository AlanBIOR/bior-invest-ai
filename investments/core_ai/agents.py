import os
from dotenv import load_dotenv  # <-- LÍNEA NUEVA 1
import google.generativeai as genai

# Cargar las variables del archivo .env a nuestro entorno
load_dotenv()  # <-- LÍNEA NUEVA 2

# 1. Configuración de la API Key
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("¡Falta la GEMINI_API_KEY en el archivo .env!")

# Inicializamos la configuración de Google
genai.configure(api_key=GEMINI_API_KEY)

def ask_financial_agent(user_question, portfolio_context):
    """Envía la pregunta del usuario y su contexto financiero a la API de Gemini."""
    
    # Unimos tu mega-prompt (el contexto fiscal y financiero) con la pregunta del usuario
    prompt_completo = f"{portfolio_context}\n\nPregunta del usuario por chat: {user_question}"
    
    try:
        # 2. Elegimos el modelo más moderno y rápido
        model = genai.GenerativeModel('models/gemini-2.5-flash')
        
        # 3. Hacemos la llamada a la inteligencia artificial
        response = model.generate_content(prompt_completo)
        
        # Devolvemos solo el texto de la respuesta
        return response.text
        
    except Exception as e:
        print(f"Error crítico en Gemini API: {e}")
        return "Disculpa, el asesor de BIOR Invest AI está experimentando interrupciones técnicas. Por favor, intenta de nuevo en un momento."