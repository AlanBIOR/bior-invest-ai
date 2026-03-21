from django.contrib import admin
from django.utils.html import format_html
from .models import Category, GlobalAsset, Investment, Profile

# --- 1. GESTIÓN DE PERFIL (Dashboard Settings) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'capital', 'aportacion')
    search_fields = ('user__username',)

# --- 2. CATEGORÍAS (Estrategia Sugerida) ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_percentage', 'slug')
    list_editable = ('target_percentage',) # Edita el % directo en la tabla
    prepopulated_fields = {'slug': ('name',)}

# --- 3. ACTIVOS GLOBALES (Precios de Mercado) ---
@admin.register(GlobalAsset)
class GlobalAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'current_price', 'last_api_update')
    list_editable = ('current_price',) # Útil para actualizaciones manuales rápidas
    search_fields = ('name', 'symbol')

# --- 4. INVERSIONES (Portafolio Real) ---
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    # Definimos todas las columnas que quieres ver "marcadas"
    list_display = (
        'asset_name', 
        'user', 
        'category',
        'amount_invested', 
        'current_value', 
        'annual_yield',      # <--- Tasa Anual visible
        'performance_display', 
        'platform', 
        'last_updated'
    )
    
    # Habilitamos edición rápida para tasa y valor actual
    list_editable = ('current_value', 'annual_yield')
    
    list_filter = ('category', 'platform', 'user')
    search_fields = ('asset_name', 'platform')
    readonly_fields = ('last_updated',)

    def performance_display(self, obj):
        """Calcula ganancia/pérdida con formato de color blindado"""
        if obj.amount_invested and obj.amount_invested > 0:
            diff = obj.current_value - obj.amount_invested
            porcentaje = (diff / obj.amount_invested) * 100
            
            # Lógica visual
            color = "#27ae60" if diff >= 0 else "#e74c3c"
            signo = "+" if diff > 0 else ""
            
            # Pre-formateo para evitar errores de SafeString
            monto_str = f"{signo}${abs(diff):,.2f}"
            pct_str = f"{porcentaje:,.2f}%"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color, monto_str, pct_str
            )
        return "0.00"

    performance_display.short_description = 'Ganancia / Rendimiento'