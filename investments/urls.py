from django.urls import path
from . import views
from . import webhooks as alerts_webhooks  # Alias para investments/webhooks.py
from .core_ai import webhooks as ai_webhooks # Alias para core_ai/webhooks.py

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('portafolio/', views.portafolio, name='portafolio'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('registro/', views.registro, name='registro'),
    
    # Rutas legales
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    
    # Detalle dinámico
    path('detalle/<slug:slug>/', views.detalle_inversion, name='detalle_inversion'),
    
    path('guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
    path('eliminar-activo/<int:pk>/', views.eliminar_activo, name='eliminar_activo'),
    
    # APIs
    path('api/get-cetes-rate/', views.get_cetes_rate, name='get_cetes_rate'),
    
    # Usamos ai_webhooks (el de la carpeta core_ai)
    path('api/v1/n8n-webhook/', ai_webhooks.process_ai_request, name='n8n_webhook_bridge'),
    path('api/v1/ai-chat/', ai_webhooks.process_ai_request, name='ai_chat_web'),

    path('nexus-advisor/', views.nexus_advisor_view, name='nexus_advisor'),
    path('api/v1/modo-decision/', views.api_modo_decision, name='api_modo_decision'),

    # Usamos alerts_webhooks (el nuevo para n8n/email)
    path('api/v1/nexus-alerts/', alerts_webhooks.check_alerts_api, name='nexus_alerts_webhook'),
]