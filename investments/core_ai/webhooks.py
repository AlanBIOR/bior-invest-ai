import json
from django.http import JsonResponse
from .agents import ask_financial_agent
from .serializers import get_portfolio_context
from django.contrib.auth.models import User
from investments.models import Profile  # <--- Importamos el Perfil

def process_ai_request(data):
    # n8n nos enviará el whatsapp_phone y el body del mensaje
    phone = data.get('whatsapp_phone')
    user_text = data.get('text')
    
    try:
        # 1. Buscamos el perfil que tenga ese número de WhatsApp
        profile = Profile.objects.get(whatsapp_number=phone)
        user = profile.user
        
        # 2. Tu serializador ya hace el trabajo pesado de armar el JSON del portafolio
        portfolio_context = get_portfolio_context(user)
        
        # 3. Consultamos a tu agente (Claude/Gemini) con los datos REALES del usuario
        ai_response = ask_financial_agent(user_text, portfolio_context)
        
        return {
            "status": "success",
            "nombre": user.first_name or user.username,
            "response": ai_response
        }
        
    except Profile.DoesNotExist:
        return {
            "status": "error", 
            "response": "Lo siento, este número no está vinculado a ninguna cuenta de BIOR Invest. Por favor, regístrate en la plataforma."
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}