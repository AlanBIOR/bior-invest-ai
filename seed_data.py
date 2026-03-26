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

    print("🌱 Actualizando estrategia Long Angle en BIOR Invest...")
    
    for cat_data in categories:
        # update_or_create es más rudo: si existe, LO CAMBIA. Si no, LO CREA.
        obj, created = Category.objects.update_or_create(
            name=cat_data['name'], # Busca por nombre
            defaults={
                'slug': cat_data['slug'],
                'target_percentage': cat_data['target_percentage'], 
                'description': cat_data['description']
            }
        )
        
        if created:
            print(f"✅ Creada: {obj.name}")
        else:
            print(f"🔄 Sobreescrita: {obj.name} -> {obj.target_percentage}%")

    print("\n🚀 ¡Base de datos sincronizada con la estrategia oficial!")