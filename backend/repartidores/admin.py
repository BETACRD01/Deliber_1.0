# repartidores/admin.py
from django.contrib import admin, messages
from django.utils.html import format_html
from django.utils.timezone import localtime
from django.template.response import TemplateResponse
from django.urls import path, reverse
from django.db.models import Count, Avg
from .models import (
    Repartidor, RepartidorVehiculo, HistorialUbicacion,
    RepartidorEstadoLog, CalificacionRepartidor, CalificacionCliente,
    EstadoRepartidor
)


# ============================
# Inlines (ligeros / de lectura)
# ============================
class RepartidorVehiculoInline(admin.TabularInline):
    model = RepartidorVehiculo
    extra = 0
    fields = ("tipo", "placa", "activo", "licencia_foto")
    readonly_fields = ()
    show_change_link = True


class RepartidorEstadoLogInline(admin.TabularInline):
    model = RepartidorEstadoLog
    extra = 0
    fields = ("estado_anterior", "estado_nuevo", "motivo", "timestamp")
    readonly_fields = ("estado_anterior", "estado_nuevo", "motivo", "timestamp")
    can_delete = False
    ordering = ("-timestamp",)
    max_num = 10  # Limitar registros mostrados


# ============================
# Actions (acciones masivas)
# ============================
@admin.action(description="✅ Marcar seleccionados como VERIFICADOS")
def action_marcar_verificados(modeladmin, request, queryset):
    updated = queryset.update(verificado=True)
    messages.success(request, f"{updated} repartidor(es) verificados.")


@admin.action(description="🚫 Desactivar repartidores seleccionados")
def action_desactivar(modeladmin, request, queryset):
    updated = queryset.update(activo=False, estado=EstadoRepartidor.FUERA_SERVICIO)
    messages.warning(request, f"{updated} repartidor(es) desactivados y fuera de servicio.")


@admin.action(description="🟢 Poner en DISPONIBLE")
def action_estado_disponible(modeladmin, request, queryset):
    updated = queryset.filter(verificado=True, activo=True).update(estado=EstadoRepartidor.DISPONIBLE)
    messages.info(request, f"{updated} repartidor(es) marcados como DISPONIBLE (solo verificados y activos).")


@admin.action(description="🔵 Poner en OCUPADO")
def action_estado_ocupado(modeladmin, request, queryset):
    updated = queryset.filter(verificado=True, activo=True).update(estado=EstadoRepartidor.OCUPADO)
    messages.info(request, f"{updated} repartidor(es) marcados como OCUPADO (solo verificados y activos).")


@admin.action(description="🔴 Poner en FUERA DE SERVICIO")
def action_estado_fuera_servicio(modeladmin, request, queryset):
    updated = queryset.update(estado=EstadoRepartidor.FUERA_SERVICIO)
    messages.info(request, f"{updated} repartidor(es) marcados como FUERA DE SERVICIO.")


# ============================
# Utilidades de presentación
# ============================
def _badge_estado(estado: str) -> str:
    """Genera un badge HTML con color según el estado."""
    colors = {
        EstadoRepartidor.DISPONIBLE: "#22c55e",   # green
        EstadoRepartidor.OCUPADO: "#3b82f6",      # blue
        EstadoRepartidor.FUERA_SERVICIO: "#ef4444" # red
    }
    color = colors.get(estado, "#6b7280")  # gray
    return f'<span style="padding:4px 12px;border-radius:12px;background:{color};color:#fff;font-weight:600;font-size:11px;">{estado}</span>'


# ============================
# RepartidorAdmin
# ============================
@admin.register(Repartidor)
class RepartidorAdmin(admin.ModelAdmin):
    list_display = (
        "id", "foto_preview", "nombre", "email",
        "estado_badge", "verificado", "activo",
        "calificacion_promedio", "entregas_completadas",
        "posicion", "ultima_localizacion_local", "creado_en_local",
    )
    list_filter = (
        "estado", "verificado", "activo",
        ("creado_en", admin.DateFieldListFilter),
    )
    search_fields = (
        "user__first_name", "user__last_name", "user__email",
        "cedula", "telefono", "vehiculos__placa"
    )
    readonly_fields = (
        "creado_en", "actualizado_en", "ultima_localizacion",
        "posicion_link", "estado_badge_readonly",
    )
    inlines = [RepartidorVehiculoInline, RepartidorEstadoLogInline]
    actions = [
        action_marcar_verificados, action_desactivar,
        action_estado_disponible, action_estado_ocupado, action_estado_fuera_servicio
    ]
    list_select_related = ("user",)
    ordering = ("-creado_en",)
    date_hierarchy = "creado_en"
    list_per_page = 25

    fieldsets = (
        ("👤 Identidad", {
            "fields": (
                ("user", "foto_perfil", "foto_preview"),
                ("cedula", "telefono"),
            )
        }),
        ("⚙️ Estado y control", {
            "fields": (
                ("estado", "estado_badge_readonly"),
                ("verificado", "activo"),
            )
        }),
        ("📍 Ubicación", {
            "fields": (
                ("latitud", "longitud"),
                ("ultima_localizacion", "posicion_link"),
            )
        }),
        ("📈 Métricas", {
            "fields": (
                ("entregas_completadas", "calificacion_promedio"),
                ("creado_en", "actualizado_en"),
            )
        }),
    )

    def get_queryset(self, request):
        """Optimiza las consultas con select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("user")

    # ---------- Métodos de presentación ----------
    def nombre(self, obj):
        return obj.user.get_full_name() or obj.user.email
    nombre.short_description = "Nombre"
    nombre.admin_order_field = "user__first_name"

    def email(self, obj):
        return obj.user.email
    email.short_description = "Email"
    email.admin_order_field = "user__email"

    def foto_preview(self, obj):
        if obj.foto_perfil:
            return format_html(
                '<img src="{}" style="height:40px;width:40px;border-radius:50%;object-fit:cover;" />',
                obj.foto_perfil.url
            )
        return "–"
    foto_preview.short_description = "Foto"

    def estado_badge(self, obj):
        return format_html(_badge_estado(obj.estado))
    estado_badge.short_description = "Estado"
    estado_badge.admin_order_field = "estado"

    def estado_badge_readonly(self, obj):
        return self.estado_badge(obj)
    estado_badge_readonly.short_description = "Estado (badge)"

    def posicion(self, obj):
        if obj.latitud is not None and obj.longitud is not None:
            return f"{obj.latitud:.5f}, {obj.longitud:.5f}"
        return "–"
    posicion.short_description = "Posición"

    def posicion_link(self, obj):
        if obj.latitud is not None and obj.longitud is not None:
            url = f"https://maps.google.com/?q={obj.latitud},{obj.longitud}"
            return format_html('<a target="_blank" href="{}">🗺️ Ver en Google Maps</a>', url)
        return "–"
    posicion_link.short_description = "Mapa"

    def ultima_localizacion_local(self, obj):
        return localtime(obj.ultima_localizacion) if obj.ultima_localizacion else "–"
    ultima_localizacion_local.short_description = "Últ. loc. (local)"

    def creado_en_local(self, obj):
        return localtime(obj.creado_en)
    creado_en_local.short_description = "Creado (local)"


# ============================
# HistorialUbicacionAdmin
# ============================
@admin.register(HistorialUbicacion)
class HistorialUbicacionAdmin(admin.ModelAdmin):
    list_display = ("id", "repartidor", "latitud", "longitud", "timestamp_local", "mapa")
    list_filter = (
        "repartidor",
        ("timestamp", admin.DateFieldListFilter),
    )
    search_fields = (
        "repartidor__user__email",
        "repartidor__user__first_name",
        "repartidor__user__last_name"
    )
    ordering = ("-timestamp",)
    list_select_related = ("repartidor__user",)
    list_per_page = 50
    raw_id_fields = ("repartidor",)
    date_hierarchy = "timestamp"

    def timestamp_local(self, obj):
        return localtime(obj.timestamp)
    timestamp_local.short_description = "Fecha (local)"
    timestamp_local.admin_order_field = "timestamp"

    def mapa(self, obj):
        url = f"https://maps.google.com/?q={obj.latitud},{obj.longitud}"
        return format_html('<a target="_blank" href="{}">🗺️ Ver</a>', url)
    mapa.short_description = "Mapa"


# ============================
# RepartidorVehiculoAdmin
# ============================
@admin.register(RepartidorVehiculo)
class RepartidorVehiculoAdmin(admin.ModelAdmin):
    list_display = ("id", "repartidor", "tipo", "placa", "activo", "creado_en")
    list_filter = ("tipo", "activo")
    search_fields = ("repartidor__user__email", "placa")
    list_select_related = ("repartidor__user",)
    ordering = ("-creado_en",)
    raw_id_fields = ("repartidor",)
    date_hierarchy = "creado_en"


# ============================
# Logs de Estado (solo lectura)
# ============================
@admin.register(RepartidorEstadoLog)
class RepartidorEstadoLogAdmin(admin.ModelAdmin):
    list_display = ("id", "repartidor", "estado_anterior", "estado_nuevo", "motivo", "timestamp_local")
    list_filter = (
        "estado_nuevo",
        "estado_anterior",
        ("timestamp", admin.DateFieldListFilter),
    )
    search_fields = ("repartidor__user__email", "motivo")
    ordering = ("-timestamp",)
    raw_id_fields = ("repartidor",)
    date_hierarchy = "timestamp"
    list_select_related = ("repartidor__user",)

    def has_add_permission(self, request):
        return False  # solo se crean desde lógica del modelo

    def has_change_permission(self, request, obj=None):
        return False  # solo lectura

    def has_delete_permission(self, request, obj=None):
        return False  # no se pueden eliminar logs

    def timestamp_local(self, obj):
        return localtime(obj.timestamp)
    timestamp_local.short_description = "Fecha (local)"
    timestamp_local.admin_order_field = "timestamp"


# ============================
# Calificaciones (Cliente → Repartidor)
# ============================
@admin.register(CalificacionRepartidor)
class CalificacionRepartidorAdmin(admin.ModelAdmin):
    list_display = ("id", "repartidor", "cliente", "pedido_id", "puntuacion", "creado_en")
    list_filter = (
        "puntuacion",
        ("creado_en", admin.DateFieldListFilter),
    )
    search_fields = (
        "repartidor__user__email",
        "cliente__email",
        "pedido_id"
    )
    ordering = ("-creado_en",)
    raw_id_fields = ("repartidor", "cliente")
    date_hierarchy = "creado_en"
    list_select_related = ("repartidor__user", "cliente")
    readonly_fields = ("creado_en", "actualizado_en")


# ============================
# Calificaciones (Repartidor → Cliente)
# ============================
@admin.register(CalificacionCliente)
class CalificacionClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "cliente", "repartidor", "pedido_id", "puntuacion", "creado_en")
    list_filter = (
        "puntuacion",
        ("creado_en", admin.DateFieldListFilter),
    )
    search_fields = (
        "cliente__email",
        "repartidor__user__email",
        "pedido_id"
    )
    ordering = ("-creado_en",)
    raw_id_fields = ("cliente", "repartidor")
    date_hierarchy = "creado_en"
    list_select_related = ("cliente", "repartidor__user")
    readonly_fields = ("creado_en", "actualizado_en")


# ============================
# Vista personalizada: Mapa de Repartidores
# ============================
class RepartidorMapaAdmin(admin.ModelAdmin):
    """
    Vista personalizada para mostrar mapa de repartidores activos.
    Se registra manualmente en el admin site.
    """

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


# Registrar la vista de mapa como una entrada personalizada en el admin
# Nota: Esto requiere sobrescribir el AdminSite o usar un enfoque alternativo
# Por simplicidad, se puede acceder directamente mediante URL personalizada

# Función de vista para el mapa
def mapa_repartidores_view(request):
    """Vista personalizada que muestra el mapa de repartidores activos."""
    if not request.user.is_staff:
        from django.contrib.auth.views import redirect_to_login
        return redirect_to_login(request.get_full_path())

    import json
    from decimal import Decimal

    repartidores = Repartidor.objects.filter(
        activo=True,
        verificado=True
    ).exclude(
        latitud__isnull=True
    ).select_related('user').values(
        "id",
        "user__first_name",
        "user__last_name",
        "estado",
        "latitud",
        "longitud",
        "calificacion_promedio"
    )

    # Convertir Decimal a float para JSON
    repartidores_list = []
    for rep in repartidores:
        rep_dict = dict(rep)
        if isinstance(rep_dict.get('calificacion_promedio'), Decimal):
            rep_dict['calificacion_promedio'] = float(rep_dict['calificacion_promedio'])
        repartidores_list.append(rep_dict)

    # Serializar a JSON
    repartidores_json = json.dumps(repartidores_list)

    context = {
        "site_title": "Administración de Repartidores",
        "site_header": "Panel de Administración",
        "title": "Mapa de Repartidores Activos",
        "repartidores": repartidores_json,
        "total_repartidores": len(repartidores_list),
    }

    return TemplateResponse(
        request,
        "admin/repartidores/mapa_repartidores.html",
        context
    )


# Registrar URLs personalizadas en el admin
def get_admin_urls():
    """Retorna URLs personalizadas para el admin."""
    urls = [
        path(
            'repartidores/mapa/',
            admin.site.admin_view(mapa_repartidores_view),
            name='repartidores_mapa'
        ),
    ]
    return urls


# Hook para agregar las URLs al admin site
# Debes añadir esto en tu urls.py principal:
# from repartidores.admin import get_admin_urls
# urlpatterns += get_admin_urls()
