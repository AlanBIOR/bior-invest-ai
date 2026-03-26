import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .agents import ask_financial_agent
from .serializers import get_portfolio_context
from investments.models import Profile

@csrf_exempt 
def process_ai_request(request): 
    auth_header = request.headers.get('X-Api-Key')
    
    print(f"\n--- NUEVA PETICIÓN RECIBIDA ---")
    if auth_header != settings.N8N_WEBHOOK_KEY:
        print("❌ ERROR: Llave de API no coincide")
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    if request.method == 'POST':
        try:
            if 'application/json' in request.content_type:
                data = json.loads(request.body)
            else:
                data = request.POST

            phone = data.get('whatsapp_phone') or data.get('phone') or data.get('From')
            user_text = data.get('text') or data.get('body') or data.get('Body')

            if not phone or not user_text:
                return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)

            # Limpieza: Mantiene el '+' para coincidir con la Base de Datos
            if isinstance(phone, str) and "whatsapp:" in phone:
                phone = phone.replace("whatsapp:", "")

            print(f"📱 Teléfono procesado: {phone} | 💬 Texto: {user_text}")

            try:
                # Búsqueda exacta con el formato +521...
                profile = Profile.objects.get(whatsapp_number=phone)
                user = profile.user
                
                portfolio_context = get_portfolio_context(user)
                ai_response = ask_financial_agent(user_text, portfolio_context)
                
                print(f"✅ Respuesta enviada a {user.username}")
                return JsonResponse({
                    "status": "success",
                    "nombre": user.first_name or user.username,
                    "response": ai_response
                })

            except Profile.DoesNotExist:
                print(f"⚠️ Número no registrado: {phone}")
                return JsonResponse({
                    "status": "error", 
                    "response": "Lo siento, este número no está vinculado a ninguna cuenta de BIOR Invest."
                }, status=200)

        except Exception as e:
            print(f"🔥 ERROR INTERNO: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)