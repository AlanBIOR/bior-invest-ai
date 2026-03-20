import json
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.template import TemplateDoesNotExist # Para manejar errores de archivos faltantes
from .models import Investment

# 1. Registro (Abierto)
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

# 2. Dashboard (Híbrido)
def dashboard(request):
    if request.user.is_authenticated:
        inversiones = Investment.objects.filter(user=request.user)
    else:
        inversiones = Investment.objects.none() 

    labels = [inv.get_category_display() for inv in inversiones]
    data_values = [str(inv.amount) for inv in inversiones]
    
    datos_js = {
        "labels": labels,
        "datasets": data_values
    }

    context = {
        'inversiones': inversiones,
        'datos_js': json.dumps(datos_js),
    }
    return render(request, 'investments/dashboard.html', context)

# 3. Portafolio (Privado)
@login_required
def portafolio(request):
    if request.method == 'POST':
        category = request.POST.get('category_id')
        amount = request.POST.get('amount')

        if category and amount:
            Investment.objects.create(
                user=request.user,
                category=category,
                amount=amount
            )
            return redirect('portafolio')

    activos = Investment.objects.filter(user=request.user)
    total_invertido = sum(asset.amount for asset in activos)
    
    datos_grafica = {}
    for asset in activos:
        nombre = asset.get_category_display()
        datos_grafica[nombre] = datos_grafica.get(nombre, 0) + float(asset.amount)
    
    context = {
        'activos': activos,
        'total_invertido': total_invertido,
        'valor_actual': total_invertido,
        'ganancia': 0,
        'nombres_categorias': json.dumps(list(datos_grafica.keys())),
        'valores_categorias': json.dumps(list(datos_grafica.values())),
    }
    return render(request, 'pages/portafolio.html', context)

# 4. Configuración (Privado)
@login_required
def configuracion(request):
    # Por ahora al admin, pronto a una página personalizada
    return redirect('admin:index')

# 5. Páginas Legales (Abiertas)
def terminos(request):
    return render(request, 'pages/terminos.html')

def privacidad(request):
    return render(request, 'pages/privacidad.html')

def disclaimer(request):
    return render(request, 'pages/disclaimer.html')

# 6. Detalle de Inversión (Dinámico)
def detalle_inversion(request, category_slug):
    """
    Busca el template específico en 'detalles/'. 
    Si no existe (ej. alguien inventa una URL), carga el genérico.
    """
    template_path = f'detalles/{category_slug}.html'
    
    try:
        return render(request, template_path, {'category': category_slug})
    except TemplateDoesNotExist:
        # Si no existe el archivo específico, mostramos el genérico por seguridad
        return render(request, 'pages/detalle_generic.html', {'category': category_slug})