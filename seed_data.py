import os
import django

# 1. Configurar el entorno de Django (esto debe ir PRIMERO)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# 2. AHORA SI, importar los modelos (después de django.setup())
from investments.models import Category, GlobalAsset

# --- PARTE 1: CATEGORÍAS ---
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

    print("🌱 Sincronizando Categorías, descripciones y porcentajes...")
    
    for cat_data in categories:
        obj, created = Category.objects.update_or_create(
            slug=cat_data['slug'],
            defaults={
                'name': cat_data['name'],
                'target_percentage': cat_data['target_percentage'], 
                'description': cat_data['description']
            }
        )
        if created:
            print(f"✅ Categoría Creada: {obj.name}")
        else:
            print(f"🔄 Categoría Actualizada: {obj.name}")

# --- PARTE 2: ACTIVOS GLOBALES (El Súper Catálogo 2026) ---
CATALOGO_ACTIVOS = {
    'efectivo': [
        {'name': 'Nu México (Cajita 14%)', 'platform': 'Nu'},
        {'name': 'Klar (Inversión Fija)', 'platform': 'Klar'},
        {'name': 'Finsus (Inversión SOFIPO)', 'platform': 'Finsus'},
        {'name': 'Ualá (Cuenta de Inversión)', 'platform': 'Ualá'},
        {'name': 'Stori Cuenta+', 'platform': 'Stori'},
        {'name': 'Bonddia (Liquidez Diaria)', 'platform': 'Cetesdirecto'},
        {'name': 'Mercado Fondo', 'platform': 'Mercado Pago'},
        {'name': 'Kubo Financiero', 'platform': 'Kubo'},
        {'name': 'SuperTasas', 'platform': 'SuperTasas'},
        {'name': 'Hey Banco (Pagaré 7 días)', 'platform': 'Hey Banco'},
    ],
    'renta-fija': [
        {'name': 'CETES 28 días', 'platform': 'Cetesdirecto'},
        {'name': 'CETES 91 días', 'platform': 'Cetesdirecto'},
        {'name': 'CETES 182 días', 'platform': 'Cetesdirecto'},
        {'name': 'CETES 364 días', 'platform': 'Cetesdirecto'},
        {'name': 'Udibonos 3 años (Protección Inflación)', 'platform': 'Cetesdirecto'},
        {'name': 'Udibonos 10 años', 'platform': 'Cetesdirecto'},
        {'name': 'Bonos M', 'platform': 'Cetesdirecto'},
        {'name': 'BPAS (Bonos de Protección)', 'platform': 'Cetesdirecto'},
        {'name': 'Smart Cash', 'platform': 'GBM+'},
        {'name': 'Pagaré Bancario Tradicional', 'platform': 'Bancos'},
    ],
    'renta-variable': [
        {'name': 'VOO (Vanguard S&P 500)', 'platform': 'GBM+ / IBKR'},
        {'name': 'IVVPESO (S&P 500 Peso Cubierto)', 'platform': 'GBM+'},
        {'name': 'VT (Total World Stock)', 'platform': 'GBM+ / IBKR'},
        {'name': 'QQQ (Nasdaq 100 - Tecnológicas)', 'platform': 'GBM+ / IBKR'},
        {'name': 'VEA (Mercados Desarrollados ex-US)', 'platform': 'GBM+ / IBKR'},
        {'name': 'VWO (Mercados Emergentes)', 'platform': 'GBM+ / IBKR'},
        {'name': 'XLF (Sector Financiero US)', 'platform': 'GBM+'},
        {'name': 'XLV (Sector Salud US)', 'platform': 'GBM+'},
        {'name': 'VTI (Vanguard Total US Market)', 'platform': 'GBM+'},
        {'name': 'NAFTRAC (IPC Bolsa Mexicana)', 'platform': 'GBM+'},
    ],
    'inmuebles': [
        {'name': 'FMTY14 (Fibra Monterrey - Industrial)', 'platform': 'GBM+'},
        {'name': 'FIBRAPL14 (Fibra Prologis - Logística)', 'platform': 'GBM+'},
        {'name': 'FUNO11 (Fibra Uno)', 'platform': 'GBM+'},
        {'name': 'DANHOS13 (Fibra Danhos - Comercial)', 'platform': 'GBM+'},
        {'name': 'FIBRAMQ12 (Fibra Macquarie)', 'platform': 'GBM+'},
        {'name': 'TERRA13 (Terrafina)', 'platform': 'GBM+'},
        {'name': 'FCFA15 (Fibra CFE - Infraestructura)', 'platform': 'GBM+'},
        {'name': 'FIHO12 (Fibra Hotel)', 'platform': 'GBM+'},
        {'name': 'VNQ (Vanguard US Real Estate ETF)', 'platform': 'GBM+ / IBKR'},
        {'name': '100 Ladrillos (Crowdfunding Inmobiliario)', 'platform': '100 Ladrillos'},
    ],
    'inversiones-alternativas': [
        {'name': 'Bitcoin (BTC)', 'platform': 'Bitso / Binance'},
        {'name': 'Ethereum (ETH)', 'platform': 'Bitso / Binance'},
        {'name': 'Solana (SOL)', 'platform': 'Binance'},
        {'name': 'USDC / USDT (Staking/Earn)', 'platform': 'Bitso / Binance'},
        {'name': 'GLD (SPDR Gold Trust - ETF Oro)', 'platform': 'GBM+ / IBKR'},
        {'name': 'SLV (iShares Silver Trust - ETF Plata)', 'platform': 'GBM+'},
        {'name': 'PDBC (Materias Primas Optimizado)', 'platform': 'GBM+'},
        {'name': 'Arte Fraccionado', 'platform': 'Masterworks'},
        {'name': 'Préstamos P2P (Bajo Riesgo)', 'platform': 'Yotepresto'},
        {'name': 'Préstamos P2P (Alto Riesgo)', 'platform': 'Doopla'},
    ],
    'private-equity': [
        {'name': 'ARKK (ETF Innovación Disruptiva)', 'platform': 'GBM+'},
        {'name': 'Crowdfunding Franquicias', 'platform': 'Snowball'},
        {'name': 'Crowdfunding Startups', 'platform': 'PlayBusiness'},
        {'name': 'Scaleups / Empresas en Crecimiento', 'platform': 'Propeler'},
        {'name': 'Venture Capital Syndicates', 'platform': 'AngelList'},
        {'name': 'Deuda Privada Inmobiliaria', 'platform': 'M2Crowd'},
        {'name': 'Préstamos a PYMES', 'platform': 'Cumplo'},
        {'name': 'Acciones Pre-IPO', 'platform': 'EquityZen'},
        {'name': 'Fondos Indexados de Private Equity', 'platform': 'IBKR'},
        {'name': 'Capital Emprendedor Directo', 'platform': 'Institucional'},
    ]
}

def sembrar_activos():
    print("\n🚀 Iniciando inyección del Súper Catálogo NEXUS 2026...")
    activos_creados = 0
    
    # Obtenemos los campos del modelo por si no tienes el campo "platform" separado
    campos_modelo = [f.name for f in GlobalAsset._meta.get_fields()]

    for slug_categoria, lista_activos in CATALOGO_ACTIVOS.items():
        categoria = Category.objects.filter(slug=slug_categoria).first()
        
        if not categoria:
            print(f"⚠️ Categoría '{slug_categoria}' no encontrada. Saltando activos...")
            continue

        for activo in lista_activos:
            if 'platform' in campos_modelo:
                obj, created = GlobalAsset.objects.get_or_create(
                    category=categoria,
                    name=activo['name'],
                    defaults={'platform': activo['platform'], 'is_active': True}
                )
            else:
                # Si no tienes campo 'platform', lo concatenamos al nombre
                nombre_completo = f"{activo['name']} (vía {activo['platform']})"
                obj, created = GlobalAsset.objects.get_or_create(
                    category=categoria,
                    name=nombre_completo,
                    defaults={'is_active': True}
                )
            
            if created:
                activos_creados += 1

    print(f"✅ Inyección completada. Se agregaron {activos_creados} nuevos activos globales.")

if __name__ == '__main__':
    # 1. Primero aseguramos que las categorías existan
    seed_categories()
    
    # 2. Luego inyectamos los activos dentro de esas categorías
    sembrar_activos()
    
    print("\n🏆 ¡Base de datos lista y blindada para el Hackathon!")