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
    
    # Logs para depuración en terminal (nohup.out)
    print(f"\n--- NUEVA PETICIÓN RECIBIDA ---")
    print(f"Método: {request.method}")
    print(f"Content-Type: {request.content_type}")
    print(f"Header API Key: {auth_header}")

    if auth_header != settings.N8N_WEBHOOK_KEY:
        print("❌ ERROR: Llave de API no coincide")
        return JsonResponse({"status": "error", "message": "No autorizado"}, status=403)

    # 2. Solo aceptamos POST para procesar mensajes
    if request.method == 'POST':
        try:
            # --- CAPTURA DE DATOS MULTIFORMATO ---
            if 'application/json' in request.content_type:
                # Caso: Chat Web (JSON)
                data = json.loads(request.body)
            else:
                # Caso: n8n / Twilio (Form Data)
                data = request.POST

            # Mapeo flexible de variables (Soporta: whatsapp_phone, phone, From, text, Body)
            phone = data.get('whatsapp_phone') or data.get('phone') or data.get('From')
            user_text = data.get('text') or data.get('body') or data.get('Body')

            print(f"📱 Teléfono: {phone} | 💬 Texto: {user_text}")

            if not phone or not user_text:
                return JsonResponse({
                    "status": "error", 
                    "message": f"Datos incompletos. Recibido: {list(data.keys())}"
                }, status=400)

            # Limpiar prefijo de Twilio si viene de WhatsApp
            if isinstance(phone, str) and "whatsapp:" in phone:
                phone = phone.replace("whatsapp:", "")

            # 3. Lógica de Negocio (Base de Datos + IA)
            try:
                # Buscar perfil por número de WhatsApp
                profile = Profile.objects.get(whatsapp_number=phone)
                user = profile.user
                
                # Obtener contexto financiero (activos, rendimientos, etc.)
                portfolio_context = get_portfolio_context(user)
                
                # Llamada al Agente Financiero (Gemini)
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
                    "response": "Lo siento, este número no está vinculado a ninguna cuenta de BIOR Invest. Por favor, regístrate en la plataforma primero."
                }, status=200) # Devolvemos 200 para que el mensaje llegue al usuario en WhatsApp

        except Exception as e:
            print(f"🔥 ERROR INTERNO: {str(e)}")
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    # Si intentan entrar por GET u otro método
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)