import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .agents import ask_financial_agent
from .serializers import get_portfolio_context
from investments.models import Profile

@csrf_exempt 
def process_ai_request(request): 
    # 1. Validar Seguridad (X-Api-Key)
    auth_header = request.headers.get('X-Api-Key')
    if auth_header != settings.N8N_WEBHOOK_KEY:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    # 2. Leer los datos enviados por el Chatbot JS
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone = data.get('whatsapp_phone')
            user_text = data.get('text')

            if not phone or not user_text:
                return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)

            # 3. Lógica de negocio (Buscar usuario y llamar a Gemini)
            try:
                profile = Profile.objects.get(whatsapp_number=phone)
                user = profile.user
                
                # Contexto del portafolio
                portfolio_context = get_portfolio_context(user)
                
                # Respuesta de la IA
                ai_response = ask_financial_agent(user_text, portfolio_context)
                
                # Devolvemos un JsonResponse real
                return JsonResponse({
                    "status": "success",
                    "nombre": user.first_name or user.username,
                    "response": ai_response
                })

            except Profile.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "response": "Lo siento, este número no está vinculado. Por favor, regístrate."
                })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)