import os, json, re, google.generativeai as genai
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan, Category, GlobalAsset 

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS v3.2: Arquitectura de Rebalanceo Táctico Dinámico.
    La IA lee los activos disponibles en tiempo real desde la Base de Datos.
    """
    try:
        # --- 1. NORMALIZACIÓN DE DATOS DE ENTRADA ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        
        # --- 2. MODELO IDEAL Y CATÁLOGO DINÁMICO (DESDE LA BD) ---
        categorias_db = Category.objects.all()
        modelo_objetivo = {
            cat.slug: {
                "nombre": cat.name,
                "target_porcentaje": float(cat.target_percentage)
            } for cat in categorias_db
        }

        # Extraemos el catálogo vivo desde la Base de Datos
        activos_globales = GlobalAsset.objects.filter(is_active=True, category__isnull=False)
        catalogo_dinamico = "CATÁLOGO DE ACTIVOS PERMITIDOS (Elige opciones variadas de aquí):\n"
        
        for cat in categorias_db:
            activos_de_esta_cat = activos_globales.filter(category=cat)
            if activos_de_esta_cat.exists():
                nombres_activos = [f"{a.name} (vía {a.platform or 'Broker'})" for a in activos_de_esta_cat]
                catalogo_dinamico += f"- {cat.name.upper()}: {', '.join(nombres_activos)}\n"

        # Salvavidas por si la BD está vacía
        if not activos_globales.exists():
            catalogo_dinamico = "CATÁLOGO DE ACTIVOS: Usa ETFs como VOO, VT, Cetes, FIBRAS y Nu México."

        # --- 3. REALIDAD PATRIMONIAL ---
        profile = Profile.objects.filter(user=user).first()
        activos_reales = Investment.objects.filter(user=user).select_related('category')
        total_invertido = float(activos_reales.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)
        
        resumen_actual = {}
        for a in activos_reales:
            slug = a.category.slug
            resumen_actual[slug] = resumen_actual.get(slug, 0) + float(a.current_value)

        # --- 4. CONFIGURACIÓN DEL PROMPT ---
        prompt_sistema = f"""
        Eres NEXUS, un estratega senior institucional. 
        TU MISIÓN: Aplicar REBALANCEO TÁCTICO con un tono ejecutivo, profesional y sin emojis. 

        {catalogo_dinamico}

        CONTEXTO TÉCNICO:
        - MODELO OBJETIVO (LONG ANGLE): {json.dumps(modelo_objetivo)}
        - REALIDAD PATRIMONIAL DE {user.username.upper()}:
          * Total Invertido: ${total_invertido:,.2f} MXN.
          * Composición Actual: {json.dumps(resumen_actual)}
        - ENFOQUES SELECCIONADOS: {preferencia_input}
        - Inyección Inmediata: ${cap_extra:,.2f} MXN.
        - Aportación Mensual: ${aportacion:,.2f} MXN.

        REGLAS DE EJECUCIÓN:
        1. DINAMISMO MENSUAL: Obligatorio rotar los activos en la hoja de ruta. No repitas la misma instrucción los 4 meses. Diversifica usando el catálogo proporcionado.
        2. PRIORIDAD: Si una categoría tiene un déficit, asigna el capital prioritariamente ahí para cerrar la brecha.
        3. ESTRUCTURA DE RESPUESTA: Usa Markdown (### para títulos, listas con guiones y negritas).
        4. ESPECIFICIDAD: Divide la aportación de ${aportacion} en al menos 2 activos distintos por mes, mencionando montos exactos y el nombre del activo/plataforma sugerido del catálogo.
        5. TONO: Profesional, analítico y sobrio. Prohibido el uso de emojis.

        RESPUESTA JSON REQUERIDA:
        {{
            "riesgo_detectado": "### Análisis de Desviación Patrimonial\\n- **Estado Actual**: [Describir distribución actual]\\n- **Déficit Identificado**: [Mencionar qué categorías faltan vs el objetivo]\\n- **Impacto**: [Riesgo técnico de no rebalancear]",
            "nivel_riesgo": "Crítico/Alto/Medio/Bajo",
            "accion_inmediata": "Instrucción de ejecución inmediata para los ${cap_extra}: Dividir $X en [Activo A] y $Y en [Activo B].",
            "hoja_ruta_mensual": [
                {{"mes": "Mes 1", "tarea": "Invertir ${aportacion}: $X en [Activo A] y $Y en [Activo B]..."}},
                {{"mes": "Mes 2", "tarea": "Invertir ${aportacion}: $X en [Activo C] y $Y en [Activo D]..."}},
                {{"mes": "Mes 3", "tarea": "Invertir ${aportacion}: $X en [Activo E] y $Y en [Activo F]..."}},
                {{"mes": "Mes 4", "tarea": "Invertir ${aportacion}: $X en [Activo G] y $Y en [Activo H]..."}}
            ],
            "porcentaje_objetivo": "Meta de composición proyectada tras 4 meses.",
            "justificacion": "Análisis técnico de por qué esta distribución diversificada optimiza el riesgo-retorno.",
            "hack_fiscal": "### Estrategia de Optimización Fiscal\\n- **Mecánica**: [Explicación técnica del beneficio]\\n- **Ventaja Real**: [Ahorro porcentual o beneficio en flujo neto]"
        }}
        """

        # --- 6. LÓGICA DE MEMORIA (Continuidad Táctica) ---
        # Buscamos el plan anterior para que la IA no sea un "disco rayado"
        plan_anterior = NexusPlan.objects.filter(user=user).order_by('-created_at')[1:2].first()
        contexto_seguimiento = ""
        if plan_anterior:
            prev = plan_anterior.plan_json
            contexto_seguimiento = f"""
            \nSEGUIMIENTO: En el último plan recomendaste: {prev.get('accion_inmediata')}. 
            Ajusta los montos y activos de la nueva hoja de ruta considerando esta memoria para dar variedad."""

        # --- 7. CONFIGURACIÓN Y LLAMADA EN CASCADA (Gemini API) ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key: 
            raise ValueError("API Key no configurada en las variables de entorno.")

        genai.configure(api_key=api_key)

        # Jerarquía para asegurar que siempre haya una respuesta rápida
        MODELOS = [
            'gemini-2.0-flash',          # La mejor opción actual: rápido y preciso
            'gemini-2.0-flash-lite',     # El más ligero, ideal para evitar Time-outs
            'gemini-1.5-flash',          # Respaldo ultra-confiable
            'gemini-1.5-flash-8b',       # Pequeño pero matón para tareas de JSON
            'gemini-2.0-flash-001',      # Versión específica estable
            'gemini-flash-latest',       # Alias para la última versión flash
            # Los 'Pro' se quedan al final como último recurso
            'gemini-1.5-pro',            
            'gemini-pro-latest'
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

                # --- 8. EXTRACCIÓN Y LIMPIEZA QUIRÚRGICA ---
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

        # --- 9. PERSISTENCIA Y SINCRONIZACIÓN FINAL ---
        
        # A. Guardamos el historial del Plan (Memoria de largo plazo)
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia_input,
            plan_json=resultado_ia
        )

        # B. Actualización del Perfil (Sincronización con Admin Django)
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