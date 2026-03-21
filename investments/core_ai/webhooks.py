import json
from django.http import JsonResponse
from .agents import ask_financial_agent
from .serializers import get_portfolio_context
from django.contrib.auth.models import User

def process_ai_request(data):
    # n8n nos enviará el username y el texto transcrito
    username = data.get('username')
    user_text = data.get('text')
    
    try:
        user = User.objects.get(username=username)
        # 1. Obtenemos contexto real
        portfolio_context = get_portfolio_context(user)
        # 2. Consultamos al agente (Claude)
        ai_response = ask_financial_agent(user_text, portfolio_context)
        
        return {
            "status": "success",
            "response": ai_response
        }
    except User.DoesNotExist:
        return {"status": "error", "message": "Usuario no encontrado"}