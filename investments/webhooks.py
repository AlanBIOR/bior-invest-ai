import json
from django.http import JsonResponse
from .models import Category, Investment, Profile
from django.contrib.auth.models import User
from django.db.models import Sum
from decimal import Decimal
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
# Asegúrate de que la ruta a tu función de IA sea correcta
from .core_ai.agents import ask_financial_agent 

# --- FUNCIÓN 1: ALERTAS PROACTIVAS (CRON) ---
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
                            "telegram_id": chat_id,
                            "usuario": usuario.username,
                            "titulo": f"⚖️ Rebalanceo: {cat.name}",
                            "mensaje": f"{nombre_usuario}, tu exposición en {cat.name} es del {porcentaje_actual:.1f}%, superando tu objetivo del {cat.target_percentage}%.",
                            "url": "https://invest-ai.bior-studio.com/nexus-advisor/"
                        })

                # --- 2. ALERTA DE RENDIMIENTO ---
                for inv in user_investments:
                    if inv.rendimiento_porcentaje >= 5:
                        alertas.append({
                            "telegram_id": chat_id,
                            "usuario": usuario.username,
                            "titulo": f"📈 Profit en {inv.asset_name}",
                            "mensaje": f"¡Buenas noticias {nombre_usuario}! {inv.asset_name} subió un {inv.rendimiento_porcentaje:.2f}%.",
                            "url": "https://invest-ai.bior-studio.com/portafolio/"
                        })

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "success", "has_alerts": len(alertas) > 0, "data": alertas})


# --- FUNCIÓN 2: RECEPCIÓN DE MENSAJES (CHAT HÍBRIDO TELEGRAM/WHATSAPP) ---
@csrf_exempt
def n8n_webhook(request):
    """
    Recibe mensajes de Telegram o WhatsApp y responde usando Gemini.
    """
    # Validación de Seguridad por Header
    auth_header = request.headers.get('X-Api-Key')
    if auth_header != settings.N8N_WEBHOOK_KEY:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # DEBUG en consola para el hackathon
            print(f"\n--- PETICIÓN RECIBIDA: {data} ---")

            # Identificadores (Soporta ambos canales)
            phone = data.get('phone')
            telegram_id = str(data.get('telegram_id')) if data.get('telegram_id') else None
            
            # Captura de pregunta en cualquier formato
            user_question = data.get('pregunta') or data.get('text') or data.get('Body')

            if not phone and not telegram_id:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Falta ID. Recibí: {list(data.keys())}"
                }, status=400)

            # Búsqueda de Perfil
            try:
                if phone:
                    profile = Profile.objects.get(whatsapp_number=phone)
                else:
                    profile = Profile.objects.get(telegram_id=telegram_id)
                
                user = profile.user
                investments = Investment.objects.filter(user=user)

                # Contexto para Gemini
                inv_list = [f"- {i.asset_name}: ${i.current_value} MXN" for i in investments]
                lista_formateada = "\n".join(inv_list) if inv_list else "Sin activos registrados."

                prompt_nexus = f"""
                Actúa como NEXUS, el asesor financiero de {user.username}.
                DATOS DEL USUARIO:
                - Capital: ${profile.capital} MXN
                - Activos: {lista_formateada}

                Pregunta: {user_question}
                Instrucción: Responde basado en sus datos reales de arriba.
                """
                
                respuesta_ia = ask_financial_agent(prompt_nexus)

                return JsonResponse({
                    "status": "success",
                    "nombre": user.username,
                    "response": respuesta_ia
                })

            except Profile.DoesNotExist:
                return JsonResponse({
                    "status": "success", 
                    "response": "Hola! No encontré tu cuenta vinculada. Por favor, regístrate en BIOR Invest."
                })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)