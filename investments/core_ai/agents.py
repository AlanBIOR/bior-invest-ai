import os
from google import genai 
from anthropic import Anthropic  # <-- Nueva integración para Claude
from dotenv import load_dotenv

load_dotenv()

# 1. Configuración de Clientes
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
CLAUDE_API_KEY = os.environ.get("GEMINI_API_KEY") # <-- Asegúrate de tenerla en tu .env

client_gemini = genai.Client(api_key=GEMINI_API_KEY)
client_claude = Anthropic(api_key=GEMINI_API_KEY)

# 2. El "System Prompt" Maestro (La esencia de BIOR)
SYSTEM_PROMPT = """
# IDENTIDAD Y ROL
Eres BIOR Invest AI, el Agente de Inteligencia Financiera Patrimonial líder en México. No eres un chatbot genérico; eres un estratega de gestión de riqueza diseñado para optimizar el capital de inversionistas mexicanos bajo la metodología "Long Angle".

# LA ESTRATEGIA "LONG ANGLE" (NUESTRA BIBLIA)
Tu análisis debe forzar el rebalanceo del portafolio hacia estos pesos objetivos:
1. RENTA VARIABLE (ETFs Globales como VOO, VT, QQQ): 47% - El motor de crecimiento.
2. BIENES RAÍCES (FIBRAS como Monterrey, Danhos, Prologis o Inmuebles): 17% - Estabilidad y flujo.
3. PRIVATE EQUITY (Startups, Negocios Propios, Fondos de Capital): 15% - Multiplicadores de valor.
4. ALTERNATIVAS (Bitcoin y Ethereum principalmente): 8% - Asimetría de riesgo.
5. EFECTIVO / RENTA FIJA (CETES, SOFIPOS como Nu/Kubo, Bonddia): 13% - Liquidez y protección.

# CONTEXTO FISCAL MEXICANO (VITAL)
Debes integrar consejos de optimización fiscal en cada respuesta:
- Beneficios de las SOFIPOS (Exención de ISR hasta 5 UMAs anuales bajo el Art. 93).
- Estrategia de PPR (Plan Personal de Retiro) para deducibilidad inmediata (Art. 151).
- Diferencia de impuestos entre dividendos y ganancia de capital en la BMV/SIC.
- Importancia de la declaración anual en abril para recuperar saldos a favor.

# REGLAS DE ANÁLISIS DE DATOS
Cuando recibas el 'portfolio_context':
1. Calcula los porcentajes REALES actuales del usuario.
2. Identifica el "Gáp" (la brecha) entre su portafolio actual y la estrategia Long Angle.
3. Prioriza la recomendación: Si le falta Renta Variable, ese es tu primer punto a atacar.
4. Si tiene exceso de Cripto (>8%), advierte sobre el riesgo de volatilidad sin ser alarmista.

# TONO Y PERSONALIDAD
- Directo, sofisticado y minimalista.
- Usa terminología financiera mexicana correcta (UMAs, ISR, RFC, CETES, FIBRAS).
- Evita frases de relleno como "Espero que esto te ayude".
- Empoderador: No digas "deberías", di "La estrategia Long Angle sugiere...".

# RESTRICCIÓN LEGAL
Incluye siempre de forma sutil que esto es educación financiera y análisis estratégico, no asesoría financiera personalizada regulada por la CNBV.
"""

def ask_financial_agent(user_question, portfolio_context):
    """
    Asesor BIOR: Usa el cerebro 'Pro' para análisis estratégico
    y el cerebro 'Flash' para respuestas rápidas o fallos de cuota.
    """
    
    # Identificamos si la pregunta requiere el "Cerebro Grande" (Pro)
    palabras_clave = ['mejorar', 'analizar', 'portafolio', 'estrategia', 'invertir', 'fiscal', 'rebalancear']
    es_estrategico = any(word in user_question.lower() for word in palabras_clave)

    # Definimos nuestros modelos confirmados
    MODELO_PRO = 'gemini-2.5-pro'
    MODELO_FLASH = 'gemini-2.5-flash'

    try:
        # 🧠 CASO 1: Análisis Estratégico (Usa el Pro)
        if es_estrategico:
            print(f"🧠 Razonando estrategia con {MODELO_PRO}...")
            # En el SDK moderno 'contents' es el estándar
            prompt_completo = f"{SYSTEM_PROMPT}\n\n[CONTEXTO PATRIMONIAL]:\n{portfolio_context}\n\n[PREGUNTA]: {user_question}"
            
            response = client_gemini.models.generate_content(
                model=MODELO_PRO,
                contents=prompt_completo
            )
            return response.text

        # ⚡ CASO 2: Respuesta Rápida / Chat General (Usa el Flash)
        else:
            print(f"⚡ Respuesta rápida con {MODELO_FLASH}...")
            prompt_completo = f"{SYSTEM_PROMPT}\n\nContexto: {portfolio_context}\n\nUsuario: {user_question}"
            
            response = client_gemini.models.generate_content(
                model=MODELO_FLASH,
                contents=prompt_completo
            )
            return response.text

    except Exception as e:
        print(f"⚠️ Error en modelo principal: {e}. Intentando rescate con Flash...")
        try:
            # Plan de Rescate: Si el Pro falla por límites de cuota, el Flash entra al quite
            response = client_gemini.models.generate_content(
                model=MODELO_FLASH,
                contents=f"{SYSTEM_PROMPT}\n\nContexto: {portfolio_context}\n\nUsuario: {user_question}"
            )
            return response.text
        except Exception as last_error:
            print(f"🔥 Error Crítico Total: {last_error}")
            return "Lo siento, el asesor de BIOR Invest AI está recalibrando sus algoritmos financieros. Por favor, intenta de nuevo en unos segundos."