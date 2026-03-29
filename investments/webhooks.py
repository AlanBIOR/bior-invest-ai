from django.http import JsonResponse
from .models import Category, Investment
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings

def check_alerts_api(request):
    """
    Endpoint para n8n que detecta Capital Ocioso y Profits significativos
    usando los datos reales de cada usuario en la base de datos.
    """
    # --- SEGURIDAD ---
    token_recibido = request.GET.get('token')
    token_seguridad = settings.NEXUS_WEBHOOK_TOKEN
    
    if token_recibido != token_seguridad:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    alertas = []
    
    try:
        # Buscamos la categoría de efectivo una sola vez para optimizar
        efectivo_cat = Category.objects.filter(slug='efectivo').first()
        usuarios = User.objects.filter(is_active=True)

        for usuario in usuarios:
            # Determinamos el nombre a mostrar (Nombre real o Username)
            nombre_usuario = usuario.first_name if usuario.first_name else usuario.username
            
            # Filtramos inversiones exclusivas de este usuario
            user_investments = Investment.objects.filter(user=usuario)
            
            # --- 1. ALERTA DE CAPITAL OCIOSO (Basado en current_value) ---
            total_patrimonio = user_investments.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
            
            if efectivo_cat and total_patrimonio > 0:
                monto_efectivo = user_investments.filter(category=efectivo_cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
                porcentaje_efectivo = (monto_efectivo / total_patrimonio) * 100
                
                if porcentaje_efectivo > 15:
                    alertas.append({
                        "usuario": usuario.username,
                        "email": usuario.email,
                        "titulo": "🚨 Capital Ocioso",
                        # AQUÍ USAMOS LA VARIABLE DINÁMICA
                        "mensaje": f"{nombre_usuario}, detectamos que tienes el {porcentaje_efectivo:.1f}% en efectivo. NEXUS sugiere rebalancear para optimizar rendimientos.",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

            # --- 2. ALERTA DE RENDIMIENTO (Detección de Subidas > 5%) ---
            for inv in user_investments:
                rendimiento = inv.rendimiento_porcentaje
                if rendimiento >= 5:
                    alertas.append({
                        "usuario": usuario.username,
                        "email": usuario.email,
                        "titulo": f"📈 Profit en {inv.asset_name}",
                        # TAMBIÉN AQUÍ PARA PERSONALIZAR
                        "mensaje": f"¡Buenas noticias {nombre_usuario}! Tu inversión en {inv.asset_name} ha subido un {rendimiento:.2f}%.",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({
        "status": "success", 
        "has_alerts": len(alertas) > 0, 
        "count": len(alertas),
        "data": alertas
    })