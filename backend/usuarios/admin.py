# usuarios/admin.py

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.db.models import Count, Q
from .models import Perfil, DireccionFavorita, MetodoPago


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'telefono_usuario',
        'total_pedidos',
        'pedidos_mes_actual',
        'puede_participar',
        'calificacion_display',
        'total_resenas',
        'es_cliente_frecuente_display',
        'tiene_fcm_display',
        'actualizado_en'
    ]

    list_filter = [
        'calificacion',
        'participa_en_sorteos',
        'notificaciones_pedido',
        'notificaciones_promociones',
        'actualizado_en'
    ]

    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'user__celular']

    readonly_fields = [
        'total_pedidos',
        'pedidos_mes_actual',
        'ultima_actualizacion_mes',
        'calificacion',
        'total_resenas',
        'edad',
        'es_cliente_frecuente',
        'puede_participar_rifa',
        'puede_recibir_notificaciones',
        'fcm_token',
        'fcm_token_actualizado',
        'creado_en',
        'actualizado_en'
    ]

    fieldsets = (
        ('Usuario', {
            'fields': ('user',)
        }),
        ('Información Personal', {
            'fields': ('foto_perfil', 'fecha_nacimiento', 'edad')
        }),
        ('📱 Notificaciones Push (FCM)', {
            'fields': (
                'puede_recibir_notificaciones',
                'fcm_token',
                'fcm_token_actualizado'
            ),
            'classes': ('collapse',),
            'description': 'Información sobre notificaciones push del dispositivo'
        }),
        ('Estadísticas de Pedidos', {
            'fields': (
                'total_pedidos',
                'pedidos_mes_actual',
                'ultima_actualizacion_mes',
                'es_cliente_frecuente'
            ),
            'classes': ('collapse',)
        }),
        ('Sistema de Rifas', {
            'fields': (
                'participa_en_sorteos',
                'puede_participar_rifa'
            ),
            'description': 'El usuario necesita mínimo 3 pedidos en el mes para participar en rifas'
        }),
        ('Calificaciones', {
            'fields': ('calificacion', 'total_resenas')
        }),
        ('Preferencias de Notificaciones', {
            'fields': (
                'notificaciones_pedido',
                'notificaciones_promociones'
            ),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'resetear_contador_mensual',
        'marcar_participa_rifas',
        'desmarcar_participa_rifas',
        'eliminar_tokens_fcm'
    ]

    # ============================================
    # OPTIMIZACIÓN DE QUERIES
    # ============================================

    def get_queryset(self, request):
        """Optimiza las queries con select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('user')

    # ============================================
    # MÉTODOS DE VISUALIZACIÓN
    # ============================================

    @admin.display(description='Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Teléfono')
    def telefono_usuario(self, obj):
        """✅ Muestra el celular del User"""
        if obj.user and getattr(obj.user, 'celular', None):
            return obj.user.celular
        return format_html('<span style="color: #999;">Sin teléfono</span>')

    @admin.display(description='Calificación', ordering='calificacion')
    def calificacion_display(self, obj):
        """✅ CORREGIDO: Muestra calificación con color y formato seguro"""
        try:
            valor = float(obj.calificacion or 0)
        except (TypeError, ValueError):
            valor = 0.0

        color = '#28a745' if valor >= 4.0 else '#ffc107' if valor >= 3.0 else '#dc3545'
        return format_html(
            '<span style="color: {}; font-weight: bold;">★ {}</span>',
            color,
            f'{valor:.1f}'
        )

    @admin.display(description='Participa en Rifa', ordering='pedidos_mes_actual')
    def puede_participar(self, obj):
        if obj.puede_participar_rifa:
            return format_html(
                '<span style="color: #28a745; font-weight: bold;">✓ Sí ({} pedidos)</span>',
                obj.pedidos_mes_actual
            )
        else:
            return format_html(
                '<span style="color: #dc3545;">✗ No ({}/3 pedidos)</span>',
                obj.pedidos_mes_actual
            )

    @admin.display(description='Cliente Frecuente', boolean=True)
    def es_cliente_frecuente_display(self, obj):
        return obj.es_cliente_frecuente

    @admin.display(description='Notificaciones Push')
    def tiene_fcm_display(self, obj):
        if obj.fcm_token:
            return format_html('<span style="color: #28a745; font-weight: bold;">📱 Activo</span>')
        return format_html('<span style="color: #999;">⌀ Sin token</span>')

    # ============================================
    # ACCIONES PERSONALIZADAS
    # ============================================

    def resetear_contador_mensual(self, request, queryset):
        count = 0
        for perfil in queryset:
            perfil.resetear_mes()
            count += 1
        self.message_user(request, f'Se reseteó el contador mensual de {count} perfil(es).')
    resetear_contador_mensual.short_description = 'Resetear contador mensual de rifas'

    def marcar_participa_rifas(self, request, queryset):
        count = queryset.update(participa_en_sorteos=True)
        self.message_user(request, f'{count} perfil(es) ahora participan en rifas.')
    marcar_participa_rifas.short_description = 'Activar participación en rifas'

    def desmarcar_participa_rifas(self, request, queryset):
        count = queryset.update(participa_en_sorteos=False)
        self.message_user(request, f'{count} perfil(es) ya no participan en rifas.')
    desmarcar_participa_rifas.short_description = 'Desactivar participación en rifas'

    def eliminar_tokens_fcm(self, request, queryset):
        count = 0
        for perfil in queryset:
            if perfil.fcm_token:
                perfil.eliminar_fcm_token()
                count += 1
        self.message_user(
            request,
            f'Se eliminaron {count} token(s) FCM. Los usuarios deberán volver a iniciar sesión para recibir notificaciones.'
        )
    eliminar_tokens_fcm.short_description = '🔒 Eliminar tokens FCM (cerrar sesión)'


# ============================================
# DIRECCIÓN FAVORITA ADMIN
# ============================================

@admin.register(DireccionFavorita)
class DireccionFavoritaAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'tipo_direccion',
        'telefono_usuario',
        'etiqueta',
        'ciudad_info',
        'es_predeterminada',
        'activa',
        'veces_usada',
        'ultimo_uso',
        'created_at'
    ]

    @admin.display(description='Teléfono')
    def telefono_usuario(self, obj):
        """Muestra el celular del usuario"""
        if obj.user and getattr(obj.user, 'celular', None):
            return obj.user.celular
        return format_html('<span style="color: #999;">Sin teléfono</span>')

    list_filter = [
        'tipo',
        'es_predeterminada',
        'activa',
        'ciudad',
        'created_at'
    ]

    search_fields = ['user__email', 'etiqueta', 'direccion', 'ciudad']

    readonly_fields = [
        'id',
        'veces_usada',
        'ultimo_uso',
        'direccion_completa',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Usuario', {'fields': ('user',)}),
        ('Información de la Dirección', {
            'fields': ('tipo', 'etiqueta', 'direccion', 'referencia', 'ciudad', 'direccion_completa')
        }),
        ('Ubicación (Coordenadas)', {
            'fields': ('latitud', 'longitud'),
            'description': 'Coordenadas GPS para el mapa'
        }),
        ('Configuración', {'fields': ('es_predeterminada', 'activa')}),
        ('Estadísticas de Uso', {
            'fields': ('veces_usada', 'ultimo_uso'),
            'classes': ('collapse',)
        }),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['marcar_predeterminada', 'activar_direcciones', 'desactivar_direcciones']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

    @admin.display(description='Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Tipo')
    def tipo_direccion(self, obj):
        iconos = {'casa': '🏠', 'trabajo': '💼', 'otro': '📍'}
        icono = iconos.get(obj.tipo, '📍')
        return f'{icono} {obj.get_tipo_display()}'

    @admin.display(description='Ciudad')
    def ciudad_info(self, obj):
        if obj.ciudad:
            return obj.ciudad
        return format_html('<span style="color: #999;">Sin ciudad</span>')

    # ============================================
    # ACCIONES PERSONALIZADAS
    # ============================================

    def marcar_predeterminada(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                'Solo puedes marcar una dirección como predeterminada a la vez.',
                level='error'
            )
            return

        direccion = queryset.first()
        DireccionFavorita.objects.filter(
            user=direccion.user,
            es_predeterminada=True
        ).update(es_predeterminada=False)

        direccion.es_predeterminada = True
        direccion.save()
        self.message_user(request, f'Dirección "{direccion.etiqueta}" marcada como predeterminada.')
    marcar_predeterminada.short_description = 'Marcar como predeterminada'

    def activar_direcciones(self, request, queryset):
        count = queryset.update(activa=True)
        self.message_user(request, f'{count} dirección(es) activada(s).')
    activar_direcciones.short_description = 'Activar direcciones'

    def desactivar_direcciones(self, request, queryset):
        count = queryset.filter(activa=True).update(activa=False, es_predeterminada=False)
        self.message_user(request, f'{count} dirección(es) desactivada(s).')
    desactivar_direcciones.short_description = 'Desactivar direcciones'


# ============================================
# MÉTODO DE PAGO ADMIN (✅ CORREGIDO)
# ============================================

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = [
        'user_email',
        'tipo_pago',
        'alias',
        'tiene_comprobante_display',
        'observaciones_display',
        'es_predeterminado',
        'activo',
        'created_at'
    ]

    list_filter = ['tipo', 'es_predeterminado', 'activo', 'created_at']

    search_fields = ['user__email', 'alias', 'observaciones']

    readonly_fields = [
        'id',
        'tiene_comprobante',
        'requiere_verificacion',
        'ver_comprobante',
        'created_at',
        'updated_at'
    ]

    fieldsets = (
        ('Usuario', {'fields': ('user',)}),
        ('Información del Método de Pago', {'fields': ('tipo', 'alias')}),
        ('✅ Comprobante de Pago', {
            'fields': (
                'comprobante_pago',
                'ver_comprobante',
                'tiene_comprobante',
                'requiere_verificacion'
            ),
            'description': 'Comprobante obligatorio para transferencias. El repartidor/admin debe verificar.'
        }),
        ('📝 Observaciones', {
            'fields': ('observaciones',),
            'description': 'Problemas o notas sobre el pago (máx. 100 caracteres)'
        }),
        ('Configuración', {'fields': ('es_predeterminado', 'activo')}),
        ('Auditoría', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = [
        'marcar_predeterminado',
        'activar_metodos',
        'desactivar_metodos',
        'ver_comprobantes'
    ]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')

    @admin.display(description='Email', ordering='user__email')
    def user_email(self, obj):
        return obj.user.email

    @admin.display(description='Tipo de Pago')
    def tipo_pago(self, obj):
        iconos = {'efectivo': '💵', 'transferencia': '🏦'}
        icono = iconos.get(obj.tipo, '💳')
        return f'{icono} {obj.get_tipo_display()}'

    @admin.display(description='Comprobante')
    def tiene_comprobante_display(self, obj):
        if obj.tiene_comprobante:
            return format_html('<span style="color: #28a745; font-weight: bold;">✓ Sí</span>')
        if obj.tipo == 'transferencia':
            return format_html('<span style="color: #dc3545; font-weight: bold;">✗ Falta</span>')
        return format_html('<span style="color: #999;">- No requiere</span>')

    @admin.display(description='Observaciones')
    def observaciones_display(self, obj):
        if obj.observaciones:
            return format_html(
                '<span style="color: #ff6b6b;" title="{}">{}</span>',
                obj.observaciones,
                obj.observaciones[:30] + '...' if len(obj.observaciones) > 30 else obj.observaciones
            )
        return format_html('<span style="color: #999;">Sin observaciones</span>')

    @admin.display(description='🖼️ Vista Previa del Comprobante')
    def ver_comprobante(self, obj):
        if obj.comprobante_pago:
            return format_html(
                '<a href="{}" target="_blank">'
                '<img src="{}" style="max-width: 300px; max-height: 300px; border: 1px solid #ddd; border-radius: 4px;"/>'
                '</a><br><br>'
                '<a href="{}" target="_blank" class="button">🔍 Ver en tamaño completo</a>',
                obj.comprobante_pago.url,
                obj.comprobante_pago.url,
                obj.comprobante_pago.url
            )
        return format_html('<span style="color: #999;">Sin comprobante</span>')

    # ============================================
    # ACCIONES PERSONALIZADAS
    # ============================================

    def marcar_predeterminado(self, request, queryset):
        if queryset.count() > 1:
            self.message_user(
                request,
                'Solo puedes marcar un método como predeterminado a la vez.',
                level='error'
            )
            return

        metodo = queryset.first()
        MetodoPago.objects.filter(user=metodo.user, es_predeterminado=True).update(es_predeterminado=False)

        metodo.es_predeterminado = True
        metodo.save()
        self.message_user(request, f'Método "{metodo.alias}" marcado como predeterminado.')
    marcar_predeterminado.short_description = 'Marcar como predeterminado'

    def activar_metodos(self, request, queryset):
        count = queryset.update(activo=True)
        self.message_user(request, f'{count} método(s) de pago activado(s).')
    activar_metodos.short_description = 'Activar métodos de pago'

    def desactivar_metodos(self, request, queryset):
        count = queryset.filter(activo=True).update(activo=False, es_predeterminado=False)
        self.message_user(request, f'{count} método(s) de pago desactivado(s).')
    desactivar_metodos.short_description = 'Desactivar métodos de pago'

    def ver_comprobantes(self, request, queryset):
        count = queryset.filter(comprobante_pago__isnull=False).count()
        if count == 0:
            self.message_user(request, 'Los métodos seleccionados no tienen comprobantes.', level='warning')
        else:
            self.message_user(request, f'{count} método(s) con comprobante. Revisa cada uno en detalle.')
    ver_comprobantes.short_description = '🔍 Ver comprobantes de pago'

# ============================================
# SOLICITUD DE CAMBIO DE ROL ADMIN
# ============================================

from .models import SolicitudCambioRol
import logging

logger = logging.getLogger('usuarios')

@admin.register(SolicitudCambioRol)
class SolicitudCambioRolAdmin(admin.ModelAdmin):
    list_display = [
        'usuario_email',
        'rol_icon',
        'estado_badge',
        'dias_pendiente',
        'creado_en'
    ]
    
    list_filter = ['estado', 'rol_solicitado', 'creado_en']
    search_fields = ['user__email', 'motivo']
    
    readonly_fields = [
        'user',
        'rol_solicitado',
        'motivo',
        'creado_en',
        'respondido_en',
        'admin_responsable'
    ]
    
    fieldsets = (
        ('📋 Solicitud', {
            'fields': (
                'user',
                'rol_solicitado',
                'motivo',
                'creado_en'
            )
        }),
        ('✅/❌ Respuesta', {
            'fields': (
                'estado',
                'admin_responsable',
                'motivo_respuesta',
                'respondido_en'
            ),
            'description': 'Selecciona estado para aceptar o rechazar'
        }),
    )
    
    actions = ['aceptar_solicitud', 'rechazar_solicitud']
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user', 'admin_responsable')
    
    @admin.display(description='Usuario', ordering='user__email')
    def usuario_email(self, obj):
        return obj.user.email
    
    @admin.display(description='Rol')
    def rol_icon(self, obj):
        iconos = {'PROVEEDOR': '🏪', 'REPARTIDOR': '🚚'}
        icono = iconos.get(obj.rol_solicitado, '👤')
        return f"{icono} {obj.get_rol_solicitado_display()}"
    
    @admin.display(description='Estado')
    def estado_badge(self, obj):
        colores = {
            'PENDIENTE': '#FFC107',
            'ACEPTADA': '#28A745',
            'RECHAZADA': '#DC3545'
        }
        color = colores.get(obj.estado, '#999')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_estado_display()
        )
    
    def aceptar_solicitud(self, request, queryset):
        """Acepta solicitudes pendientes"""
        aceptadas = 0
        errores = 0
        
        for solicitud in queryset.filter(estado='PENDIENTE'):
            try:
                solicitud.aceptar(request.user, 'Aceptada por administrador')
                aceptadas += 1
                logger.info(
                    f"✅ Admin {request.user.email} aceptó: "
                    f"{solicitud.user.email} → {solicitud.rol_solicitado}"
                )
            except Exception as e:
                logger.error(f"❌ Error aceptando: {e}")
                errores += 1
        
        msg = f"✅ {aceptadas} aceptada(s)"
        if errores > 0:
            msg += f" | ❌ {errores} error(es)"
        
        self.message_user(request, msg)
    
    aceptar_solicitud.short_description = "✅ Aceptar solicitudes"
    
    def rechazar_solicitud(self, request, queryset):
        """Rechaza solicitudes pendientes"""
        rechazadas = 0
        
        for solicitud in queryset.filter(estado='PENDIENTE'):
            solicitud.rechazar(request.user, 'Rechazada por administrador')
            rechazadas += 1
            logger.warning(
                f"❌ Admin {request.user.email} rechazó: "
                f"{solicitud.user.email} → {solicitud.rol_solicitado}"
            )
        
        self.message_user(request, f"❌ {rechazadas} rechazada(s)")
    
    rechazar_solicitud.short_description = "❌ Rechazar solicitudes"
