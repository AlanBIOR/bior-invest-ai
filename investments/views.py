import json
import requests  # Importante: para conectar con CoinGecko
from django.http import JsonResponse
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

from django.views.decorators.csrf import csrf_exempt
from .core_ai import process_ai_request

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
        {"name": cat.name, "target_percentage": float(cat.target_percentage), "description": cat.description} 
        for cat in categorias
    ]

    if request.user.is_authenticated:
        profile, created = Profile.objects.get_or_create(user=request.user)
        capital_inicial = profile.capital
        aportacion_mensual = profile.aportacion
    else:
        capital_inicial = 10000
        aportacion_mensual = 500

    context = {
        'categorias': categorias,
        'datos_js': json.dumps(datos_lista),
        'capital_inicial': capital_inicial,
        'aportacion_mensual': aportacion_mensual,
    }
    return render(request, 'investments/dashboard.html', context)

# --- 2. PORTAFOLIO CON ACTUALIZACIÓN DE PRECIOS ---
@login_required
def portafolio(request):
    activos_alternativos = Investment.objects.filter(user=request.user, category_id=4)
    
    for asset in activos_alternativos:
        api_id = asset.asset_name.lower().strip().replace(" ", "-")
        precio_actual_api = FinanceService.get_crypto_price_mxn(api_id)
        
        if precio_actual_api:
            try:
                precio_entrada_simulado = Decimal('1200000') # Esto debe ser el precio cuando compraste
                if api_id == 'solana': precio_entrada_simulado = Decimal('2500')
                if api_id == 'dogecoin': precio_entrada_simulado = Decimal('2.50')

                unidades_poseidas = asset.amount_invested / precio_entrada_simulado
                asset.current_value = unidades_poseidas * Decimal(str(precio_actual_api))
                
                asset.save()
            except Exception as e:
                print(f"Error: {e}")

    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        asset_name = request.POST.get('asset_name')
        amount = Decimal(request.POST.get('amount_invested'))
        platform = request.POST.get('platform')
        yield_val = request.POST.get('annual_yield')
        
        yield_val = float(yield_val) if yield_val and yield_val.strip() else 0.0

        if category_id and amount:
            try:
                cat = get_object_or_404(Category, id=category_id)
                Investment.objects.create(
                    user=request.user, 
                    category=cat, 
                    asset_name=asset_name,
                    amount_invested=amount, 
                    current_value=amount, 
                    annual_yield=yield_val, 
                    platform=platform
                )
                messages.success(request, 'added')
                return redirect('portafolio')
            except Exception as e:
                messages.error(request, f"Error: {e}")

    activos = Investment.objects.filter(user=request.user).select_related('category')
    total_invertido = activos.aggregate(Sum('amount_invested'))['amount_invested__sum'] or 0
    valor_actual_total = activos.aggregate(Sum('current_value'))['current_value__sum'] or 0
    
    datos_grafica = {}
    for asset in activos:
        nombre = asset.category.name
        datos_grafica[nombre] = datos_grafica.get(nombre, 0) + float(asset.current_value)
    
    context = {
        'activos': activos,
        'categorias_list': Category.objects.all(),
        'total_invertido': total_invertido,
        'valor_actual': valor_actual_total,
        'ganancia': valor_actual_total - total_invertido,
        'nombres_categorias': json.dumps(list(datos_grafica.keys())),
        'valores_categorias': json.dumps(list(datos_grafica.values())),
    }
    
    return render(request, 'pages/portafolio.html', context)

@login_required
# --- 3. FUNCIONES DE APOYO & DETALLE ---
def get_cetes_rate(request):
    """Sustituye a get_cetes_rate.php"""
    serie = request.GET.get('series', 'SF43936')
    tasa = FinanceService.get_banxico_data(serie)
    return JsonResponse({'rate': tasa})

def detalle_inversion(request, category_slug):
    db_slug = category_slug.replace('_', '-')
    category = get_object_or_404(Category, slug=db_slug)
    template_slug = db_slug.replace('-', '_')
    template_path = f'detalles/{template_slug}.html'
    
    context = {
        'category': category,
        'activos': Investment.objects.filter(user=request.user, category=category) if request.user.is_authenticated else []
    }
    try:
        return render(request, template_path, context)
    except TemplateDoesNotExist:
        return render(request, 'pages/detalle_generic.html', context)

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

@csrf_exempt
def n8n_webhook(request):
    if request.method == 'POST':
        try:
            # 1. Recibimos el JSON de n8n
            data = json.loads(request.body)
            
            # 2. Procesamos con la lógica de tu carpeta core_ai
            result = process_ai_request(data)
            
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
            
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)