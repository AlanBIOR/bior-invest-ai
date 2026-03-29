import os
import json
import re
import google.generativeai as genai
from google.api_core import exceptions
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan 

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS v2.1: Estratega Senior Optimizado.
    Enfoque en respuestas breves, alto valor estratégico y visualización limpia para móvil.
    """
    try:
        # --- 1. NORMALIZACIÓN ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        preferencia = preferencia_input

        # --- 2. CACHÉ INTELIGENTE ---
        ultimo_plan = NexusPlan.objects.filter(
            user=user, 
            capital_extra=cap_extra, 
            aportacion_mensual=aportacion, 
            preferencia_activo=preferencia
        ).order_by('-created_at').first()

        if ultimo_plan:
            return ultimo_plan.plan_json

        # --- 3. CONTEXTO PATRIMONIAL ---
        profile = Profile.objects.filter(user=user).first()
        efectivo_dash = float(profile.capital) if profile and profile.capital else 0.0
        
        activos = Investment.objects.filter(user=user).select_related('category')
        total_inv = float(activos.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)
        cap_total = efectivo_dash + total_inv + cap_extra
        
        txt_activos = "\n".join([
            f"- {a.asset_name}: ${float(a.current_value or 0):,.0f} ({a.category.name})" 
            for a in activos
        ])

        # --- 4. PROMPT ULTRA-OPTIMIZADO (MOBILE FIRST) ---
        prompt_sistema = f"""
        Eres NEXUS, estratega financiero con 100 años de experiencia. Tu misión es guiar a {user.username}.
        REGLA CRÍTICA: Sé breve, directo y evita el uso excesivo de asteriscos (**) o negritas. Queremos un texto limpio.

        DATOS HOY:
        - Capital Total: ${cap_total:,.0f} MXN.
        - Inyección hoy: ${cap_extra:,.0f} MXN.
        - Ahorro mensual: ${aportacion:,.0f} MXN.
        - Interés: {preferencia}.
        - Cartera: {txt_activos if txt_activos else "Iniciando desde cero."}

        TAREA:
        Basado en 'Long Angle', da una instrucción quirúrgica. 
        - Si el capital es bajo (<$50k), recomienda FIBRAS o ETFs.
        - Menciona el tope de 5 UMAs en SOFIPOS si aplica.
        - Menciona PPR (Art 151) si hay flujo mensual.

        RESPUESTA ÚNICAMENTE JSON:
        {{
            "riesgo_detectado": "Análisis de 1 oración.",
            "nivel_riesgo": "Bajo/Medio/Alto/Crítico",
            "accion_inmediata": "Instrucción corta (Activo + Plataforma).",
            "porcentaje_objetivo": "Meta %.",
            "justificacion": "Explicación lógica sin rellenos (máximo 3 párrafos cortos).",
            "hack_fiscal": "Tip de impuestos México en 1 oración."
        }}
        """
        # --- 5. EJECUCIÓN EN CASCADA Y LIMPIEZA QUIRÚRGICA ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("API Key no configurada.")

        genai.configure(api_key=api_key)

        # Jerarquía optimizada para velocidad y estabilidad
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

        resultado_ia = None
        ultimo_error = ""

        for model_name in MODELOS_HIERARCHY:
            try:
                model = genai.GenerativeModel(model_name)
                respuesta = model.generate_content(prompt_sistema)
                texto_sucio = respuesta.text.strip()

                # --- 6. EXTRACCIÓN PURA DE JSON (Regex) ---
                # Buscamos el primer { y el último } para ignorar basura como ```json o textos extra
                match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
                
                if match:
                    texto_limpio = match.group(0)
                    # Eliminamos escapes de asteriscos si el modelo intentó poner negritas dentro del JSON
                    texto_limpio = texto_limpio.replace('**', '') 
                else:
                    texto_limpio = texto_sucio.replace("```json", "").replace("```", "").strip()

                # Intentamos parsear para validar
                resultado_ia = json.loads(texto_limpio)
                break # Éxito: Salimos del bucle de modelos

            except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable):
                continue # Salto automático al siguiente modelo por falta de tokens
            except Exception as e:
                ultimo_error = str(e)
                continue

        if not resultado_ia:
            raise ValueError(f"Falla total del motor. Error: {ultimo_error}")

        # --- 7. PERSISTENCIA Y RETORNO ---
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        return resultado_ia

    except Exception as e:
        # Log técnico silencioso para el servidor
        print(f"DEBUG NEXUS: {str(e)}")
        
        # Fallback elegante con el estilo de NEXUS
        return {
            "riesgo_detectado": "Anomalía temporal en el procesamiento.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Reintente en 30 segundos.",
            "porcentaje_objetivo": "N/A",
            "justificacion": "El motor está recalibrando la conexión con los mercados mundiales.",
            "hack_fiscal": "Mantenga su RFC actualizado."
        }