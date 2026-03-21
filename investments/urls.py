from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('portafolio/', views.portafolio, name='portafolio'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('registro/', views.registro, name='registro'),
    
    # Rutas legales
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    
    # Detalle dinámico (cambiado a <slug:slug> para evitar errores)
    path('detalle/<slug:slug>/', views.detalle_inversion, name='detalle_inversion'),
    
    path('guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
    path('eliminar-activo/<int:pk>/', views.eliminar_activo, name='eliminar_activo'),
    
    # APIs (Asegúrate de que views.get_cetes_rate exista en views.py)
    path('api/get-cetes-rate/', views.get_cetes_rate, name='get_cetes_rate'),
    path('api/v1/n8n-webhook/', views.n8n_webhook, name='n8n_webhook'),
]