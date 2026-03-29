import json
import google.generativeai as genai
from django.conf import settings

def generar_plan_decision_nexus(user):
    """
    Motor de decisiones del Action Hub. 
    Analiza el portafolio y genera un plan de acción estricto en JSON.
    """
    # 1. Variables simuladas (luego las conectamos a tus modelos reales)
    capital_total = 37262.18
    porcentaje_cripto = 28.7
    porcentaje_rv = 21.5

    # 2. El Prompt Estricto
    prompt_sistema = f"""
    Eres NEXUS, un asesor financiero basado en la estrategia Long Angle. 
    El usuario {user.username} tiene un capital de ${capital_total} MXN.
    Su Renta Variable es del {porcentaje_rv}% (Ideal: 47%).
    Su Cripto/Alternativas es del {porcentaje_cripto}% (Ideal: 8%).

    Tu objetivo es darle un plan de acción INMEDIATO para rebalancear su portafolio.
    
    REGLA ESTRICTA: Tu respuesta DEBE ser ÚNICA Y EXCLUSIVAMENTE un objeto JSON válido con esta estructura exacta:
    {{
        "riesgo_detectado": "Descripción breve del mayor riesgo actual.",
        "nivel_riesgo": "Alto, Medio o Bajo",
        "accion_inmediata": "Qué activo específico debe comprar o vender HOY.",
        "porcentaje_objetivo": "A qué porcentaje debe llevar ese activo.",
        "justificacion": "Por qué esta acción matemática le beneficia.",
        "hack_fiscal": "Un consejo fiscal aplicable en México (ej. PPR, SOFIPO)."
    }}
    """

    # 3. Llamada a Gemini
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    try:
        respuesta = model.generate_content(prompt_sistema)
        texto_limpio = respuesta.text.strip()
        
        if texto_limpio.startswith("```json"):
            texto_limpio = texto_limpio[7:-3].strip()
            
        return json.loads(texto_limpio)

    except Exception as e:
        print(f"Error en NEXUS Decision Engine: {e}")
        return {
            "riesgo_detectado": "Error de conexión temporal.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Revisa tu conexión a internet.",
            "porcentaje_objetivo": "-",
            "justificacion": "El motor de IA está procesando demasiadas solicitudes.",
            "hack_fiscal": "Aprovecha el tiempo para leer sobre la LISR."
        }