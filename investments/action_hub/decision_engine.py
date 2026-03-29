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

        ESTADO ACTUAL:
        - Capital Total Operativo: ${cap_total:,.0f} MXN.
        - Inyección HOY: ${cap_extra:,.0f} MXN.
        - Aporte Mensual: ${aportacion:,.0f} MXN.
        - Enfoque: {preferencia}.
        - Cartera actual: {txt_activos if txt_activos else "Sin activos previos."}

        TAREAS ESPECÍFICAS:
        1. DIAGNÓSTICO: Explica el error principal de la cartera actual (ej: falta de diversificación, dinero ocioso) y por qué es peligroso.
        2. MISIÓN HOY: Qué hacer exactamente con los ${cap_extra} disponibles hoy.
        3. HOJA DE RUTA (4 MESES): Crea un plan mensual para los ${aportacion} de ahorro. Sé específico (Mes 1: Comprar X, Mes 2: Rebalancear Y...).
        4. HACK FISCAL: Un consejo legal en México para pagar menos impuestos o recuperar dinero, explicando el beneficio tangible.

        RESPUESTA JSON:
        {{
            "riesgo_detectado": "Análisis del error principal en 2 frases.",
            "nivel_riesgo": "Bajo/Medio/Alto/Crítico",
            "accion_inmediata": "Instrucción para el capital de hoy.",
            "hoja_ruta_mensual": [
                {{"mes": "Mes 1", "tarea": "Instrucción específica"}},
                {{"mes": "Mes 2", "tarea": "Instrucción específica"}},
                {{"mes": "Mes 3", "tarea": "Instrucción específica"}},
                {{"mes": "Mes 4", "tarea": "Instrucción específica"}}
            ],
            "porcentaje_objetivo": "Meta de cartera %.",
            "justificacion": "Por qué este plan es el más inteligente según tu experiencia.",
            "hack_fiscal": "Acción fiscal + Beneficio (dinero que ganas/ahorras)."
        }}
        """

        # --- 5. LÓGICA DE MEMORIA (FEEDBACK) ---
        # Buscamos el plan anterior (el penúltimo) para darle contexto de seguimiento
        plan_anterior = NexusPlan.objects.filter(user=user).order_by('-created_at')[1:2].first()
        contexto_seguimiento = ""
        if plan_anterior:
            prev_data = plan_anterior.plan_json
            contexto_seguimiento = f"""
            CONTEXTO DE SEGUIMIENTO (Plan Anterior):
            El mes pasado le recomendaste: {prev_data.get('accion_inmediata')}
            Tu hoja de ruta era: {prev_data.get('hoja_ruta_mensual')}
            Evalúa brevemente si su portafolio actual refleja progreso y ajusta la nueva hoja de ruta.
            """
        # --- 6. CONFIGURACIÓN Y LLAMADA EN CASCADA ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("API Key no configurada.")

        genai.configure(api_key=api_key)

        # Jerarquía optimizada para velocidad y estabilidad
        MODELOS = [
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

        # Combinamos el prompt original con el seguimiento
        prompt_final = prompt_sistema + contexto_seguimiento

        for model_name in MODELOS:
            try:
                model = genai.GenerativeModel(model_name)
                respuesta = model.generate_content(prompt_final)
                texto_sucio = respuesta.text.strip()

                # Limpieza de asteriscos y extracción de JSON
                match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
                if match:
                    texto_limpio = match.group(0).replace('**', '').replace('*', '')
                    resultado_ia = json.loads(texto_limpio)
                    break
            except Exception as e:
                ultimo_error = str(e)
                continue

        if not resultado_ia:
            raise ValueError(f"Falla total: {ultimo_error}")

        # --- 7. PERSISTENCIA FINAL ---
        # Guardamos el registro. Al tener el plan_json completo, 
        # siempre podremos reconstruir la hoja de ruta en el frontend.
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        return resultado_ia

    except Exception as e:
        print(f"ERROR CRÍTICO NEXUS: {str(e)}")
        return {
            "riesgo_detectado": "Error en el núcleo de memoria.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Reintente en 60 segundos.",
            "hoja_ruta_mensual": [],
            "justificacion": f"No pudimos conectar con tu historial: {str(e)[:50]}",
            "hack_fiscal": "Consulta tu constancia de situación fiscal."
        }