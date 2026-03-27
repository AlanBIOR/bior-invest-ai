from django.contrib import admin
from django.utils.html import format_html
from .models import Category, GlobalAsset, Investment, Profile
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from decimal import Decimal

# --- 0. CONFIGURACIÓN DE PERFIL INTEGRADO (INLINE) ---
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Información del Perfil (WhatsApp / Capital)'
    # Aquí defines qué campos del Profile quieres editar desde el User
    fields = ('whatsapp_number', 'capital', 'aportacion')
    fk_name = 'user'

# --- 1. SEGURIDAD DE USUARIOS (Con Profile integrado) ---
admin.site.unregister(User)

@admin.register(User)
class MyUserAdmin(UserAdmin):
    # Agregamos el inline aquí para que aparezca al final de la ficha del usuario
    inlines = (ProfileInline,)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(id=request.user.id)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        
        if not request.user.is_superuser:
            # Para el usuario Alan/Staff: Ocultamos permisos y grupos
            fieldsets = (
                (None, {'fields': ('username', 'password')}),
                ('Información personal', {'fields': ('first_name', 'last_name', 'email')}),
            )
        return fieldsets

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ('username',)
        return super().get_readonly_fields(request, obj)

# --- 2. GESTIÓN DE PERFIL (Opcional: Mantenerlo también como sección independiente) ---
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'whatsapp_number', 'capital', 'aportacion')
    search_fields = ('user__username', 'whatsapp_number')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

# --- 3. CATEGORÍAS (Estrategia Sugerida) ---
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'target_percentage', 'slug')
    list_editable = ('target_percentage',)
    prepopulated_fields = {'slug': ('name',)}

# --- 4. ACTIVOS GLOBALES (Precios de Mercado) ---
@admin.register(GlobalAsset)
class GlobalAssetAdmin(admin.ModelAdmin):
    list_display = ('name', 'symbol', 'current_price', 'last_api_update')
    list_editable = ('current_price',)
    search_fields = ('name', 'symbol')

# --- 5. INVERSIONES (Portafolio Real) ---
@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        'asset_name', 
        'user', 
        'category',
        'amount_invested', 
        'current_value', 
        'annual_yield',
        'performance_display', 
        'platform', 
        'last_updated'
    )
    
    list_editable = ('current_value', 'annual_yield')
    list_filter = ('category', 'platform', 'user')
    search_fields = ('asset_name', 'platform')
    readonly_fields = ('last_updated',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)

    def performance_display(self, obj):
        if obj.amount_invested and obj.amount_invested > 0:
            val_actual = obj.current_value or Decimal('0')
            diff = val_actual - obj.amount_invested
            porcentaje = (diff / obj.amount_invested) * 100
            
            color = "#27ae60" if diff >= 0 else "#e74c3c"
            signo = "+" if diff > 0 else ""
            
            monto_str = f"{signo}${abs(diff):,.2f}"
            pct_str = f"{porcentaje:,.2f}%"
            
            return format_html(
                '<span style="color: {}; font-weight: bold;">{} ({})</span>',
                color, monto_str, pct_str
            )
        return "0.00"

    performance_display.short_description = 'Ganancia / Rendimiento'