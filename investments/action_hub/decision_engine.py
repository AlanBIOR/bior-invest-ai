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
    Mecanismo de cascada para modelos, ahorro de tokens y adaptabilidad financiera total.
    """
    try:
        # --- 1. NORMALIZACIÓN DE DATOS ---
        cap_extra = float(capital_extra_input or 0)
        aportacion = float(aportacion_mensual_input or 0)
        preferencia = preferencia_input

        # --- 2. CACHÉ DE BASE DE DATOS (Ahorro de API / Persistencia) ---
        # Si la situación no ha cambiado, servimos el análisis guardado al instante
        ultimo_plan = NexusPlan.objects.filter(
            user=user, 
            capital_extra=cap_extra, 
            aportacion_mensual=aportacion, 
            preferencia_activo=preferencia
        ).order_by('-created_at').first()

        if ultimo_plan:
            return ultimo_plan.plan_json

        # --- 3. CONTEXTO PATRIMONIAL REAL ---
        profile = Profile.objects.filter(user=user).first()
        efectivo_en_dashboard = float(profile.capital) if profile and profile.capital else 0.0
        
        activos = Investment.objects.filter(user=user).select_related('category')
        total_invertido = float(activos.aggregate(total_cur=Sum('current_value'))['total_cur'] or 0.0)

        # Patrimonio sobre el cual el mentor tomará decisiones quirúrgicas
        capital_total_operativo = efectivo_en_dashboard + total_invertido + cap_extra
        
        desglose_activos = "\n".join([
            f"- {a.asset_name}: ${float(a.current_value or 0):,.2f} MXN ({a.category.name})" 
            for a in activos
        ])

        # --- 4. EL PROMPT MAESTRO (EL ALMA DEL AGENTE SENIOR) ---
        prompt_sistema = f"""
        PERSONALIDAD Y AUTORIDAD:
        Eres el Agente NEXUS, un legendario estratega patrimonial con más de 100 años de experiencia acumulada operando en las bolsas de Nueva York, Londres y los mercados emergentes de México. Has visto burbujas estallar y fortunas nacer. Tu misión es proteger y exponenciar el capital de {user.username}. Tu tono es sabio, directo, meticuloso y altamente estratégico.

        CONTEXTO FINANCIERO DEL USUARIO:
        - Patrimonio Neto Visible: ${capital_total_operativo:,.2f} MXN.
        - Efectivo actual en Dashboard: ${efectivo_en_dashboard:,.2f} MXN.
        - Capital NUEVO para inyectar HOY: ${cap_extra:,.2f} MXN.
        - Capacidad de ahorro mensual proyectada: ${aportacion:,.2f} MXN.
        - Enfoque deseado: "{preferencia}".
        - Portafolio actual:
        {desglose_activos if desglose_activos else "Sin activos registrados; capital listo para el primer despliegue."}

        METODOLOGÍA 'FLEXIBLE LONG ANGLE':
        Básate en la filosofía de 'Long Angle' (47% Renta Variable, 17% Inmuebles, 15% Private Equity, 8% Alternativas, 13% Efectivo), pero ADÁPTALA a la realidad económica del usuario. 
        - Si el capital es bajo (ej. menos de $100k MXN), no sugieras inmuebles físicos; prioriza FIBRAS (Monterrey, Danhos, Prologis) por su dividendo y exención fiscal.
        - Si el usuario prefiere "{preferencia}", potencia ese sector sin descuidar la supervivencia de la cartera.
        - Valora la liquidez: En México, el efectivo debe rendir. Sugiere Bonddia o SOFIPOS si detectas dinero ocioso.

        MARCO FISCAL MÉXICO (OBLIGATORIO):
        Eres experto en la LISR. Debes mencionar:
        1. SOFIPOS (Nu, Klar, etc): Límite de exención de 5 UMAs anuales (~$198,000 MXN). Si el usuario se acerca a este monto, advierte sobre la retención de ISR.
        2. Deducibilidad: Si tiene excedente de flujo, recomienda el PPR (Art. 151 LISR) para recuperar impuestos en abril.
        3. Declaración Informativa: Advierte si los movimientos anuales (préstamos/premios) superan los $600,000 MXN.

        TU OBJETIVO: Generar un plan de acción quirúrgico y motivador. Sé extenso y profundo en la justificación.

        RESPUESTA REQUERIDA (ÚNICAMENTE JSON VÁLIDO):
        {{
            "riesgo_detectado": "Análisis exhaustivo de vulnerabilidades actuales.",
            "nivel_riesgo": "Crítico, Alto, Medio o Bajo",
            "accion_inmediata": "Instrucción exacta paso a paso para HOY. Indica activo y plataforma sugerida (GBM+, CetesDirecto, Bitso).",
            "porcentaje_objetivo": "Meta de composición para este activo.",
            "justificacion": "Aquí despliega tu siglo de experiencia financiera. Explica el porqué matemático y estratégico de este movimiento bajo el actual entorno de tasas e inflación en México.",
            "hack_fiscal": "Consejo fiscal avanzado aplicable al monto y situación actual del usuario."
        }}
        """
        # --- 5. CONFIGURACIÓN DE HIERARQUÍA Y LLAMADA EN CASCADA ---
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("API Key no detectada en las variables de entorno del servidor.")

        genai.configure(api_key=api_key)

        # Jerarquía de modelos para asegurar continuidad del servicio
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

        # Iniciamos el ciclo de consulta
        for model_name in MODELOS_HIERARCHY:
            try:
                print(f"📡 NEXUS intentando consultar con: {model_name}...")
                model = genai.GenerativeModel(model_name)
                
                # Solicitamos la generación de contenido con el prompt masivo de la Parte 1
                respuesta = model.generate_content(prompt_sistema)
                texto_sucio = respuesta.text.strip()

                # --- 6. LÓGICA DE LIMPIEZA QUIRÚRGICA (Regex) ---
                # Esta lógica extrae el JSON incluso si la IA manda texto extra o bloques markdown
                texto_limpio = texto_sucio
                # Buscamos el patrón que empieza con { y termina con } de forma recursiva
                match = re.search(r'\{.*\}', texto_limpio, re.DOTALL)
                
                if match:
                    texto_limpio = match.group(0)
                else:
                    # Limpieza manual de emergencia si el regex falla
                    texto_limpio = texto_limpio.replace("```json", "").replace("```", "").strip()

                # Intentamos parsear el JSON definitivo
                resultado_ia = json.loads(texto_limpio)
                
                # Si llegamos aquí, el análisis fue exitoso. Rompemos el ciclo de modelos.
                print(f"✅ Éxito total. Respuesta obtenida de: {model_name}")
                break

            except (exceptions.ResourceExhausted, exceptions.ServiceUnavailable):
                print(f"⚠️ El modelo {model_name} agotó su cuota. Escalando al siguiente...")
                continue
            except Exception as e:
                print(f"❌ Error interno con {model_name}: {str(e)}")
                ultimo_error = str(e)
                continue

        # Si después de recorrer todos los modelos no hay respuesta, lanzamos error
        if not resultado_ia:
            raise ValueError(f"Falla crítica: Todos los modelos fallaron. {ultimo_error}")

        # --- 7. PERSISTENCIA PATRIMONIAL (Base de Datos) ---
        # Guardamos el plan para auditoría futura y para evitar re-consultas innecesarias
        NexusPlan.objects.create(
            user=user,
            capital_extra=cap_extra,
            aportacion_mensual=aportacion,
            preferencia_activo=preferencia,
            plan_json=resultado_ia
        )

        return resultado_ia

    except Exception as e:
        # Registro detallado en nohup.out para depuración técnica
        print(f"!!! ERROR CRÍTICO EN NEXUS ENGINE !!!")
        print(f"Usuario: {user.username} | Error: {str(e)}")
        
        # Fallback de seguridad para no romper la experiencia del usuario
        return {
            "riesgo_detectado": "Se detectó una anomalía en el núcleo de procesamiento.",
            "nivel_riesgo": "Medio",
            "accion_inmediata": "Refresque su navegador y reintente en 60 segundos.",
            "porcentaje_objetivo": "N/A",
            "justificacion": f"El Agente Senior detectó un problema de comunicación: {str(e)[:80]}...",
            "hack_fiscal": "Mantenga sus registros actualizados mientras restauramos el sistema."
        }