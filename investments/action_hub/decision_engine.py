import os
import json
import re
import google.generativeai as genai
from google.api_core import exceptions
from django.db.models import Sum
from ..models import Profile, Investment, NexusPlan 

def generar_plan_decision_nexus(user, capital_extra_input=0, aportacion_mensual_input=0, preferencia_input="Equilibrado"):
    """
    NEXUS Engine v2.0: Consultor Patrimonial Senior con +100 años de experiencia.
    Analiza el portafolio REAL de la base de datos y personaliza según el capital del usuario.
    """
    try:
        # --- 1. NORMALIZACIÓN DE INPUTS DEL FRONTEND ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        preferencia = preferencia_input # Lista de enfoques (ej: "renta-variable, inmuebles")

        # --- 2. CACHÉ DE MEMORIA (Ahorro de API Tokens) ---
        # Si el usuario pide exactamente lo mismo que hace poco, no gastamos tokens
        ultimo_plan = NexusPlan.objects.filter(
            user=user, 
            capital_extra=cap_extra, 
            aportacion_mensual=aportacion, 
            preferencia_activo=preferencia
        ).order_by('-created_at').first()

        if ultimo_plan:
            return ultimo_plan.plan_json

        # --- 3. EXTRACCIÓN DE ADN FINANCIERO (Datos Reales de DB) ---
        profile = Profile.objects.filter(user=user).first()
        efectivo_dashboard = float(profile.capital) if profile and profile.capital else 0.0
        
        # Obtenemos todos tus activos reales (lo que se ve en tu imagen del admin)
        activos_reales = Investment.objects.filter(user=user).select_related('category')
        total_invertido = float(activos_reales.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)

        # Patrimonio Total Proyectado = Efectivo + Inversiones + Inyección Nueva
        capital_total_operativo = efectivo_dashboard + total_invertido + cap_extra
        
        # Construimos el reporte detallado para que la IA "vea" tu portafolio
        lista_activos_txt = "\n".join([
            f"- {a.asset_name}: ${float(a.current_value or 0):,.2f} MXN ({a.category.name})" 
            for a in activos_reales
        ])

        # --- 4. INGENIERÍA DE PROMPT MAESTRO (EL MENTOR DE 100 AÑOS) ---
        prompt_sistema = f"""
        ACTÚA COMO: El Agente NEXUS, un estratega financiero de élite con más de 100 años de experiencia acumulada. Eres un mentor sabio que ha visto crisis mundiales y burbujas. Tu misión es proteger y hacer crecer el patrimonio de {user.username}.

        CONTEXTO PATRIMONIAL REAL DEL USUARIO:
        - Patrimonio Total (Real + Inyección): ${capital_total_operativo:,.2f} MXN.
        - Capital EXTRA para invertir HOY: ${cap_extra:,.2f} MXN.
        - Aportación mensual planificada: ${aportacion:,.2f} MXN.
        - Enfoques deseados por el usuario: "{preferencia}".
        - Desglose de activos actuales en su cuenta:
        {lista_activos_txt if lista_activos_txt else "El usuario aún no tiene activos registrados, está iniciando de cero."}

        METODOLOGÍA DE ANÁLISIS:
        1. Tu brújula es la estrategia 'Long Angle' (47% Renta Variable, 17% Inmuebles, 15% Private Equity, 8% Alternativas, 13% Efectivo).
        2. ADAPTABILIDAD CRÍTICA: Sé flexible. Si el usuario tiene poco capital (ej: menos de $50k MXN), no sugieras comprar departamentos; prioriza FIBRAS (REITs mexicanos) o ETFs como VOO/VT. 
        3. RESPETO AL PERFIL: Si el usuario seleccionó enfoques específicos en "{preferencia}", dales prioridad en tu recomendación pero advierte si descuida la diversificación.
        4. EL FACTOR SAT (MÉXICO): 
           - SOFIPOS: Advierte sobre la retención de ISR si el saldo total en SOFIPOS supera las 5 UMAs anuales (~$198,000 MXN).
           - Art. 151 LISR: Si detectas capacidad de ahorro, sugiere el PPR para deducir impuestos.
           - Declaración Informativa: Si el capital total o aportaciones superan los $600,000 MXN anuales, recuérdale su obligación ante el SAT.

        TU OBJETIVO: Generar un plan de acción detallado, largo, quirúrgico y con autoridad.

        RESPUESTA REQUERIDA (ÚNICAMENTE UN OBJETO JSON VÁLIDO):
        {{
            "riesgo_detectado": "Análisis profundo sobre la concentración de riesgo o la falta de exposición en sectores clave.",
            "nivel_riesgo": "Crítico, Alto, Medio o Bajo",
            "accion_inmediata": "Instrucción exacta: qué activo comprar/vender hoy mismo con los ${cap_extra} MXN. Indica plataforma (GBM+, Bitso, CetesDirecto).",
            "porcentaje_objetivo": "Meta de composición para ese activo dentro del portafolio.",
            "justificacion": "Aquí despliega tu siglo de experiencia. Explica por qué este movimiento es matemáticamente superior para alguien con su nivel de capital actual.",
            "hack_fiscal": "Consejo fiscal avanzado de México aplicable a su monto de ${capital_total_operativo}."
        }}
        """
        # --- 5. CONFIGURACIÓN DE HIERARQUÍA Y LLAMADA EN CASCADA ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("API Key no detectada en las variables de entorno del servidor.")

        genai.configure(api_key=api_key)

        # Jerarquía solicitada para garantizar continuidad del servicio (Fallback)
        MODELOS_HIERARCHY = [
            'gemini-2.5-pro',
            'gemini-2.5-flash',
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite',
            'gemini-1.5-pro',
            'gemini-1.5-flash',
            'gemini-flash-latest',
            'gemini-pro-latest',
            'gemini-2.0-flash-001',
            'gemini-1.5-flash-8b'
        ]

        resultado_ia = None
        ultimo_error = ""

        # Iniciamos el ciclo de consulta a través de la jerarquía
        for model_path in MODELOS_HIERARCHY:
            try:
                # Limpiamos el prefijo 'models/' si es que el SDK lo requiere solo con el nombre
                model_name = model_path.replace('models/', '')
                print(f"📡 NEXUS consultando nivel de inteligencia: {model_name}...")
                
                model = genai.GenerativeModel(model_name)
                respuesta = model.generate_content(prompt_sistema)
                texto_sucio = respuesta.text.strip()

                # --- 6. LÓGICA DE LIMPIEZA QUIRÚRGICA (Regex) ---
                # Extraemos solo el objeto JSON, ignorando cualquier texto previo o posterior
                match = re.search(r'\{.*\}', texto_sucio, re.DOTALL)
                
                if match:
                    texto_limpio = match.group(0)
                else:
                    # Intento de limpieza manual si el regex no encuentra el bloque
                    texto_limpio = texto_sucio.replace("```json", "").replace("```", "").strip()

                # Intentamos parsear el JSON definitivo
                resultado_ia = json.loads(texto_limpio)
                
                # Si llegamos aquí, el análisis fue exitoso. Salimos del loop de modelos.
                print(f"✅ Análisis exitoso obtenido de: {model_name}")
                break

            except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable):
                print(f"⚠️ El modelo {model_name} alcanzó su cuota. Escalando al siguiente nivel...")
                continue
            except Exception as e:
                print(f"❌ Error con {model_name}: {str(e)}")
                ultimo_error = str(e)
                continue

        # Si después de recorrer toda la jerarquía no hay respuesta, lanzamos error crítico
        if not resultado_ia:
            raise ValueError(f"Falla total: Todos los modelos de Gemini fallaron. {ultimo_error}")

        # --- 7. PERSISTENCIA PATRIMONIAL (Memoria de NEXUS) ---
        # Guardamos el plan para auditoría y persistencia en el Dashboard
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        return resultado_ia

    except Exception as e:
        # Log para depuración en el servidor (nohup.out)
        print(f"!!! ERROR CRÍTICO EN NEXUS ENGINE !!!")
        print(f"Usuario: {user.username} | Error: {str(e)}")
        
        # Fallback de seguridad para el usuario final con el tono del Agente
        return {
            "riesgo_detectado": "Anomalía en la red de procesamiento de datos.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Refresque su Dashboard y reintente en 60 segundos.",
            "porcentaje_objetivo": "N/A",
            "justificacion": f"El Agente Senior detectó una interrupción técnica: {str(e)[:80]}...",
            "hack_fiscal": "Mantenga sus registros actualizados mientras restauramos el núcleo."
        }