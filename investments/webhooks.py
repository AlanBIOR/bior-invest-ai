from django.http import JsonResponse
from .models import Category, Investment
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal

def check_alerts_api(request):
    token_recibido = request.GET.get('token')
    token_seguridad = "BIOR_NEXUS_2024_SECRET" 
    
    if token_recibido != token_seguridad:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    alertas = []
    
    try:
        efectivo_cat = Category.objects.filter(slug='efectivo').first()
        usuarios = User.objects.filter(is_active=True)

        for usuario in usuarios:
            user_investments = Investment.objects.filter(user=usuario)
            
            # --- 1. ALERTA DE CAPITAL OCIOSO ---
            total_patrimonio = user_investments.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
            if efectivo_cat and total_patrimonio > 0:
                monto_efectivo = user_investments.filter(category=efectivo_cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
                porcentaje_efectivo = (monto_efectivo / total_patrimonio) * 100
                
                if porcentaje_efectivo > 15:
                    alertas.append({
                        "usuario": usuario.username,
                        "email": usuario.email,
                        "titulo": "🚨 Capital Ocioso",
                        "mensaje": f"Alan, tienes el {porcentaje_efectivo:.1f}% en efectivo. ¡Ponlo a trabajar!",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

            # --- 2. ALERTA DE RENDIMIENTO (Detección de Subidas) ---
            for inv in user_investments:
                rendimiento = inv.rendimiento_porcentaje # Usamos tu @property del modelo
                if rendimiento >= 5: # Si subió más del 5%
                    alertas.append({
                        "usuario": usuario.username,
                        "email": usuario.email,
                        "titulo": f"📈 Profit en {inv.asset_name}",
                        "mensaje": f"¡Buenas noticias! Tu inversión en {inv.asset_name} ha subido un {rendimiento:.2f}%.",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success", "has_alerts": len(alertas) > 0, "data": alertas})