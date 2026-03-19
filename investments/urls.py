from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('portafolio/', views.portafolio, name='portafolio'),
    path('configuracion/', views.configuracion, name='configuracion'),
    # Rutas legales del footer
    path('terminos/', views.terminos, name='terminos'),
    path('privacidad/', views.privacidad, name='privacidad'),
    path('disclaimer/', views.disclaimer, name='disclaimer'),
    # Ruta dinámica para los detalles (lo que tenías en PHP como detalle_inversion/)
    path('detalle/<str:category_slug>/', views.detalle_inversion, name='detalle_inversion'),
]