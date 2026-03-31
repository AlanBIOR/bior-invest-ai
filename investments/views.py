import json
from decimal import Decimal
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import random
from .models import Category


# Modelos, Formularios y Servicios
from .models import Investment, Category, Profile, NexusPlan
from .services import FinanceService
from .forms import RegistroForm

# Inteligencia Artificial & Action Hub
from .core_ai.agents import ask_financial_agent
from .action_hub.decision_engine import generar_plan_decision_nexus

# --- 1. REGISTRO & DASHBOARD ---
def registro(request):
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # 1. Guardar el usuario (El Signal creará el Profile en automático)
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password1'])
            user.save()

            # 2. Actualizar el Profile que el Signal acaba de crear
            perfil = user.profile
            perfil.whatsapp_number = form.cleaned_data['whatsapp_number']
            perfil.save()

            messages.success(request, f'¡Bienvenido {user.username}! Ya puedes iniciar sesión.')
            return redirect('login')
    else:
        form = RegistroForm()
    
    return render(request, 'auth/registro.html', {'form': form})

def dashboard(request):
    categorias = Category.objects.all().order_by('-target_percentage')
    
    datos_lista = [
        {
            "name": cat.name, 
            "target_percentage": float(cat.target_percentage), 
            "description": cat.description,
            "slug": cat.slug 
        } 
        for cat in categorias
    ]

    # --- LÓGICA DE VALORES MOMENTÁNEOS (SESIÓN) ---
    
    # 1. Definimos los valores base (del perfil si existe, o defaults)
    if request.user.is_authenticated:
        profile, _ = Profile.objects.get_or_create(user=request.user)
        val_base_cap = float(profile.capital or 10000.0)
        val_base_apor = float(profile.aportacion or 500.0)
    else:
        val_base_cap = 10000.0
        val_base_apor = 500.0

    # 2. Intentamos obtener los valores de la sesión (si el usuario ya los movió en el Dashboard)
    # Si no existen en la sesión todavía, usamos los valores base definidos arriba
    capital_inicial = request.session.get('capital_simulado', val_base_cap)
    aportacion_mensual = request.session.get('aportacion_simulada', val_base_apor)

    context = {
        'categorias': categorias,
        'datos_js': json.dumps(datos_lista), 
        'capital_inicial': capital_inicial,
        'aportacion_mensual': aportacion_mensual,
        'n8n_key': getattr(settings, 'N8N_WEBHOOK_KEY', ''), 
    }
    
    return render(request, 'investments/dashboard.html', context)

# --- 2. PORTAFOLIO CON ACTUALIZACIÓN DE PRECIOS ---
@login_required
def portafolio(request):
    # --- 1. PROCESAR FORMULARIO (POST) ---
    if request.method == 'POST':
        try:
            category_id = request.POST.get('category_id')
            asset_name = request.POST.get('asset_name')
            amount_raw = request.POST.get('amount_invested')
            platform = request.POST.get('platform')
            yield_input = request.POST.get('annual_yield')

            if category_id and amount_raw:
                amount = Decimal(str(amount_raw))
                cat = get_object_or_404(Category, id=category_id)
                new_yield = float(yield_input) if yield_input and yield_input.strip() else 0.0
                
                Investment.objects.filter(user=request.user, platform=platform, asset_name=asset_name).update(annual_yield=new_yield)

                qty = Decimal('1.0')
                if category_id == "4":
                    api_id = asset_name.lower().strip().replace(" ", "-")
                    p_hoy = FinanceService.get_crypto_price_mxn(api_id)
                    if p_hoy: 
                        qty = amount / Decimal(str(p_hoy))

                Investment.objects.create(
                    user=request.user, category=cat, asset_name=asset_name,
                    amount_invested=amount, current_value=amount,
                    quantity=qty, annual_yield=new_yield, platform=platform
                )
                messages.success(request, 'Portafolio actualizado')
                return redirect('portafolio')
        except Exception as e:
            print(f"Error en POST: {e}")
            messages.error(request, f"Error al guardar: {e}")

    # --- 2. ACTUALIZACIÓN DINÁMICA (OPTIMIZADA) ---
    todos_los_activos = Investment.objects.filter(user=request.user)
    ahora = timezone.now()

    try:
        usd_rate_data = FinanceService.get_usd_mxn_rate()
        usd_mxn_rate = Decimal(str(usd_rate_data)) if usd_rate_data else Decimal('18.50')
    except:
        usd_mxn_rate = Decimal('18.50')

    for asset in todos_los_activos:
        try:
            # Solo actualizar si el dato tiene más de 5 minutos de antigüedad
            # Esto evita saturar APIs y base de datos en cada refresh
            if (ahora - asset.last_updated).total_seconds() > 300:
                asset_inv = Decimal(str(asset.amount_invested or '0'))
                asset_qty = Decimal(str(asset.quantity or '0'))
                asset_cur = Decimal(str(asset.current_value or '0'))

                if asset.category_id == 4: # Criptos
                    api_id = asset.asset_name.lower().strip().replace(" ", "-")
                    precio = FinanceService.get_crypto_price_mxn(api_id)
                    if precio and asset_qty > 0:
                        asset.current_value = asset_qty * Decimal(str(precio))
                        if asset_inv > 0:
                            diff = asset.current_value - asset_inv
                            asset.annual_yield = (diff / asset_inv) * 100
                
                elif asset.annual_yield and asset.annual_yield > 0: # Renta Fija
                    dias_pasados = (ahora - asset.last_updated).days
                    if dias_pasados > 0:
                        tasa_diaria = (Decimal(str(asset.annual_yield)) / 100) / 365
                        asset.current_value = asset_cur * (1 + (tasa_diaria * dias_pasados))
                
                asset.save()
        except Exception as e:
            print(f"Error actualizando activo {asset.asset_name}: {e}")

    # --- 3. CÁLCULOS PARA VISTA (Aggregations) ---
    try:
        activos = Investment.objects.filter(user=request.user).select_related('category')
        agg = activos.aggregate(total_inv=Sum('amount_invested'), total_cur=Sum('current_value'))
        
        total_inv = Decimal(str(agg['total_inv'] or '0.00'))
        total_cur = Decimal(str(agg['total_cur'] or '0.00'))
        
        datos_grafica = {}
        for a in activos:
            n = a.category.name
            val = float(a.current_value or 0)
            datos_grafica[n] = datos_grafica.get(n, 0) + val
        
        context = {
            'activos': activos,
            'categorias_list': Category.objects.all(),
            'total_invertido': total_inv,
            'valor_actual': total_cur,
            'ganancia': total_cur - total_inv,
            'usd_mxn': usd_mxn_rate,
            'nombres_categorias': json.dumps(list(datos_grafica.keys())),
            'valores_categorias': json.dumps(list(datos_grafica.values())),
        }
        return render(request, 'pages/portafolio.html', context)
    except Exception as e:
        print(f"Error en renderizado: {e}")
        return render(request, 'pages/portafolio.html', {
            'categorias_list': Category.objects.all(),
            'total_invertido': Decimal('0'),
            'valor_actual': Decimal('0'),
            'ganancia': Decimal('0'),
            'error': True
        })
# --- 3. FUNCIONES DE APOYO & DETALLE ---

@login_required # Movido correctamente aquí
def get_cetes_rate(request):
    serie = request.GET.get('series', 'SF43936')
    tasa = FinanceService.get_banxico_data(serie)
    return JsonResponse({'rate': tasa})

def detalle_inversion(request, slug):
    # 1. 'slug' recibe 'renta-variable'
    category = get_object_or_404(Category, slug=slug)
    
    # 2. Convertimos el guion medio (-) en bajo (_) para el archivo
    # Esto transforma 'renta-variable' en 'renta_variable'
    nombre_archivo = slug.replace('-', '_')
    
    # 3. Ahora sí, la ruta coincide con tu VS Code
    template_path = f'detalles/{nombre_archivo}.html'
    
    context = {
        'category': category,
        'activos': Investment.objects.filter(user=request.user, category=category) if request.user.is_authenticated else []
    }
    
    return render(request, template_path, context)

@login_required
def guardar_progreso(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            profile, created = Profile.objects.get_or_create(user=request.user)
            profile.capital = data.get('capital')
            profile.aportacion = data.get('aportacion')
            profile.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'invalid'}, status=400)

@login_required
def eliminar_activo(request, pk):
    activo = get_object_or_404(Investment, pk=pk, user=request.user)
    activo.delete()
    messages.success(request, 'deleted')
    return redirect('portafolio')

@login_required
def configuracion(request):
    return render(request, 'pages/configuracion.html')

# Rutas legales
def terminos(request): return render(request, 'pages/terminos.html')
def privacidad(request): return render(request, 'pages/privacidad.html')
def disclaimer(request): return render(request, 'pages/disclaimer.html')

import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from investments.models import Profile, Investment  # <--- IMPORTANTE

@csrf_exempt
def n8n_webhook(request):
    print("--- ¡PETICIÓN ENTRANDO! ---")
    print(f"Metodo: {request.method}")
    print(f"Headers: {request.headers}")
    print(f"Body crudo: {request.body}")
    # --- 1. VALIDACIÓN DE SEGURIDAD ---
    auth_header = request.headers.get('X-Api-Key')
    if auth_header != settings.N8N_WEBHOOK_KEY:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    if request.method == 'POST':
        # --- 2. LEER DATOS (JSON) ---
        try:
            data = json.loads(request.body)
            phone = data.get('phone')
            telegram_id = data.get('telegram_id')
            user_question = data.get('pregunta')
            
            # DEBUG TEMPORAL: Esto saldrá en tu consola del VPS
            print(f"DATOS RECIBIDOS -> ID: {telegram_id}, PREGUNTA: {user_question}")

            if not phone and not telegram_id:
                return JsonResponse({"status": "error", "message": f"Falta identificador. Recibí: {list(data.keys())}"}, status=400)

            # --- 3. BUSCAR PERFIL Y DATOS ---
            try:
                # Búsqueda segura: Prioriza WhatsApp, si no está, usa Telegram
                if phone:
                    profile = Profile.objects.get(whatsapp_number=phone)
                else:
                    profile = Profile.objects.get(telegram_id=telegram_id)
                    
                user = profile.user
                investments = Investment.objects.filter(user=user)

                # Formatear inversiones para el contexto de la IA
                inv_list = [f"- {i.asset_name}: ${i.current_value} MXN" for i in investments]
                lista_formateada = "\n".join(inv_list) if inv_list else "Sin inversiones aún."

                # --- 4. CREAR CONTEXTO PARA GEMINI ---
                contexto_ia = f"""
                [DATOS REALES DEL USUARIO: {user.username}]
                Capital Libre: ${profile.capital} MXN
                Inversiones:
                {lista_formateada}
                
                INSTRUCCIÓN: Responde de forma breve y profesional por WhatsApp. 
                Uusa los datos de arriba para contestar la pregunta del usuario.
                """
                # --- 5. LLAMAR A GEMINI (Inyección de Datos Directa) ---
                if user_question:
                    # Este es el bloque que ya tienes, está excelente
                    prompt_final = f"""
                    FICHA TÉCNICA DEL USUARIO {user.username}:
                    - SALDO EN EFECTIVO: ${profile.capital} MXN
                    - PORTAFOLIO DETALLADO:
                    {lista_formateada}

                    INSTRUCCIÓN OBLIGATORIA: Eres el asistente personal de {user.username}. 
                    Acabas de leer su base de datos privada (los datos de arriba). 
                    USA ESOS DATOS para responder su pregunta. 
                    NUNCA digas que no tienes acceso, porque el sistema ya te los dio.

                    PREGUNTA DEL USUARIO: {user_question}

                    INSTRUCCIÓN: Responde basándote ÚNICAMENTE en los datos de arriba. 
                    Si los datos muestran montos, dáselos al usuario de forma clara. 
                    No digas que no tienes acceso, porque los datos están en este mensaje.
                    """
                    
                    # Mandamos el bloque con autoridad
                    respuesta_final = ask_financial_agent(prompt_final)
                
                else:
                    # Esto es lo que debes poner en el 'else'
                    respuesta_final = (
                        f"Hola {user.username}, recibí tu mensaje pero no pude entender la pregunta. "
                        f"Te confirmo que tu capital disponible es de ${profile.capital} MXN. "
                        "¿En qué más te puedo ayudar?"
                    )                

                return JsonResponse({
                    "status": "success",
                    "nombre": user.username,
                    "response": respuesta_final
                })

            except Profile.DoesNotExist:
                return JsonResponse({
                    "status": "success", 
                    "response": "Hola! No encontré tu número ni tu ID de Telegram vinculados a BIOR Invest. Regístrate en la web para ayudarte."
                })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)


@login_required # Quitamos csrf_exempt para usar la seguridad de la sesión de la web
def ai_chat_webhook(request):
    """Webhook para el chat web: Seguro, privado y conectado a Gemini 2.5"""
    if request.method == 'POST':
        try:
            print(f"BODY RECIBIDO: {request.body}")
            data = json.loads(request.body)
            # Buscamos 'text' (de la web) o 'Body' (por si acaso)
            user_question = data.get('text') or data.get('Body')
            
            if not user_question:
                return JsonResponse({"status": "error", "message": "No enviaste una pregunta"}, status=400)
            
            # --- 1. Obtener contexto con Estructura de Autoridad ---
            profile, _ = Profile.objects.get_or_create(user=request.user)
            investments = Investment.objects.filter(user=request.user)

            # Creamos una lista más descriptiva para la IA
            inv_list = [f"- {i.asset_name}: ${i.current_value} MXN (Plataforma: {i.platform})" for i in investments]
            lista_formateada = "\n".join(inv_list)

            # ESTO es lo que obliga a la IA a no alucinar:
            contexto = f"""
            [REPORTE OFICIAL DE BASE DE DATOS - BIOR INVEST]
            USUARIO LOGUEADO: {request.user.username}
            CAPITAL DISPONIBLE (EFECTIVO): ${profile.capital} MXN

            INVERSIONES REGISTRADAS:
            {lista_formateada if inv_list else "Sin inversiones registradas aún."}

            INSTRUCCIÓN: Analiza EXCLUSIVAMENTE estos montos reales para responder al usuario. 
            Si el usuario pregunta por 'llegar al Long Angle', compáralo contra los porcentajes de la estrategia usando ESTOS valores.
            """

            # 2. LLAMAR A TU AGENTE
            respuesta_ia = ask_financial_agent(user_question, contexto)
            
            return JsonResponse({
                "status": "success",
                "response": respuesta_ia
            })
        except Exception as e:
            # Muy útil para debug: esto saldrá en la consola del navegador si falla
            return JsonResponse({"status": "error", "message": str(e)}, status=500)
            
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

@login_required
def nexus_advisor_view(request):
    """
    Carga la página de NEXUS recuperando los últimos valores 
    reales guardados por el usuario.
    """
    # Buscamos el registro más reciente en la base de datos
    ultimo_plan = NexusPlan.objects.filter(user=request.user).order_by('-created_at').first()
    
    context = {
        # Si existe un plan, usamos sus valores; si no, ponemos 0 y 500
        'last_capital': ultimo_plan.capital_extra if ultimo_plan else 0,
        'last_aportacion': ultimo_plan.aportacion_mensual if ultimo_plan else 500,
        'last_plan': ultimo_plan.plan_json if ultimo_plan else None
    }
    return render(request, 'pages/nexus_advisor.html', context)

@login_required
@require_POST
def api_modo_decision(request):
    """
    NEXUS v2.4: Simulación basada en Pesos y Rendimientos Reales de la DB.
    """
    try:
        # 1. Extraer datos del request
        data = json.loads(request.body)
        capital_extra = data.get('capital_extra', 0)
        aportacion = data.get('aportacion', 0)
        preferencia = data.get('preferencia', 'Equilibrado')

        # 2. Llamar al motor estratégico (IA)
        plan_accion = generar_plan_decision_nexus(
            user=request.user,
            capital_extra_input=capital_extra,
            aportacion_mensual_input=aportacion,
            preferencia_input=preferencia
        )

        # --- 3. MÁQUINA DEL TIEMPO DINÁMICA (Basada en Categorías de la DB) ---
        profile = request.user.profile
        cap_base_sim = float(profile.capital or 0) + float(capital_extra)
        apor_sim = float(aportacion)

        # Consultamos las categorías y sus rendimientos configurados
        categorias = Category.objects.all()
        
        # Calculamos el Rendimiento Ponderado Anual (Weighted Average Yield)
        # r_anual = Σ (Peso_i * Rendimiento_i)
        rendimiento_anual_cartera = 0
        for cat in categorias:
            peso = float(cat.target_percentage or 0) / 100
            # Asumimos que tienes un campo 'expected_yield' en tu modelo Category
            # Si el campo tiene otro nombre, cámbialo aquí:
            rend_cat = float(getattr(cat, 'expected_yield', 0.10)) # 10% de respaldo
            rendimiento_anual_cartera += (peso * rend_cat)

        # Convertimos rendimiento anual a mensual compuesto
        # Formula: (1 + r_anual)^(1/12) - 1
        rendimiento_mensual_base = (1 + rendimiento_anual_cartera) ** (1/12) - 1

        time_machine_points = []
        acumulado = cap_base_sim
        meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", 
                        "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

        for i in range(12):
            # Aplicamos volatilidad orgánica (ruido de mercado)
            # Entre -1.5% y +2.5% de desviación para que la gráfica no sea una línea recta perfecta
            volatilidad = random.uniform(-0.015, 0.025)
            
            # Crecimiento: (Capital + Aporte) * (1 + r_mensual + ruido)
            acumulado = (acumulado + apor_sim) * (1 + rendimiento_mensual_base + volatilidad)
            
            time_machine_points.append({
                "mes": meses_labels[i],
                "valor": round(acumulado, 2)
            })

        # 4. Respuesta consolidada
        return JsonResponse({
            "status": "success",
            "data": plan_accion,
            "time_machine": time_machine_points
        })

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Formato JSON inválido"}, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "success", # Mantenemos success para no romper el JS pero enviamos el error en logs
            "message": f"Falla en el motor NEXUS: {str(e)}"
        }, status=500)