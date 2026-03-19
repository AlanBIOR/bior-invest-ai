import json
from django.shortcuts import render
from .models import Investment

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
    return render(request, 'pages/portafolio.html')

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