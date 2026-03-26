import os
from google import genai 
from dotenv import load_dotenv

load_dotenv()

# 1. Configuración del Cliente - USAREMOS 'client' COMO ESTÁNDAR
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

if not GEMINI_API_KEY:
    raise ValueError("⚠️ Falta la GEMINI_API_KEY en el archivo .env")

client = genai.Client(api_key=GEMINI_API_KEY)

# 2. SYSTEM_PROMPT Optimizado (Menos "rollo", más precisión)
SYSTEM_PROMPT = """
# ROL: BIOR Invest AI - Estratega Patrimonial México.

# ESTRATEGIA LONG ANGLE (PESOS OBJETIVO):
- Renta Variable (ETFs: VOO, VT): 47%
- Bienes Raíces (FIBRAS): 17%
- Private Equity: 15%
- Alternativas (Cripto): 8%
- Efectivo/Renta Fija (CETES, Nu): 13%

# REGLAS DE ORO DE RESPUESTA:
1. BREVEDAD: No des introducciones largas. Ve al grano.
2. RELEVANCIA: Si el usuario pregunta por un dato externo (ej. tasas de CETES), responde ESO y no analices su portafolio a menos que él lo pida o sea necesario para comparar.
3. ESTILO: Máximo 3 párrafos por respuesta, a menos que sea un análisis solicitado. Usa bullets.
4. TAX-SMART: Siempre que menciones Renta Fija o SOFIPOS, recuerda la exención del Art. 93 (5 UMAs) y el PPR (Art. 151).
5. TASA CETES (MARZO 2026): Si te preguntan tasas, menciona que rondan el 10.00% - 10.50% anual, pero deben validar en CetesDirecto.
6. Si recibes un bloque de texto que dice '[REPORTE DE USUARIO]' o similar, 
tienes permiso total para leer esos datos y usarlos en tu respuesta. 
6. No digas que no tienes acceso, porque el sistema te los está proporcionando legalmente.

# LÓGICA DE ANÁLISIS:
- Solo si detectas intención de "revisar mi dinero", calcula porcentajes reales del 'portfolio_context', detecta el GAP vs Long Angle y prioriza la Renta Variable.
- Si hay exceso de Cripto (>8%), menciónalo como riesgo de volatilidad.

# CIERRE:
- Finaliza siempre con una frase corta de exención legal: "Educación estratégica, no asesoría regulada por CNBV."
"""

import time

# Variable global para control de flujo (Rate Limiting básico a nivel de ejecución)
LAST_REQUEST_TIME = 0
MIN_INTERVAL = 3  # No permite peticiones con menos de 3 segundos de diferencia

def ask_financial_agent(user_question, portfolio_context):
    global LAST_REQUEST_TIME
    
    # 1. Restricción de seguridad: Evitar spam de peticiones
    current_time = time.time()
    if current_time - LAST_REQUEST_TIME < MIN_INTERVAL:
        return "⚠️ Sistema saturado. Por favor, espera unos segundos antes de enviar otra consulta. 🚀"
    
    LAST_REQUEST_TIME = current_time

    # 2. Definición de disparadores
    palabras_analisis = ['mi portafolio', 'mis inversiones', 'como voy', 'mejorar', 'rebalancear', 'que hago', 'analiza']
    quiere_analisis = any(word in user_question.lower() for word in palabras_analisis)

    # 3. Lista de Prioridad (Redundancia de 10 niveles)
    MODELOS_HIERARCHY = [
        'models/gemini-2.5-pro',
        'models/gemini-2.5-flash',
        'models/gemini-2.0-flash',
        'models/gemini-2.0-flash-lite',
        'models/gemini-1.5-pro',
        'models/gemini-1.5-flash',
        'models/gemini-flash-latest',
        'models/gemini-pro-latest',
        'models/gemini-2.0-flash-001',
        'models/gemini-1.5-flash-8b'
    ]

    # Preparación del Prompt
    if quiere_analisis:
        prompt_final = f"""
        [DATOS REALES DEL USUARIO]: {portfolio_context}
        [INSTRUCCIONES]: {SYSTEM_PROMPT}
        [ORDEN]: Analiza el portafolio real arriba descrito contra la estrategia BIOR.
        [PREGUNTA]: {user_question}
        """
    else:
        prompt_final = f"{SYSTEM_PROMPT}\n\nPregunta rápida: {user_question}"

    # 4. Bucle de ejecución con Fallback Automático
    for i, modelo in enumerate(MODELOS_HIERARCHY):
        try:
            print(f"尝试 (Intento {i+1}/10): Usando {modelo}...")
            
            response = client.models.generate_content(
                model=modelo,
                contents=prompt_final
            )
            
            # --- LIMPIEZA DE FORMATO PARA WHATSAPP ---
            # Guardamos la respuesta y forzamos el reemplazo de Markdown doble (**) a simple (*)
            respuesta_final = response.text.replace("**", "*")
            
            # Si llegamos aquí, la respuesta fue exitosa
            return respuesta_final

        except Exception as e:
            error_str = str(e).upper()
            print(f"❌ Falló {modelo}: {e}")
            
            if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                print(f"🔄 Cuota agotada en {modelo}. Saltando al siguiente nivel...")
                continue
            else:
                continue

    # 5. Si después de recorrer los 10 modelos nada funcionó
    return "Estamos recibiendo un volumen inusual de consultas en todos nuestros nodos. Por favor, intenta de nuevo en 1 minuto. 🚀"