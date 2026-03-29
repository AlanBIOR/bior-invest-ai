from django.http import JsonResponse
from .models import Category, Investment
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings

def check_alerts_api(request):
    token_recibido = request.GET.get('token')
    token_seguridad = settings.NEXUS_WEBHOOK_TOKEN
    
    if token_recibido != token_seguridad:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    alertas = []
    
    try:
        usuarios = User.objects.filter(is_active=True)
        # Traemos todas las categorías que tengan un target definido
        categorias = Category.objects.all()

        for usuario in usuarios:
            nombre_usuario = usuario.first_name if usuario.first_name else usuario.username
            user_investments = Investment.objects.filter(user=usuario)
            total_patrimonio = user_investments.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')

            if total_patrimonio > 0:
                # --- 1. ALERTA DINÁMICA POR CATEGORÍA (Rebalanceo) ---
                for cat in categorias:
                    monto_cat = user_investments.filter(category=cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
                    porcentaje_actual = (monto_cat / total_patrimonio) * 100
                    
                    # Comparamos contra el target que pusiste en el Admin (con un margen de error del 5%)
                    # Ejemplo: Si Renta Variable es 47% y tienes 60%, NEXUS dispara alerta.
                    limite_alerta = cat.target_percentage + Decimal('5.0')
                    
                    if porcentaje_actual > limite_alerta:
                        alertas.append({
                            "usuario": usuario.username,
                            "email": usuario.email,
                            "titulo": f"⚖️ Rebalanceo: {cat.name}",
                            "mensaje": f"{nombre_usuario}, tu exposición en {cat.name} es del {porcentaje_actual:.1f}%, superando tu objetivo del {cat.target_percentage}%. NEXUS sugiere vender parte para mitigar riesgo.",
                            "url": "https://invest-ai.bior-studio.com/nexus-advisor/"
                        })

            # --- 2. ALERTA DE RENDIMIENTO (Profit) ---
            for inv in user_investments:
                rendimiento = inv.rendimiento_porcentaje
                if rendimiento >= 5:
                    alertas.append({
                        "usuario": usuario.username,
                        "email": usuario.email,
                        "titulo": f"📈 Profit en {inv.asset_name}",
                        "mensaje": f"¡Buenas noticias {nombre_usuario}! Tu inversión en {inv.asset_name} ha subido un {rendimiento:.2f}%.",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success", "has_alerts": len(alertas) > 0, "count": len(alertas), "data": alertas})