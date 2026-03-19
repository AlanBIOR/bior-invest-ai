import json
from django.shortcuts import render
from .models import Investment
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.shortcuts import render, redirect

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
    inversiones = Investment.objects.all()
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

# --- Nuevas funciones para evitar el AttributeError ---

def portafolio(request):
    activos = Investment.objects.all()
    total_invertido = sum(asset.amount for asset in activos)
    
    # Lógica para la gráfica (Agrupar por categoría)
    datos_grafica = {}
    for asset in activos:
        nombre = asset.get_category_display()
        datos_grafica[nombre] = datos_grafica.get(nombre, 0) + float(asset.amount)
    
    context = {
        'activos': activos,
        'total_invertido': total_invertido,
        'valor_actual': total_invertido, # Por ahora igual
        'ganancia': 0,
        'nombres_categorias': json.dumps(list(datos_grafica.keys())),
        'valores_categorias': json.dumps(list(datos_grafica.values())),
    }
    return render(request, 'pages/portafolio.html', context)

def configuracion(request):
    return render(request, 'pages/configuracion.html')

def terminos(request):
    return render(request, 'pages/terminos.html')

def privacidad(request):
    return render(request, 'pages/privacidad.html')

def disclaimer(request):
    return render(request, 'pages/disclaimer.html')

def detalle_inversion(request, category_slug):
    # Esta función es dinámica, luego la conectaremos con los datos reales
    context = {'category': category_slug}
    return render(request, 'detalles/detalle_generic.html', context)