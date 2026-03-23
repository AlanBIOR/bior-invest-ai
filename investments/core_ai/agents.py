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

# LÓGICA DE ANÁLISIS:
- Solo si detectas intención de "revisar mi dinero", calcula porcentajes reales del 'portfolio_context', detecta el GAP vs Long Angle y prioriza la Renta Variable.
- Si hay exceso de Cripto (>8%), menciónalo como riesgo de volatilidad.

# CIERRE:
- Finaliza siempre con una frase corta de exención legal: "Educación estratégica, no asesoría regulada por CNBV."
"""

def ask_financial_agent(user_question, portfolio_context):
    """
    Asesor BIOR: Inteligencia selectiva con prioridad absoluta en datos reales.
    """
    # 1. Definimos disparadores de análisis profundo
    palabras_analisis = ['mi portafolio', 'mis inversiones', 'como voy', 'mejorar', 'rebalancear', 'que hago', 'analiza']
    quiere_analisis = any(word in user_question.lower() for word in palabras_analisis)

    # 2. Modelos
    MODELO_PRO = 'gemini-2.5-pro'
    MODELO_FLASH = 'gemini-2.5-flash'

    try:
        # --- CASO A: Análisis Profundo ---
        if quiere_analisis:
            print(f"🧠 Modo Estratégico activado ({MODELO_PRO})...")
            
            # Forzamos los datos AL PRINCIPIO del prompt
            prompt_final = f"""
            [DATOS REALES DEL USUARIO - PRIORIDAD MÁXIMA]:
            {portfolio_context}
            
            [INSTRUCCIONES DE SISTEMA]:
            {SYSTEM_PROMPT}
            
            [ORDEN]: Analiza el portafolio real arriba descrito. 
            NO menciones clubes privados ni definiciones externas de 'Long Angle'. 
            Compáralo exclusivamente contra los porcentajes de la estrategia BIOR.
            
            [PREGUNTA DEL USUARIO]: {user_question}
            """
            modelo_a_usar = MODELO_PRO

        # --- CASO B: Respuesta Rápida ---
        else:
            print(f"⚡ Modo Consulta Rápida ({MODELO_FLASH})...")
            prompt_final = f"""
            {SYSTEM_PROMPT}
            
            Pregunta rápida: {user_question}
            (Responde de forma concisa. No analices el portafolio a menos que sea necesario).
            """
            modelo_a_usar = MODELO_FLASH

        # 3. Llamada a la API
        response = client.models.generate_content(
            model=modelo_a_usar,
            contents=prompt_final
        )
        return response.text

    except Exception as e:
        print(f"⚠️ Error: {e}")
        # Plan de Rescate
        try:
            res_backup = client.models.generate_content(
                model=MODELO_FLASH,
                contents=f"Responde de forma sencilla: {user_question}"
            )
            return res_backup.text
        except:
            return "BIOR Invest AI está recalibrando sus algoritmos financieros."