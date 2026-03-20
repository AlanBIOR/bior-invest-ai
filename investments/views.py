from django.http import JsonResponse
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.template import TemplateDoesNotExist
from .models import Investment, Category

# 1. Registro (Abierto) - Vinculado al nuevo modelo User
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
    # Traemos las 6 categorías del script de siembra
    categorias = Category.objects.all()
    
    # Preparamos los datos para Chart.js y la calculadora
    datos_lista = [
        {
            "name": cat.name,
            "target_percentage": float(cat.target_percentage),
            "description": cat.description
        } for cat in categorias
    ]

    # Si el usuario está logueado, usamos sus preferencias; si no, valores default
    capital_inicial = request.user.capital if request.user.is_authenticated else 10000
    aportacion_mensual = request.user.aportacion if request.user.is_authenticated else 500

    context = {
        'categorias': categorias,
        'datos_js': json.dumps(datos_lista),
        'capital_inicial': capital_inicial,
        'aportacion_mensual': aportacion_mensual,
    }
    return render(request, 'investments/dashboard.html', context)

# 3. Portafolio (Gestión de Activos Reales)
@login_required
def portafolio(request):
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        asset_name = request.POST.get('asset_name')
        amount = request.POST.get('amount')
        platform = request.POST.get('platform')

        if category_id and amount:
            cat = get_object_or_404(Category, id=category_id)
            Investment.objects.create(
                user=request.user,
                category=cat,
                asset_name=asset_name,
                amount_invested=amount,
                current_value=amount, # Al inicio el valor actual es igual al invertido
                platform=platform
            )
            return redirect('portafolio')

    # Obtenemos los activos reales del usuario
    activos = Investment.objects.filter(user=request.user).select_related('category')
    total_invertido = sum(asset.amount_invested for asset in activos)
    valor_actual_total = sum(asset.current_value for asset in activos)
    
    # Datos para la gráfica de dona del portafolio REAL
    datos_grafica = {}
    for asset in activos:
        nombre = asset.category.name
        datos_grafica[nombre] = datos_grafica.get(nombre, 0) + float(asset.current_value)
    
    context = {
        'activos': activos,
        'categorias_list': Category.objects.all(), # Para el formulario de agregar
        'total_invertido': total_invertido,
        'valor_actual': valor_actual_total,
        'ganancia': valor_actual_total - total_invertido,
        'nombres_categorias': json.dumps(list(datos_grafica.keys())),
        'valores_categorias': json.dumps(list(datos_grafica.values())),
    }
    return render(request, 'pages/portafolio.html', context)

# 4. Configuración (Próximamente para editar capital/aportación)
@login_required
def configuracion(request):
    return render(request, 'pages/configuracion.html')

# 5. Páginas Legales
def terminos(request):
    return render(request, 'pages/terminos.html')

def privacidad(request):
    return render(request, 'pages/privacidad.html')

def disclaimer(request):
    return render(request, 'pages/disclaimer.html')

# 6. Detalle de Inversión (Dinámico)
def detalle_inversion(request, category_slug):
    # Forzamos que el slug use guiones bajos para que coincida con tus archivos .html
    slug_fijo = category_slug.replace('-', '_') 
    
    # Buscamos la categoría en la DB (ignorando si es guion medio o bajo)
    nombre_busqueda = category_slug.replace('-', ' ').replace('_', ' ')
    category = get_object_or_404(Category, name__iexact=nombre_busqueda)
    
    # Intentamos cargar el archivo que tienes en la carpeta detalles/
    template_path = f'detalles/{slug_fijo}.html'
    
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
            user = request.user
            user.capital = data.get('capital', user.capital)
            user.aportacion = data.get('aportacion', user.aportacion)
            user.save()
            return JsonResponse({'status': 'success', 'message': 'Progreso guardado en BD'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid_method'}, status=405)