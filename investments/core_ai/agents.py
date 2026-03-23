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
    Decide si usar Gemini (rápido) o Claude (estratégico) 
    dependiendo de la complejidad.
    """
    
    # Si la pregunta es sobre "mejorar", "analizar" o "estrategia", usamos CLAUDE
    es_estrategico = any(word in user_question.lower() for word in ['mejorar', 'analizar', 'portafolio', 'estrategia', 'invertir'])

    try:
        if es_estrategico and CLAUDE_API_KEY:
            print("🧠 Usando Claude 3.5 (OpenClaw) para análisis estratégico...")
            response = client_claude.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": f"Contexto de Portafolio: {portfolio_context}\n\nPregunta: {user_question}"}
                ]
            )
            return response.content[0].text
        else:
            print("⚡ Usando Gemini 2.5 para respuesta rápida...")
            prompt_completo = f"{SYSTEM_PROMPT}\n\nContexto: {portfolio_context}\n\nUsuario: {user_question}"
            response = client_gemini.models.generate_content(
                model='gemini-2.5-flash', 
                contents=prompt_completo
            )
            return response.text
            
    except Exception as e:
        print(f"Error en Agentes IA: {e}")
        return "Lo siento, el asesor de BIOR Invest AI está recalibrando sus algoritmos. Intenta de nuevo en un momento."