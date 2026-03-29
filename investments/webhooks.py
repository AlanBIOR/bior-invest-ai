from django.http import JsonResponse
from .models import Category, Investment
from django.db.models import Sum
from decimal import Decimal

def check_alerts_api(request):
    """
    Endpoint seguro que n8n consultará para disparar alertas proactivas.
    URL: /investments/api/v1/nexus-alerts/
    """
    
    # --- SEGURIDAD BÁSICA ---
    token_recibido = request.GET.get('token')
    token_seguridad = "BIOR_NEXUS_2024_SECRET" 
    
    if token_recibido != token_seguridad:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    alertas = []
    
    try:
        # 1. CÁLCULO DE PATRIMONIO TOTAL (Usando tu variable current_value)
        total_patrimonio = Investment.objects.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
        
        # 2. BUSCAR CATEGORÍA DE EFECTIVO
        efectivo_cat = Category.objects.filter(slug='efectivo').first()
        
        if efectivo_cat and total_patrimonio > 0:
            # Sumamos solo lo que esté en la categoría efectivo
            monto_efectivo = Investment.objects.filter(category=efectivo_cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
            porcentaje_efectivo = (monto_efectivo / total_patrimonio) * 100
            
            # Umbral del 15%
            if porcentaje_efectivo > 15:
                alertas.append({
                    "canal": "todos", 
                    "prioridad": "Alta",
                    "titulo": "🚨 Alerta de Liquidez: Capital Ocioso",
                    "mensaje": f"Alan, detectamos que tu efectivo representa el {porcentaje_efectivo:.1f}% de tu cartera. NEXUS sugiere rebalancear para optimizar rendimientos.",
                    "url": "https://invest-ai.bior-studio.com/nexus-advisor/",
                    "color": "#1a2a6c"
                })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({
        "status": "success",
        "has_alerts": len(alertas) > 0,
        "count": len(alertas),
        "data": alertas
    })