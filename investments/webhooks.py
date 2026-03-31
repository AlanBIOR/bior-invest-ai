from django.http import JsonResponse
from .models import Category, Investment, Profile # Asegúrate de importar Profile
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
        # Filtramos usuarios activos que tengan un perfil con Telegram ID vinculado
        # Si no usas Profile, puedes quitar el filter de profile__telegram_id__isnull
        usuarios = User.objects.filter(is_active=True, profile__telegram_id__isnull=False)
        categorias = Category.objects.all()

        for usuario in usuarios:
            # Extraemos el ID de Telegram del perfil
            chat_id = usuario.profile.telegram_id
            nombre_usuario = usuario.first_name if usuario.first_name else usuario.username
            user_investments = Investment.objects.filter(user=usuario)
            total_patrimonio = user_investments.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')

            if total_patrimonio > 0:
                # --- 1. ALERTA DE REBALANCEO ---
                for cat in categorias:
                    monto_cat = user_investments.filter(category=cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
                    porcentaje_actual = (monto_cat / total_patrimonio) * 100
                    limite_alerta = cat.target_percentage + Decimal('5.0')
                    
                    if porcentaje_actual > limite_alerta:
                        alertas.append({
                            "telegram_id": chat_id, # <--- MANDAMOS EL ID A n8n
                            "usuario": usuario.username,
                            "titulo": f"⚖️ Rebalanceo: {cat.name}",
                            "mensaje": f"{nombre_usuario}, tu exposición en {cat.name} es del {porcentaje_actual:.1f}%, superando tu objetivo del {cat.target_percentage}%.",
                            "url": "https://invest-ai.bior-studio.com/nexus-advisor/"
                        })

            # --- 2. ALERTA DE RENDIMIENTO ---
            for inv in user_investments:
                if inv.rendimiento_porcentaje >= 5:
                    alertas.append({
                        "telegram_id": chat_id, # <--- MANDAMOS EL ID A n8n
                        "usuario": usuario.username,
                        "titulo": f"📈 Profit en {inv.asset_name}",
                        "mensaje": f"¡Buenas noticias {nombre_usuario}! {inv.asset_name} subió un {inv.rendimiento_porcentaje:.2f}%.",
                        "url": "https://invest-ai.bior-studio.com/portafolio/"
                    })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success", "has_alerts": len(alertas) > 0, "data": alertas})