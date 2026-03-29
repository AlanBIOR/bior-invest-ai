import os, json, re, google.generativeai as genai
from google.api_core import exceptions
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan 

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS v2.4: Estratega con Foco Quirúrgico.
    Separa el capital nuevo del portafolio actual y genera una agenda de diversificación real.
    """
    try:
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        preferencia = preferencia_input

        # Cache
        ultimo_plan = NexusPlan.objects.filter(
            user=user, capital_extra=cap_extra, 
            aportacion_mensual=aportacion, preferencia_activo=preferencia
        ).order_by('-created_at').first()

        if ultimo_plan: return ultimo_plan.plan_json

        # Contexto Real
        profile = Profile.objects.filter(user=user).first()
        efectivo_dash = float(profile.capital) if profile and profile.capital else 0.0
        activos = Investment.objects.filter(user=user).select_related('category')
        total_inv = float(activos.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)
        cap_total_existente = efectivo_dash + total_inv
        
        txt_activos = "\n".join([f"- {a.asset_name}: ${float(a.current_value or 0):,.0f}" for a in activos])

        # PROMPT DE ALTO NIVEL
        prompt_sistema = f"""
        Eres NEXUS, consultor con 100 años de experiencia. Alan te entrega ${cap_extra:,.0f} MXN nuevos HOY.
        
        CONTEXTO DE APOYO (Solo para saber qué ya tiene):
        - Portafolio actual: ${cap_total_existente:,.0f} MXN.
        - Activos actuales: {txt_activos if txt_activos else "Ninguno."}

        REGLAS DE ORO:
        1. LA MISIÓN DE HOY: Debe enfocarse EXCLUSIVAMENTE en cómo distribuir los ${cap_extra:,.0f} nuevos. No sumes lo que ya tiene para esta instrucción.
        2. AGENDA DE 4 MESES: Cada mes debe tener una tarea DIFERENTE para su aporte mensual de ${aportacion:,.0f}. No repitas activos. Haz una rotación lógica para diversificar (ej: Mes 1: Acciones, Mes 2: FIBRAS, Mes 3: Renta Fija, Mes 4: Oro/Alternativas).
        3. NO USES ASTERISCOS ni negritas.

        RESPUESTA JSON:
        {{
            "riesgo_detectado": "Análisis de riesgo del portafolio TOTAL en 1 oración.",
            "nivel_riesgo": "Bajo/Medio/Alto/Crítico",
            "accion_inmediata": "Instrucción exacta para los ${cap_extra} de hoy.",
            "hoja_ruta_mensual": [
                {{"mes": "Mes 1", "tarea": "Tarea única para diversificar."}},
                {{"mes": "Mes 2", "tarea": "Tarea diferente para complementar."}},
                {{"mes": "Mes 3", "tarea": "Tarea de estabilidad o cobertura."}},
                {{"mes": "Mes 4", "tarea": "Tarea de rebalanceo o nuevo sector."}}
            ],
            "porcentaje_objetivo": "Meta %.",
            "justificacion": "Breve explicación de por qué esta rotación de aportaciones es superior a invertir siempre en lo mismo.",
            "hack_fiscal": "Consejo fiscal: Acción + Beneficio tangible en pesos."
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
                # Limpieza de nombre de modelo por si viene con prefijo
                m_name = model_name.replace('models/', '')
                model = genai.GenerativeModel(m_name)
                respuesta = model.generate_content(prompt_final)
                texto_sucio = respuesta.text.strip()

                # --- 7. EXTRACCIÓN Y LIMPIEZA QUIRÚRGICA ---
                # Buscamos el bloque JSON y eliminamos asteriscos que ensucian el mensaje
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

        # --- 8. PERSISTENCIA Y SINCRONIZACIÓN REAL CON DB ---
        
        # A. Guardamos el historial del plan
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        # B. ACTUALIZACIÓN DEL PERFIL (Lo que antes hacía el Dashboard)
        # Esto modifica los campos 'capital' y 'aportacion' que ves en tu Admin de Django
        if profile:
            profile.capital = cap_extra
            profile.aportacion = aportacion
            profile.save()

        return resultado_ia

    except Exception as e:
        print(f"ERROR CRÍTICO NEXUS: {str(e)}")
        return {
            "riesgo_detectado": "Error en el núcleo de memoria o sincronización.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Reintente en 60 segundos.",
            "hoja_ruta_mensual": [],
            "justificacion": f"No pudimos conectar con tu historial: {str(e)[:50]}",
            "hack_fiscal": "Consulta tu constancia de situación fiscal mientras restauramos el sistema."
        }