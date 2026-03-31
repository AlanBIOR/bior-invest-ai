import json
from django.http import JsonResponse
from .models import Category, Investment, Profile
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .core_ai.agents import ask_financial_agent 

# --- 1. ALERTAS DE NEXUS (CRON/NOTIFICACIONES) ---
def check_alerts_api(request):
    token_recibido = request.GET.get('token')
    token_seguridad = settings.NEXUS_WEBHOOK_TOKEN
    
    if token_recibido != token_seguridad:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    alertas = []
    try:
        usuarios = User.objects.filter(is_active=True, profile__telegram_id__isnull=False)
        categorias = Category.objects.all()

        for usuario in usuarios:
            chat_id = usuario.profile.telegram_id
            nombre_usuario = usuario.first_name or usuario.username
            user_investments = Investment.objects.filter(user=usuario)
            total_patrimonio = user_investments.aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')

            if total_patrimonio > 0:
                for cat in categorias:
                    monto_cat = user_investments.filter(category=cat).aggregate(total=Sum('current_value'))['total'] or Decimal('0.00')
                    porcentaje_actual = (monto_cat / total_patrimonio) * 100
                    if porcentaje_actual > (cat.target_percentage + Decimal('5.0')):
                        alertas.append({
                            "telegram_id": chat_id,
                            "titulo": f"⚖️ Rebalanceo: {cat.name}", # <--- ASEGÚRATE DE QUE ESTO ESTÉ AHÍ
                            "mensaje": f"{nombre_usuario}, rebalanceo necesario en {cat.name} ({porcentaje_actual:.1f}%).",
                            "url": "https://invest-ai.bior-studio.com/nexus-advisor/"
                        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success", "data": alertas})


# --- 2. WEBHOOK WHATSAPP (CONEXIÓN A BASE DE DATOS) ---
@csrf_exempt
def n8n_webhook(request):
    if request.method == 'POST':
        try:
            auth_header = request.headers.get('X-Api-Key')
            if auth_header != settings.N8N_WEBHOOK_KEY:
                return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

            data = json.loads(request.body)
            raw_phone = str(data.get('phone', ''))
            user_question = data.get('pregunta') or data.get('text') or data.get('Body')

            if not raw_phone:
                return JsonResponse({"status": "error", "message": "Falta teléfono"}, status=400)

            # Lógica de limpieza: Si el número en DB tiene "+", nos aseguramos de buscarlo bien
            # Intentamos buscar el número tal cual llega, y si no, le agregamos el "+" 
            profile = Profile.objects.filter(whatsapp_number__icontains=raw_phone.replace('+', '')).first()

            if not profile:
                print(f"DEBUG: No se encontró perfil para el número {raw_phone}")
                return JsonResponse({"status": "success", "response": "Número no reconocido en la base de datos de BIOR Invest."})

            # ACCESO A LA BASE DE DATOS (User -> Inversiones)
            user = profile.user
            mis_inversiones = Investment.objects.filter(user=user)
            
            # Construcción del contexto real para Gemini
            contexto_activos = ""
            for inv in mis_inversiones:
                contexto_activos += f"- {inv.asset_name}: ${inv.current_value} MXN (Rendimiento: {inv.rendimiento_porcentaje}%)\n"

            prompt_nexus = f"""
            Eres NEXUS, el sistema de IA de BIOR Invest.
            ESTÁS HABLANDO CON: {user.first_name or user.username}
            
            DATOS REALES DEL USUARIO (BASE DE DATOS):
            - Efectivo (Capital): ${profile.capital} MXN
            - Portafolio Actual:
            {contexto_activos if contexto_activos else "Sin activos registrados."}

            INSTRUCCIÓN: Responde de forma breve y profesional a: "{user_question}"
            """
            
            respuesta_ia = ask_financial_agent(prompt_nexus)

            return JsonResponse({
                "status": "success",
                "nombre": user.username,
                "response": respuesta_ia
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)