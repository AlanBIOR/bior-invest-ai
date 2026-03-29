import os, json, re, google.generativeai as genai
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan, Category

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS v2.8: Arquitectura de Rebalanceo Táctico.
    Python provee los límites de la DB y la IA aplica ingeniería financiera 
    para decidir la ruta más segura y eficiente.
    """
    try:
        # --- 1. NORMALIZACIÓN DE DATOS DE ENTRADA ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        
        # --- 2. MODELO IDEAL (Configuración dinámica desde Admin Django) ---
        categorias_db = Category.objects.all()
        # Mapa: { 'slug': { 'nombre': '...', 'target': % } }
        modelo_objetivo = {
            cat.slug: {
                "nombre": cat.name,
                "target_porcentaje": float(cat.target_percentage)
            } for cat in categorias_db
        }

        # --- 3. REALIDAD PATRIMONIAL (Análisis de activos actuales del usuario) ---
        profile = Profile.objects.filter(user=user).first()
        activos_reales = Investment.objects.filter(user=user).select_related('category')
        total_invertido = float(activos_reales.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)
        
        # Agrupamos lo invertido por categoría para detectar "huecos"
        resumen_actual = {}
        for a in activos_reales:
            slug = a.category.slug
            resumen_actual[slug] = resumen_actual.get(slug, 0) + float(a.current_value)

        # --- 4. CONFIGURACIÓN DEL PROMPT (Ingeniería de Instrucciones) ---
        prompt_sistema = f"""
        Eres NEXUS, un estratega senior con 100 años de experiencia acumulada. 
        TU MISIÓN: Aplicar REBALANCEO TÁCTICO. No dividas el dinero al azar; detecta dónde falta capital para alcanzar el modelo ideal.

        MODELO OBJETIVO (Basado en Long Angle):
        {json.dumps(modelo_objetivo)}

        REALIDAD PATRIMONIAL DE {user.username.upper()}:
        - Total Invertido Actual: ${total_invertido:,.2f} MXN.
        - Desglose por categoría: {json.dumps(resumen_actual)}
        - Enfoques seleccionados en Action Hub: {preferencia_input}

        RECURSOS PARA OPERAR HOY:
        - Inyección Inmediata: ${cap_extra:,.2f} MXN.
        - Aportación Mensual Recurrente: ${aportacion:,.2f} MXN.

        REGLAS DE EJECUCIÓN FINANCIERA:
        1. PRIORIDAD DE LLENADO: Si una categoría está por debajo de su 'target_porcentaje', usa los ${cap_extra} preferentemente ahí. 
        2. CONCISIÓN: El diagnóstico y la acción inmediata deben ser breves y directos.
        3. HOJA DE RUTA ESPECÍFICA: En 'hoja_ruta_mensual', desglosa los ${aportacion} en montos exactos ($) por categoría. Varía los activos cada mes para diversificar.
        4. TEXTO LIMPIO: Prohibido usar asteriscos (**) o negritas en los valores del JSON.

        RESPUESTA REQUERIDA (JSON PURO):
        {{
            "riesgo_detectado": "Análisis breve de la desviación actual.",
            "nivel_riesgo": "Crítico/Alto/Medio/Bajo",
            "accion_inmediata": "Instrucción de inversión para los ${cap_extra} de hoy.",
            "hoja_ruta_mensual": [
                {{"mes": "Mes 1", "tarea": "Desglose de los ${aportacion}: $X en..., $Y en..."}},
                {{"mes": "Mes 2", "tarea": "Desglose de los ${aportacion}: $X en..., $Y en..."}},
                {{"mes": "Mes 3", "tarea": "Desglose de los ${aportacion}: $X en..., $Y en..."}},
                {{"mes": "Mes 4", "tarea": "Desglose de los ${aportacion}: $X en..., $Y en..."}}
            ],
            "porcentaje_objetivo": "Meta de equilibrio para este trimestre.",
            "justificacion": "Por qué este movimiento protege el capital hoy.",
            "hack_fiscal": "Consejo fiscal estratégico (LISR/SAT)."
        }}
        """

        # --- 5. LÓGICA DE MEMORIA (Continuidad Táctica) ---
        # Buscamos el plan anterior para que la IA no sea un "disco rayado"
        plan_anterior = NexusPlan.objects.filter(user=user).order_by('-created_at')[1:2].first()
        contexto_seguimiento = ""
        if plan_anterior:
            prev = plan_anterior.plan_json
            contexto_seguimiento = f"""
            \nSEGUIMIENTO: En el último plan recomendaste: {prev.get('accion_inmediata')}. 
            Ajusta los montos de la nueva hoja de ruta considerando si el usuario ya avanzó con ese plan."""

        # --- 6. CONFIGURACIÓN Y LLAMADA EN CASCADA (Gemini API) ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key: 
            raise ValueError("API Key no configurada en las variables de entorno.")

        genai.configure(api_key=api_key)

        # Jerarquía para asegurar que siempre haya una respuesta rápida
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
        prompt_final = prompt_sistema + contexto_seguimiento

        for model_name in MODELOS:
            try:
                # Limpiamos el nombre por si tiene el prefijo 'models/' del SDK anterior
                m_name = model_name.replace('models/', '')
                model = genai.GenerativeModel(m_name)
                
                respuesta = model.generate_content(prompt_final)
                texto_sucio = respuesta.text.strip()

                # --- 7. EXTRACCIÓN Y LIMPIEZA QUIRÚRGICA ---
                # Extraemos el bloque JSON y barremos con asteriscos para móviles
                match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
                if match:
                    # Limpiamos formatos de chat (**) para que el JSON sea puro
                    texto_limpio = match.group(0).replace('**', '').replace('*', '')
                    resultado_ia = json.loads(texto_limpio)
                    break 
            except Exception as e:
                ultimo_error = str(e)
                continue

        if not resultado_ia:
            raise ValueError(f"Falla total del motor NEXUS: {ultimo_error}")

        # --- 8. PERSISTENCIA Y SINCRONIZACIÓN FINAL ---
        
        # A. Guardamos el historial del Plan (Memoria de largo plazo)
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia_input,
            plan_json=resultado_ia
        )

        # B. Actualización del Perfil (Sincronización con Admin Django)
        # Aquí 'profile' ya viene definido desde la Parte 1
        if profile:
            profile.capital = cap_extra # Actualizamos el capital fresco
            profile.aportacion = aportacion # Actualizamos capacidad de ahorro
            profile.save()

        # Retornamos el objeto JSON listo para el Frontend
        return resultado_ia

    except Exception as e:
        # Registro técnico en logs del servidor
        print(f"!!! ERROR CRÍTICO NEXUS ENGINE !!!: {str(e)}")
        
        # Fallback controlado para que el usuario no vea una pantalla blanca
        return {
            "riesgo_detectado": "Anomalía en la red de procesamiento de rebalanceo.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Refresque su Action Hub e intente de nuevo.",
            "hoja_ruta_mensual": [{"mes": "Mes 1", "tarea": "Restableciendo parámetros financieros..."}],
            "porcentaje_objetivo": "N/A",
            "justificacion": f"Error técnico detectado: {str(e)[:60]}",
            "hack_fiscal": "Mantenga sus activos registrados para mejorar el diagnóstico."
        }