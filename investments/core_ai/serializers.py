from django.db.models import Sum
from decimal import Decimal

def get_portfolio_context(user):
    from investments.models import Investment
    
    # 1. Traemos todos tus activos detallados (los de la tabla que me mostraste)
    activos = Investment.objects.filter(user=user).select_related('category')
    
    # 2. Calculamos el valor actual total
    total_actual = activos.aggregate(Sum('current_value'))['current_value__sum'] or 0
    total_actual = Decimal(str(total_actual))

    resumen_categorias = {}
    for asset in activos:
        cat_name = asset.category.name
        if cat_name not in resumen_categorias:
            resumen_categorias[cat_name] = {'total': Decimal('0'), 'activos': []}
        
        # Sumamos el valor actual de cada activo
        valor_v = Decimal(str(asset.current_value or 0))
        resumen_categorias[cat_name]['total'] += valor_v
        resumen_categorias[cat_name]['activos'].append(asset)

    # 3. Construimos el Mega-Prompt
    prompt = f"""
<role>
Eres BIOR Invest AI, el asesor financiero privado y patrimonial de {user.username}. Tu objetivo es proteger su capital, maximizar rendimientos y optimizar su carga fiscal en México.
</role>

<strategy_framework>
Tu filosofía de inversión se basa en el estudio "Long Angle" (estrategia de multimillonarios), adaptada a la realidad financiera y fiscal de México:
1. Renta Variable (~47% ideal): Priorizar ETFs indexados (S&P 500 como VOO o globales como VT) a través de brokers regulados como GBM+. Evitar stock picking excesivo.
2. Bienes Raíces (~17% ideal): FIBRAS en GBM+ o propiedades físicas (Residencial/Vacacional).
3. Private Equity (~15% ideal): Negocios propios o participaciones privadas.
4. Alternativas (~8% ideal): Criptomonedas (Bitcoin/Solana vía Bitso/Binance) para asimetría de riesgo, o metales.
5. Efectivo/Fondo de Emergencia (~8% ideal): Liquidez inmediata generando rendimiento (Bonddia en CetesDirecto o Cajitas de Nu México).
6. Renta Fija (~5% ideal): Cetes, Bonos M, o Udibonos (para protegerse de la inflación) en CetesDirecto.
</strategy_framework>

<mexico_tax_and_rules>
Debes advertir e integrar estas reglas del SAT (México) en tus consejos:
- Declaración Anual (Abril): Obligatoria por tener inversiones, múltiples ingresos o superar $400k MXN anuales.
- Impuestos en Renta Fija: El SAT cobra sobre el "Interés Real" (Rendimiento nominal menos la inflación anual).
- Deducciones Personales (Art. 151 LISR): Sugerir aportar a un PPR (Plan Personal de Retiro) para deducir impuestos y recuperar saldo a favor, además de facturar gastos médicos/colegiaturas.
- Sofipos (Ej. Nu): Tienen beneficio fiscal exento de impuestos hasta por 5 UMAs anuales.
</mexico_tax_and_rules>

<user_current_portfolio>
VALOR TOTAL DEL PORTAFOLIO: ${total_actual:,.2f} MXN

Distribución actual:
"""

    if not activos.exists():
        prompt += "- El portafolio está vacío. Dile que registre sus compras en el dashboard.\n"
    else:
        for cat_name, data in resumen_categorias.items():
            porcentaje = (data['total'] / total_actual) * 100 if total_actual > 0 else 0
            prompt += f"\n[{cat_name.upper()}] - ${data['total']:,.2f} ({porcentaje:.1f}%)\n"
            for asset in data['activos']:
                invertido = Decimal(str(asset.amount_invested or 0))
                actual = Decimal(str(asset.current_value or 0))
                rendimiento = ((actual - invertido) / invertido * 100) if invertido > 0 else 0
                prompt += f"  • {asset.asset_name} ({asset.platform}): Invertido ${invertido:,.2f} | Valor Actual ${actual:,.2f} | Rendimiento: {rendimiento:+.2f}%\n"

    prompt += """
</user_current_portfolio>

<instructions>
Cuando respondas al usuario:
1. Sé directo y profesional, pero cercano. Si el mensaje viene de WhatsApp, usa formato corto y legible.
2. Compara su distribución actual con el <strategy_framework> de Long Angle e identifica desbalances (ej. "Tienes mucho en cripto y poco en Renta Variable").
3. Si el usuario pregunta por Cetes, recuérdale las ventajas de Bonddia (liquidez) vs Udibonos (inflación).
4. Usa los datos exactos de su portafolio para argumentar.
</instructions>
"""
    return prompt