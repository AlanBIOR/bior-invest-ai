import json
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.template import TemplateDoesNotExist
from django.db.models import Sum
from django.contrib import messages
from .models import Investment, Category, Profile

# 1. Registro
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

# 2. Dashboard (Estrategia Sugerida)
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

# 3. Portafolio (Actualizado para asegurar datos de gráfica)
@login_required
def portafolio(request):
    if request.method == 'POST':
        # ... (toda tu lógica de guardado POST se mantiene igual, está perfecta)
        category_id = request.POST.get('category_id')
        asset_name = request.POST.get('asset_name')
        amount = request.POST.get('amount_invested')
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

    # LÓGICA DE CONSULTA
    activos = Investment.objects.filter(user=request.user).select_related('category')
    total_invertido = activos.aggregate(Sum('amount_invested'))['amount_invested__sum'] or 0
    valor_actual_total = activos.aggregate(Sum('current_value'))['current_value__sum'] or 0
    
    # Preparamos los datos para Chart.js
    datos_grafica = {}
    for asset in activos:
        nombre = asset.category.name
        # Sumamos el valor actual por cada nombre de categoría
        datos_grafica[nombre] = datos_grafica.get(nombre, 0) + float(asset.current_value)
    
    context = {
        'activos': activos,
        'categorias_list': Category.objects.all(),
        'total_invertido': total_invertido,
        'valor_actual': valor_actual_total,
        'ganancia': valor_actual_total - total_invertido,
        # Filtramos para que si no hay activos, no mande una gráfica vacía que de error
        'nombres_categorias': json.dumps(list(datos_grafica.keys())),
        'valores_categorias': json.dumps(list(datos_grafica.values())),
    }
    return render(request, 'pages/portafolio.html', context)

# NUEVA FUNCIÓN: API para que el JS no de error 404
def get_cetes_rate(request):
    # Aquí podrías conectar a Banxico en el futuro
    # Por ahora devolvemos un valor base para que tu main.js funcione
    return JsonResponse({'rate': 11.00})

# DETALLE INVERSION (Corregida la búsqueda en DB)
def detalle_inversion(request, category_slug):
    # Normalizamos: si entra 'renta_variable' buscamos 'renta-variable'
    db_slug = category_slug.replace('_', '-')
    
    # BUSCAMOS CON EL SLUG CORRECTO
    category = get_object_or_404(Category, slug=db_slug)
    
    # Cargamos el template usando guion bajo (como tus archivos reales)
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
    
# 4. Guardar Capital y Aportación (Dashboard AJAX)
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

# 5. Funciones de apoyo (Se mantienen igual)
@login_required
def eliminar_activo(request, pk):
    activo = get_object_or_404(Investment, pk=pk, user=request.user)
    activo.delete()
    messages.success(request, 'deleted')
    return redirect('portafolio')

@login_required
def configuracion(request):
    return render(request, 'pages/configuracion.html')

def detalle_inversion(request, category_slug):
    db_slug = category_slug.replace('_', '-')
    category = get_object_or_404(Category, slug=category_slug)
    template_slug = category_slug.replace('-', '_')
    template_path = f'detalles/{template_slug}.html'
    context = {
        'category': category,
        'activos': Investment.objects.filter(user=request.user, category=category) if request.user.is_authenticated else []
    }
    try:
        return render(request, template_path, context)
    except TemplateDoesNotExist:
        return render(request, 'pages/detalle_generic.html', context)

# Rutas legales
def terminos(request): return render(request, 'pages/terminos.html')
def privacidad(request): return render(request, 'pages/privacidad.html')
def disclaimer(request): return render(request, 'pages/disclaimer.html')