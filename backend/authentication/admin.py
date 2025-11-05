from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = [
        'email', 'username', 'full_name', 'rol_badge', 'celular', 
        'is_active', 'verificado_badge', 'cuenta_desactivada', 'created_at'
    ]
    list_filter = [
        'rol', 'is_active', 'verificado', 'disponible', 
        'cuenta_desactivada', 'terminos_aceptados', 'created_at'
    ]
    search_fields = [
        'email', 'username', 'first_name', 'last_name', 'celular', 
        'nombre_negocio', 'ruc', 'placa_vehiculo'
    ]
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    
    # Campos readonly
    readonly_fields = [
        'created_at', 'updated_at', 'last_login', 
        'terminos_fecha_aceptacion', 'terminos_ip_aceptacion',
        'fecha_desactivacion', 'ultimo_login_ip', 'intentos_login_fallidos',
        'cuenta_bloqueada_hasta', 'reset_password_expire', 'reset_password_attempts'
    ]
    
    # CORREGIDO: Cambiado reset_password_token por reset_password_code
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Información Personal', {
            'fields': ('first_name', 'last_name', 'email', 'celular', 'fecha_nacimiento')
        }),
        ('Rol y Permisos', {
            'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Términos y Condiciones', {
            'fields': (
                'terminos_aceptados', 'terminos_fecha_aceptacion', 
                'terminos_version_aceptada', 'terminos_ip_aceptacion'
            ),
            'classes': ('collapse',)
        }),
        ('Datos de Repartidor', {
            'fields': (
                'vehiculo', 'placa_vehiculo', 'licencia_conducir', 'disponible'
            ),
            'classes': ('collapse',)
        }),
        ('Datos de Proveedor', {
            'fields': (
                'nombre_negocio', 'ruc', 'direccion_negocio', 
                'categoria_negocio', 'verificado'
            ),
            'classes': ('collapse',)
        }),
        ('Autenticación con Google', {
            'fields': ('google_picture',),
            'classes': ('collapse',)
        }),
        ('Preferencias de Notificaciones', {
            'fields': (
                'notificaciones_email', 'notificaciones_marketing',
                'notificaciones_pedidos', 'notificaciones_push'
            ),
            'classes': ('collapse',)
        }),
        ('Seguridad y Recuperación de Contraseña', {
            'fields': (
                'intentos_login_fallidos', 'cuenta_bloqueada_hasta',
                'ultimo_login_ip', 'reset_password_code', 'reset_password_expire',
                'reset_password_attempts'
            ),
            'classes': ('collapse',)
        }),
        ('Estado de Cuenta', {
            'fields': (
                'cuenta_desactivada', 'fecha_desactivacion', 'razon_desactivacion'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('created_at', 'updated_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    actions = [
        'verificar_proveedores', 'desverificar_proveedores', 
        'activar_repartidores', 'desactivar_repartidores',
        'activar_cuentas', 'desactivar_cuentas',
        'resetear_intentos_login', 'enviar_email_bienvenida'
    ]
    
    # ==========================================
    # MÉTODOS PERSONALIZADOS PARA DISPLAY
    # ==========================================
    
    def full_name(self, obj):
        """Muestra el nombre completo del usuario"""
        return obj.get_full_name() or '-'
    full_name.short_description = 'Nombre Completo'
    
    def rol_badge(self, obj):
        """Muestra el rol con un badge de color"""
        colors = {
            'USUARIO': '#6c757d',
            'REPARTIDOR': '#28a745',
            'PROVEEDOR': '#007bff',
            'ADMINISTRADOR': '#dc3545'
        }
        color = colors.get(obj.rol, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-size: 11px; font-weight: bold;">{}</span>',
            color,
            obj.get_rol_display()
        )
    rol_badge.short_description = 'Rol'
    
    def verificado_badge(self, obj):
        """Muestra el estado de verificación para proveedores"""
        if obj.es_proveedor():
            if obj.verificado:
                return format_html(
                    '<span style="color: green; font-weight: bold;">✓ Verificado</span>'
                )
            else:
                return format_html(
                    '<span style="color: orange; font-weight: bold;">⚠ Sin verificar</span>'
                )
        return '-'
    verificado_badge.short_description = 'Verificado'
    
    # ==========================================
    # ACCIONES MASIVAS
    # ==========================================
    
    def verificar_proveedores(self, request, queryset):
        """Verifica proveedores seleccionados"""
        updated = queryset.filter(rol='PROVEEDOR').update(verificado=True)
        self.message_user(request, f"{updated} proveedores verificados exitosamente")
    verificar_proveedores.short_description = "✓ Verificar proveedores seleccionados"
    
    def desverificar_proveedores(self, request, queryset):
        """Quita verificación a proveedores"""
        updated = queryset.filter(rol='PROVEEDOR').update(verificado=False)
        self.message_user(request, f"{updated} proveedores desverificados")
    desverificar_proveedores.short_description = "✗ Desverificar proveedores seleccionados"
    
    def activar_repartidores(self, request, queryset):
        """Activa repartidores (disponible = True)"""
        updated = queryset.filter(rol='REPARTIDOR').update(disponible=True)
        self.message_user(request, f"{updated} repartidores activados")
    activar_repartidores.short_description = "🚗 Activar disponibilidad de repartidores"
    
    def desactivar_repartidores(self, request, queryset):
        """Desactiva repartidores (disponible = False)"""
        updated = queryset.filter(rol='REPARTIDOR').update(disponible=False)
        self.message_user(request, f"{updated} repartidores desactivados")
    desactivar_repartidores.short_description = "🚫 Desactivar disponibilidad de repartidores"
    
    def activar_cuentas(self, request, queryset):
        """Activa cuentas de usuarios"""
        updated = queryset.update(is_active=True, cuenta_desactivada=False)
        self.message_user(request, f"{updated} cuentas activadas")
    activar_cuentas.short_description = "✓ Activar cuentas seleccionadas"
    
    def desactivar_cuentas(self, request, queryset):
        """Desactiva cuentas de usuarios"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f"{updated} cuentas desactivadas")
    desactivar_cuentas.short_description = "✗ Desactivar cuentas seleccionadas"
    
    def resetear_intentos_login(self, request, queryset):
        """Resetea los intentos de login fallidos y desbloquea cuentas"""
        updated = queryset.update(
            intentos_login_fallidos=0, 
            cuenta_bloqueada_hasta=None
        )
        self.message_user(request, f"{updated} cuentas desbloqueadas")
    resetear_intentos_login.short_description = "🔓 Resetear intentos de login y desbloquear"
    
    def enviar_email_bienvenida(self, request, queryset):
        """Envía email de bienvenida a usuarios seleccionados"""
        from django.core.mail import send_mass_mail
        from django.conf import settings
        
        emails = []
        for user in queryset:
            if user.puede_recibir_emails():
                message = (
                    'Bienvenido a JP Express',
                    f'Hola {user.get_full_name()},\n\nBienvenido a JP Express.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email]
                )
                emails.append(message)
        
        if emails:
            send_mass_mail(emails, fail_silently=False)
            self.message_user(request, f"{len(emails)} emails enviados")
        else:
            self.message_user(request, "Ningún usuario puede recibir emails", level='warning')
    enviar_email_bienvenida.short_description = "📧 Enviar email de bienvenida"
    
    # ==========================================
    # FILTROS PERSONALIZADOS
    # ==========================================
    
    def get_queryset(self, request):
        """Optimiza las consultas"""
        qs = super().get_queryset(request)
        return qs.select_related()
    
    # ==========================================
    # CONFIGURACIÓN ADICIONAL
    # ==========================================
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar usuarios"""
        return request.user.is_superuser
    
    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }
        js = ('admin/js/custom_admin.js',)