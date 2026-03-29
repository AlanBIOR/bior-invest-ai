import os
import json
import google.generativeai as genai
from django.db.models import Sum

# Importamos tus modelos reales
from investments.models import Profile, Investment

def generar_plan_decision_nexus(user):
    """
    Motor de decisiones del Action Hub. 
    Analiza el portafolio REAL de la base de datos y genera un plan de acción en JSON.
    """
    try:
        # --- 1. EXTRACCIÓN DE DATOS REALES (Django ORM) ---
        profile = Profile.objects.filter(user=user).first()
        capital_efectivo = float(profile.capital) if profile and profile.capital else 0.0

        activos = Investment.objects.filter(user=user).select_related('category')
        
        # Sumamos el valor actual de todas las inversiones
        agg = activos.aggregate(total_cur=Sum('current_value'))
        total_invertido = float(agg['total_cur'] or 0.0)

        # Capital Total = Efectivo en mano + Dinero Invertido
        capital_total = capital_efectivo + total_invertido

        # Si el usuario es nuevo y tiene 0 pesos, evitamos errores matemáticos
        if capital_total <= 0:
            return {
                "riesgo_detectado": "Aún no tienes fondos registrados en tu portafolio.",
                "nivel_riesgo": "Bajo",
                "accion_inmediata": "Agrega tu capital inicial en el Dashboard para comenzar.",
                "porcentaje_objetivo": "100%",
                "justificacion": "El primer paso para invertir es definir con cuánto capital cuentas.",
                "hack_fiscal": "Recuerda que en México las inversiones en CETES tienen beneficios fiscales."
            }

        # --- 2. CÁLCULO DE PORCENTAJES MATEMÁTICOS ---
        # Filtramos por nombre de categoría o ID (ID 4 suele ser cripto en tu sistema)
        valor_cripto = sum(float(a.current_value or 0) for a in activos if 'cripto' in a.category.name.lower() or 'alternativas' in a.category.name.lower() or a.category.id == 4)
        valor_rv = sum(float(a.current_value or 0) for a in activos if 'renta variable' in a.category.name.lower())

        porcentaje_cripto = round((valor_cripto / capital_total) * 100, 2)
        porcentaje_rv = round((valor_rv / capital_total) * 100, 2)

        # Construimos un resumen en texto de todos los activos para dárselo a la IA
        lista_activos_texto = "\n".join([f"- {a.asset_name}: ${float(a.current_value or 0):.2f} MXN ({a.category.name})" for a in activos])

        # --- 3. INGENIERÍA DE PROMPT CON CONTEXTO DINÁMICO ---
        prompt_sistema = f"""
        Eres NEXUS, un asesor financiero basado en la estrategia Long Angle. 
        Analiza el portafolio real del usuario {user.username}:

        DATOS FINANCIEROS ACTUALES:
        - Capital Total (Efectivo + Inversiones): ${capital_total:.2f} MXN
        - Efectivo sin invertir: ${capital_efectivo:.2f} MXN
        - Exposición a Renta Variable: {porcentaje_rv}% (Ideal Long Angle: 47%)
        - Exposición a Cripto/Alternativas: {porcentaje_cripto}% (Ideal Long Angle: 8%)
        
        DESGLOSE DE ACTIVOS:
        {lista_activos_texto if lista_activos_texto else "Solo tiene efectivo por ahora."}

        Tu objetivo es darle un plan de acción INMEDIATO para rebalancear su portafolio hacia el modelo Long Angle.
        
        REGLA ESTRICTA: Tu respuesta DEBE ser ÚNICA Y EXCLUSIVAMENTE un objeto JSON válido con esta estructura exacta, sin markdown de bloques de código:
        {{
            "riesgo_detectado": "Descripción breve del mayor riesgo actual basado en los números reales.",
            "nivel_riesgo": "Alto, Medio o Bajo",
            "accion_inmediata": "Qué activo específico debe comprar o vender HOY usando su efectivo disponible o rebalanceando.",
            "porcentaje_objetivo": "A qué porcentaje debe llegar ese activo.",
            "justificacion": "Por qué esta acción matemática le beneficia.",
            "hack_fiscal": "Un consejo fiscal aplicable en México (ej. PPR, SOFIPO)."
        }}
        """

        # --- 4. LLAMADA A GEMINI ---
        api_key = os.environ.get('GEMINI_API_KEY') # O como se llame tu variable de entorno
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        respuesta = model.generate_content(prompt_sistema)
        texto_limpio = respuesta.text.strip()
        
        # Limpiamos bloques de markdown si Gemini los incluye por necedad
        if texto_limpio.startswith("```json"):
            texto_limpio = texto_limpio[7:-3].strip()
        elif texto_limpio.startswith("```"):
            texto_limpio = texto_limpio[3:-3].strip()
            
        return json.loads(texto_limpio)

    except Exception as e:
        print(f"Error Crítico en NEXUS Decision Engine: {e}")
        return {
            "riesgo_detectado": "Error de procesamiento de portafolio.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Por favor, recarga la página.",
            "porcentaje_objetivo": "-",
            "justificacion": f"Ocurrió un error interno: {str(e)[:50]}...",
            "hack_fiscal": "Aprovecha el tiempo para leer sobre la LISR."
        }