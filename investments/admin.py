from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Category, GlobalAsset, Investment

# --- Registro del Usuario Personalizado ---
# Usamos UserAdmin para que se vean los campos de permisos y fechas
admin.site.register(User, UserAdmin)

# --- Registro de Categorías ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_percentage')
    search_fields = ('name',)

# --- Registro de Activos Globales ---
@admin.register(GlobalAsset)
class GlobalAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'default_category')
    list_filter = ('default_category',)
    search_fields = ('name', 'symbol')

# --- Registro de Inversiones ---
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ('asset_name', 'user', 'category', 'current_value', 'platform')
    list_filter = ('category', 'platform', 'user')
    search_fields = ('asset_name', 'platform')
    # Esto permite que la fecha se vea en el listado pero no se pueda editar manualmente
    readonly_fields = ('last_updated',)