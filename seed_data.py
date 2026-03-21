import os
import django
from django.utils.text import slugify # Útil para generar slugs automáticamente

# Configuramos el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from investments.models import Category

def seed_categories():
    # Añadimos el campo 'slug' a cada diccionario
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

    print("🌱 Sembrando categorías estratégicas en BIOR Invest...")
    
    for cat_data in categories:
        # Usamos name para buscar, pero incluimos el slug en los defaults para la creación
        obj, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'slug': cat_data['slug'], # <--- El nuevo campo requerido
                'target_percentage': cat_data['target_percentage'], 
                'description': cat_data['description']
            }
        )
        
        if created:
            print(f"✅ Categoría creada: {obj.name} (slug: {obj.slug})")
        else:
            # Si ya existe, podemos aprovechar para actualizar el slug o la descripción por si acaso
            obj.slug = cat_data['slug']
            obj.target_percentage = cat_data['target_percentage']
            obj.description = cat_data['description']
            obj.save()
            print(f"🟡 Categoría actualizada: {obj.name}")

    print("\n🚀 ¡Configuración estratégica completada!")

if __name__ == '__main__':
    seed_categories()