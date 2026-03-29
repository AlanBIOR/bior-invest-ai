import os
import json
import re
import google.generativeai as genai
from google.api_core import exceptions
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan 

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS v2.2: Consultor Patrimonial Senior.
    Optimizado para móvil: Diagnósticos con 'por qué', Agenda Mensual y Hacks Fiscales claros.
    """
    try:
        # --- 1. NORMALIZACIÓN DE DATOS ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        preferencia = preferencia_input

        # --- 2. CACHÉ DE BASE DE DATOS ---
        ultimo_plan = NexusPlan.objects.filter(
            user=user, 
            capital_extra=cap_extra, 
            aportacion_mensual=aportacion, 
            preferencia_activo=preferencia
        ).order_by('-created_at').first()

        if ultimo_plan:
            return ultimo_plan.plan_json

        # --- 3. CONTEXTO PATRIMONIAL REAL (ADN BIOR) ---
        profile = Profile.objects.filter(user=user).first()
        efectivo_dash = float(profile.capital) if profile and profile.capital else 0.0
        
        activos = Investment.objects.filter(user=user).select_related('category')
        total_inv = float(activos.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)
        cap_total = efectivo_dash + total_inv + cap_extra
        
        txt_activos = "\n".join([
            f"- {a.asset_name}: ${float(a.current_value or 0):,.0f} ({a.category.name})" 
            for a in activos
        ])

        # --- 4. PROMPT ESTRATÉGICO (DIAGNÓSTICO + AGENDA + BENEFICIO FISCAL) ---
        prompt_sistema = f"""
        Eres NEXUS, estratega patrimonial con 1 siglo de experiencia. Guía a {user.username}.
        REGLA DE ORO: No uses asteriscos (**), ni negritas, ni lenguaje técnico complejo. Sé directo.

        CONTEXTO:
        - Capital Total: ${cap_total:,.0f} MXN.
        - Inyección HOY: ${cap_extra:,.0f} MXN.
        - Aporte Mensual: ${aportacion:,.0f} MXN.
        - Interés: {preferencia}.
        - Cartera: {txt_activos if txt_activos else "Cuenta nueva."}

        TAREA:
        1. Diagnóstico: Qué está mal y por qué (conciso).
        2. Misión de Hoy: Instrucción para los ${cap_extra} disponibles ahora.
        3. Agenda Mensual: Una lista de tareas (tasks) paso a paso para la aportación de ${aportacion}.
        4. Hack Fiscal: Un consejo de impuestos en México explicando para qué sirve y qué ganas tú.

        RESPUESTA JSON ÚNICAMENTE:
        {{
            "riesgo_detectado": "Explica qué falta o sobra y qué peligro representa en 2 oraciones.",
            "nivel_riesgo": "Bajo/Medio/Alto/Crítico",
            "accion_inmediata": "Instrucción corta para el capital de hoy.",
            "agenda_mensual": "Lista de tareas para tu ahorro mensual (ej: 1. Comprar X... 2. Revisar Y...).",
            "porcentaje_objetivo": "Meta %.",
            "justificacion": "Razonamiento estratégico breve (máximo 2 párrafos cortos).",
            "hack_fiscal": "Consejo claro: Qué hacer + Qué beneficio obtienes tú (dinero de vuelta, menos cobro de ISR, etc)."
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

                # --- 6. LIMPIEZA QUIRÚRGICA (Regex + Limpiador de Asteriscos) ---
                # Extraemos el bloque JSON
                match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
                
                if match:
                    texto_limpio = match.group(0)
                    # Limpieza total de negritas sucias (**) que ensucian el texto en móvil
                    texto_limpio = texto_clean = texto_limpio.replace('**', '').replace('*', '')
                else:
                    texto_limpio = texto_sucio.replace("```json", "").replace("```", "").strip()

                # Parseo y validación
                resultado_ia = json.loads(texto_limpio)
                break 

            except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable):
                continue # Salto por cuota agotada
            except Exception as e:
                ultimo_error = str(e)
                continue

        if not resultado_ia:
            raise ValueError(f"Falla total del motor: {ultimo_error}")

        # --- 7. PERSISTENCIA EN BASE DE DATOS ---
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        return resultado_ia

    except Exception as e:
        print(f"DEBUG NEXUS ERROR: {str(e)}")
        # Fallback con el nuevo formato de v2.2
        return {
            "riesgo_detectado": "El sistema de análisis detectó una interrupción en los flujos de datos.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Refresca la página y reintenta.",
            "agenda_mensual": "1. Mantener liquidez actual. 2. Reintentar consulta en 1 minuto.",
            "porcentaje_objetivo": "N/A",
            "justificacion": "Error técnico: El motor está reconectando con el núcleo financiero.",
            "hack_fiscal": "Asegúrate de que tu información de perfil esté completa para mejorar el diagnóstico."
        }