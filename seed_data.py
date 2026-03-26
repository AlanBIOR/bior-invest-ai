import os
import django

# 1. Configurar el entorno de Django (esto debe ir PRIMERO)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. AHORA SI, importar el modelo (después de django.setup())
from investments.models import Category  # <--- REVISA QUE ESTA RUTA SEA CORRECTA

def seed_categories():
    categories = [
        {
            'name': 'Renta Variable', 
            'slug': 'renta-variable',
            'target_percentage': 47.00, 
            'description': 'ETFs (S&P 500), Acciones individuales e Internacionales'
        },
        {
            'name': 'Inmuebles', 
            'slug': 'inmuebles',
            'target_percentage': 17.00, 
            'description': 'Residencial, Alquiler a largo plazo y FIBRAS'
        },
        {
            'name': 'Private Equity', 
            'slug': 'private-equity',
            'target_percentage': 15.00, 
            'description': 'Empresas privadas, Search Funds y Venture Capital'
        },
        {
            'name': 'Inversiones Alternativas', 
            'slug': 'inversiones-alternativas',
            'target_percentage': 8.00, 
            'description': 'Criptomonedas, Oro, Materias primas y Coleccionables'
        },
        {
            'name': 'Efectivo', 
            'slug': 'efectivo',
            'target_percentage': 8.00, 
            'description': 'Cuentas remuneradas, depósitos y liquidez inmediata'
        },
        {
            'name': 'Renta Fija', 
            'slug': 'renta-fija',
            'target_percentage': 5.00, 
            'description': 'Bonos gubernamentales (CETES, bonos) y corporativos'
        },
    ]

    print("🌱 Sincronizando descripciones y porcentajes...")
    
    for cat_data in categories:
        # update_or_create es la clave aquí
        obj, created = Category.objects.update_or_create(
            slug=cat_data['slug'], # Busca por slug para no fallar
            defaults={
                'name': cat_data['name'],
                'target_percentage': cat_data['target_percentage'], 
                'description': cat_data['description'] # Esto llenará el <small>
            }
        )
        if created:
            print(f"✅ Creada: {obj.name}")
        else:
            print(f"🔄 Actualizada: {obj.name}")

if __name__ == '__main__':
    seed_categories()