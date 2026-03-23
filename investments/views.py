import json
import requests  # Importante: para conectar con CoinGecko
from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.template import TemplateDoesNotExist
from django.db.models import Sum
from django.contrib import messages
from decimal import Decimal
from .models import Investment, Category, Profile
from .services import FinanceService
from django.utils import timezone

from django.views.decorators.csrf import csrf_exempt
from .core_ai import process_ai_request
from .core_ai.agents import ask_financial_agent  # Importamos tu agente de Gemini 2.5

# --- 1. REGISTRO & DASHBOARD ---
def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'auth/registro.html', {'form': form})

def dashboard(request):
    categorias = Category.objects.all()
    datos_lista = [
        {
            "name": cat.name, 
            "target_percentage": float(cat.target_percentage), 
            "description": cat.description
        } 
        for cat in categorias
    ]

    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(user=request.user)
        capital_inicial = profile.capital
        aportacion_mensual = profile.aportacion
    else:
        # Valores por defecto para usuarios no logueados (opcional)
        capital_inicial = 10000
        aportacion_mensual = 500

    context = {
        'categorias': categorias,
        'datos_js': json.dumps(datos_lista),
        'capital_inicial': capital_inicial,
        'aportacion_mensual': aportacion_mensual,
        # Pasamos la llave de n8n/webhook desde el .env al HTML de forma dinámica
        'n8n_key': settings.N8N_WEBHOOK_KEY, 
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
                amount = Decimal(amount_raw)
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

    # --- 2. ACTUALIZACIÓN DINÁMICA (Aquí suele estar el 500) ---
    todos_los_activos = Investment.objects.filter(user=request.user)
    ahora = timezone.now()

    # Blindaje para el tipo de cambio
    try:
        usd_rate_data = FinanceService.get_usd_mxn_rate()
        usd_mxn_rate = Decimal(str(usd_rate_data)) if usd_rate_data else Decimal('18.50')
    except:
        usd_mxn_rate = Decimal('18.50')

    for asset in todos_los_activos:
        try:
            if asset.category_id == 4: # Criptos
                api_id = asset.asset_name.lower().strip().replace(" ", "-")
                precio = FinanceService.get_crypto_price_mxn(api_id)
                if precio and asset.quantity and asset.quantity > 0:
                    asset.current_value = asset.quantity * Decimal(str(precio))
                    # Recalcular rendimiento
                    diff = asset.current_value - asset.amount_invested
                    asset.annual_yield = (diff / asset.amount_invested) * 100
            
            elif asset.annual_yield and asset.annual_yield > 0: # Renta Fija / Efectivo
                dias_pasados = (ahora - asset.last_updated).days
                if dias_pasados > 0:
                    tasa_diaria = (Decimal(str(asset.annual_yield)) / 100) / 365
                    asset.current_value = asset.current_value * (1 + (tasa_diaria * dias_pasados))
            
            asset.save()
        except Exception as e:
            print(f"Error actualizando activo {asset.asset_name}: {e}")

    # --- 3. CÁLCULOS PARA VISTA (Aggregations) ---
    try:
        activos = Investment.objects.filter(user=request.user).select_related('category')
        agg = activos.aggregate(total_inv=Sum('amount_invested'), total_cur=Sum('current_value'))
        
        total_inv = agg['total_inv'] or Decimal('0.00')
        total_cur = agg['total_cur'] or Decimal('0.00')
        
        datos_grafica = {}
        for a in activos:
            n = a.category.name
            datos_grafica[n] = datos_grafica.get(n, 0) + float(a.current_value)
        
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
        return render(request, 'pages/portafolio.html', {'error': True})

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
    # --- 1. VALIDACIÓN DE SEGURIDAD ---
    auth_header = request.headers.get('X-Api-Key')
    if auth_header != settings.N8N_WEBHOOK_KEY:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    if request.method == 'POST':
        try:
            # --- 2. LEER DATOS (JSON) ---
            data = json.loads(request.body)
            phone = data.get('phone')
            user_question = data.get('pregunta') # Aquí llega lo de Whisper o texto

            if not phone:
                return JsonResponse({"status": "error", "message": "Falta el teléfono"}, status=400)

            # --- 3. BUSCAR PERFIL Y DATOS ---
            try:
                profile = Profile.objects.get(whatsapp_number=phone)
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
                Usa los datos de arriba para contestar la pregunta del usuario.
                """

                # --- 5. LLAMAR A GEMINI (TU AGENTE) ---
                # Si no hay pregunta, damos un saludo con su saldo
                if user_question:
                    respuesta_final = ask_financial_agent(user_question, contexto_ia)
                else:
                    respuesta_final = f"Hola {user.username}, detecté tu mensaje pero no una pregunta clara. Tu capital es ${profile.capital} MXN. ¿En qué te ayudo?"

                return JsonResponse({
                    "status": "success",
                    "nombre": user.username,
                    "response": respuesta_final
                })

            except Profile.DoesNotExist:
                return JsonResponse({
                    "status": "success", 
                    "response": "Hola! No encontré tu número vinculado a BIOR Invest. Regístrate en la web para ayudarte."
                })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)
@login_required # Quitamos csrf_exempt para usar la seguridad de la sesión de la web
def ai_chat_webhook(request):
    """Webhook para el chat web: Seguro, privado y conectado a Gemini 2.5"""
    if request.method == 'POST':
        try:
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