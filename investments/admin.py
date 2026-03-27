from django.contrib import admin
from django.utils.html import format_html
from .models import Category, GlobalAsset, Investment, Profile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from decimal import Decimal

# --- 0. SEGURIDAD DE USUARIOS (Solo ver su propio User en el Admin) ---
admin.site.unregister(User)

@admin.register(User)
class MyUserAdmin(UserAdmin):
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        # Si NO es superusuario, quitamos los bloques de "Permisos" y "Fechas importantes"
        if not request.user.is_superuser:
            # Solo dejamos 'Nombre de usuario/Password' e 'Información Personal'
            fieldsets = (
                (None, {'fields': ('username', 'password')}),
                ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        # Si no es superusuario, el nombre de usuario es de solo lectura 
        # para evitar que se cambien el nombre y causen conflictos
        if not request.user.is_superuser:
            return ('username',)
        return super().get_readonly_fields(request, obj)

# --- 1. GESTIÓN DE PERFIL (Dashboard Settings) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'capital', 'aportacion')
    search_fields = ('user__username',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

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

    def get_queryset(self, request):
        """Filtro de privacidad: Solo ver inversiones propias"""
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def performance_display(self, obj):
        """Calcula ganancia/pérdida con formato de color blindado y protección contra nulos"""
        if obj.amount_invested and obj.amount_invested > 0:
            # CORRECCIÓN DE ERROR: Usamos 'or 0' para evitar InvalidOperation si current_value es None
            val_actual = obj.current_value or Decimal('0')
            diff = val_actual - obj.amount_invested
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