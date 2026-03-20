import os
import django

# Configuramos el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from investments.models import Category

def seed_categories():
    categories = [
        {
            'name': 'Renta Variable', 
            'target_percentage': 47.00, 
            'description': 'ETFs (S&P 500), Acciones individuales e Internacionales'
        },
        {
            'name': 'Inmuebles', 
            'target_percentage': 17.00, 
            'description': 'Residencia principal, Alquiler a largo plazo y Vacacional'
        },
        {
            'name': 'Private Equity', 
            'target_percentage': 15.00, 
            'description': 'Empresas privadas, Search Funds y Venture Capital'
        },
        {
            'name': 'Inversiones Alternativas', 
            'target_percentage': 8.00, 
            'description': 'Criptomonedas, Oro, Materias primas y Coleccionables'
        },
        {
            'name': 'Efectivo', 
            'target_percentage': 8.00, 
            'description': 'Cuentas remuneradas, depósitos y liquidez inmediata'
        },
        {
            'name': 'Renta Fija', 
            'target_percentage': 5.00, 
            'description': 'Bonos gubernamentales (EE.UU.) y corporativos'
        },
    ]

    print("🌱 Sembrando categorías en la base de datos...")
    
    for cat_data in categories:
        # get_or_create evita que se dupliquen si corres el script dos veces
        obj, created = Category.objects.get_or_create(
            name=cat_data['name'],
            defaults={
                'target_percentage': cat_data['target_percentage'], 
                'description': cat_data['description']
            }
        )
        if created:
            print(f"✅ Categoría creada: {obj.name}")
        else:
            print(f"🟡 La categoría ya existía: {obj.name}")

    print("\n🚀 ¡Siembra completada!")

if __name__ == '__main__':
    seed_categories()