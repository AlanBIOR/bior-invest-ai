import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .agents import ask_financial_agent
from .serializers import get_portfolio_context
from investments.models import Profile

@csrf_exempt 
def process_ai_request(request): 
    # 1. Validar Seguridad (Candado compartido para n8n y JS)
    auth_header = request.headers.get('X-Api-Key')
    print(f"--- NUEVA PETICIÓN ---")
    print(f"Header Recibido: {auth_header}")
    print(f"Llave Esperada: {settings.N8N_WEBHOOK_KEY}")
    if auth_header != settings.N8N_WEBHOOK_KEY:
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    # 2. Captura de datos inteligente
    if request.method == 'POST':
        try:
            # --- SOPORTE PARA JS (JSON) ---
            if request.content_type == 'application/json':
                data = json.loads(request.body)
            # --- SOPORTE PARA n8n (FORM DATA) ---
            else:
                data = request.POST

            # Buscamos el teléfono probando todas las llaves posibles de ambos sistemas
            phone = data.get('whatsapp_phone') or data.get('phone') or data.get('From')
            # Buscamos el texto probando llaves de JS y de n8n/Twilio
            user_text = data.get('text') or data.get('body') or data.get('Body')

            if not phone or not user_text:
                return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)

            # Limpiar el teléfono de prefijos de Twilio si vienen de n8n
            if isinstance(phone, str) and "whatsapp:" in phone:
                phone = phone.replace("whatsapp:", "")

            # 3. Lógica de negocio (Buscar usuario y llamar a Gemini)
            try:
                profile = Profile.objects.get(whatsapp_number=phone)
                user = profile.user
                
                # Obtener contexto financiero real
                portfolio_context = get_portfolio_context(user)
                
                # Llamada a la IA (Gemini 2.5/3)
                ai_response = ask_financial_agent(user_text, portfolio_context)
                
                return JsonResponse({
                    "status": "success",
                    "nombre": user.first_name or user.username,
                    "response": ai_response
                })

            except Profile.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "response": "Lo siento, este número no está vinculado. Por favor, regístrate en BIOR Invest."
                }, status=200)

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # Si intentan entrar por navegador (GET)
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)