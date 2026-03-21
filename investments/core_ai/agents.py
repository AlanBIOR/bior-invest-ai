import os
import google.generativeai as genai

# 1. Configuración de la API Key
# IMPORTANTE: Para el hackatón rápido puedes pegar tu llave directamente donde dice "TU_API_KEY_AQUI".
# Sin embargo, la buena práctica es guardarla en un archivo .env y leerla con os.environ.get()
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
# Inicializamos la configuración de Google
genai.configure(api_key=GEMINI_API_KEY)

def ask_financial_agent(user_question, portfolio_context):
    """Envía la pregunta del usuario y su contexto financiero a la API de Gemini."""
    
    # Unimos tu mega-prompt (el contexto fiscal y financiero) con la pregunta del usuario
    prompt_completo = f"{portfolio_context}\n\nPregunta del usuario por WhatsApp: {user_question}"
    
    try:
        # 2. Elegimos el modelo. 'gemini-1.5-flash' es el ideal porque es el más rápido
        # y barato para aplicaciones de chat de texto, perfecto para el flujo de n8n.
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 3. Hacemos la llamada a la inteligencia artificial
        response = model.generate_content(prompt_completo)
        
        # Devolvemos solo el texto de la respuesta
        return response.text
        
    except Exception as e:
        print(f"Error crítico en Gemini API: {e}")
        return "Disculpa, el asesor de BIOR Invest AI está experimentando interrupciones técnicas. Por favor, intenta de nuevo en un momento."