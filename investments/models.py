from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

# --- 1. CATEGORÍAS DE INVERSIÓN ---
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

# --- 2. ACTIVOS GLOBALES (Para jalar precios de APIs) ---
class GlobalAsset(models.Model):
    name = models.CharField(max_length=255)
    symbol = models.CharField(max_length=20, help_text="Ej: BTC, AAPL, AMZN")
    api_id = models.CharField(max_length=100, blank=True, null=True, help_text="ID para CoinGecko")
    current_price = models.DecimalField(max_digits=20, decimal_places=10, default=0.0)
    last_api_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.symbol})"

# --- 3. INVERSIONES DEL USUARIO (Activos Reales) ---
class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    global_asset = models.ForeignKey(GlobalAsset, on_delete=models.SET_NULL, null=True, blank=True)
    
    asset_name = models.CharField(max_length=255)
    
    # Campo detectado en tu DB: Importante para criptos o acciones fraccionadas
    quantity = models.DecimalField(max_digits=25, decimal_places=12, default=1.0)
    
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2)
    current_value = models.DecimalField(max_digits=15, decimal_places=2)
    platform = models.CharField(max_length=100, blank=True)
    
    annual_yield = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    banxico_series = models.CharField(max_length=50, blank=True, null=True)
    last_updated = models.DateTimeField(auto_now=True) 

    @property
    def rendimiento_porcentaje(self):
        if self.amount_invested and self.amount_invested > 0:
            diff = self.current_value - self.amount_invested
            return (diff / self.amount_invested) * 100
        return 0

# --- 4. PERFIL DE USUARIO (Configuración de la Calculadora) ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000.00)
    aportacion = models.DecimalField(max_digits=15, decimal_places=2, default=500.00)

    def __str__(self):
        return f"Perfil de {self.user.username}"

# --- 5. AUTOMATIZACIÓN (SIGNALS) ---
# Esto garantiza que cada AlanAdmin o usuario nuevo tenga su Perfil creado automáticamente
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Usamos try/except por si el perfil fue borrado manualmente
    try:
        instance.profile.save()
    except Profile.DoesNotExist:
        Profile.objects.create(user=instance)

# --- 4. PERFIL DE USUARIO ---
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    capital = models.DecimalField(max_digits=15, decimal_places=2, default=10000.00)
    aportacion = models.DecimalField(max_digits=15, decimal_places=2, default=500.00)
    
    # AGREGA ESTA LÍNEA:
    whatsapp_number = models.CharField(max_length=20, unique=True, null=True, blank=True, help_text="Ej: 5215512345678")

    def __str__(self):
        return f"Perfil de {self.user.username}"