from django.db import models
from django.contrib.auth.models import AbstractUser

# ==========================================================================
# 1. USUARIO PERSONALIZADO (Mapeo de tabla 'usuarios')
# ==========================================================================
class User(AbstractUser):
    # Campos adicionales de tu SQL original
    capital = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    aportacion = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    ip_registro = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.username})"

# ==========================================================================
# 2. CATEGORÍAS (Mapeo de tabla 'investment_categories')
# ==========================================================================
class Category(models.Model):
    name = models.CharField(max_length=100)
    target_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    description = models.TextField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return f"{self.name} ({self.target_percentage}%)"

# ==========================================================================
# 3. ACTIVOS GLOBALES (Mapeo de tabla 'global_assets')
# ==========================================================================
class GlobalAsset(models.Model):
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    default_category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.name} [{self.symbol}]"

# ==========================================================================
# 4. INVERSIONES (Mapeo de tabla 'investments' - El Corazón)
# ==========================================================================
class Investment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='investments')
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    
    asset_name = models.CharField(max_length=100)
    api_id = models.CharField(max_length=50, null=True, blank=True, help_text="ID para CoinGecko/Yahoo Finance")
    banxico_series = models.CharField(max_length=20, null=True, blank=True, help_text="Serie para consulta de CETES")
    
    annual_yield = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    amount_invested = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Precisión de 10 decimales para Cripto (Satoshi-ready)
    quantity = models.DecimalField(max_digits=20, decimal_places=10, default=1.0000000000)
    current_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    # Cambiamos placeholder por help_text
    platform = models.CharField(
        max_length=50, 
        null=True, 
        blank=True, 
        help_text="Ej: Bitso, Nu, GBM"
    )
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.asset_name} ({self.user.username})"