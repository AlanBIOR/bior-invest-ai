from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('portafolio/', views.portafolio, name='portafolio'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('registro/', views.registro, name='registro'),
    # Rutas legales del footer
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    # Ruta dinámica para los detalles (lo que tenías en PHP como detalle_inversion/)
    path('detalle/<str:category_slug>/', views.detalle_inversion, name='detalle_inversion'),
    path('guardar-progreso/', views.guardar_progreso, name='guardar_progreso'),
    path('eliminar-activo/<int:pk>/', views.eliminar_activo, name='eliminar_activo'),
    path('api/v1/n8n-webhook/', views.n8n_webhook, name='n8n_webhook'),
]