# pedidos/serializers.py (CORREGIDO Y MEJORADO)
"""
Serializers para la aplicación de Pedidos.

✅ CORRECCIONES APLICADAS:
- Validaciones de coordenadas geográficas (Ecuador)
- Validaciones cruzadas mejoradas
- Mensajes de error más descriptivos
- Optimización de queries con select_related
- Manejo robusto de campos opcionales
"""
from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from decimal import Decimal
import re

from .models import Pedido, EstadoPedido, TipoPedido
from usuarios.models import Perfil
from repartidores.models import Repartidor
from proveedores.models import Proveedor


# ==========================================================
# 🌍 VALIDADORES PERSONALIZADOS (NUEVOS)
# ==========================================================

def validar_latitud_ecuador(value):
    """
    ✅ NUEVO: Valida que la latitud esté dentro del rango de Ecuador
    Ecuador: -5.0° a 2.0° de latitud
    """
    if value is None:
        return value

    if not isinstance(value, (int, float, Decimal)):
        raise serializers.ValidationError(
            "La latitud debe ser un número."
        )

    if not (-5.0 <= float(value) <= 2.0):
        raise serializers.ValidationError(
            "La latitud debe estar entre -5.0 y 2.0 (rango de Ecuador). "
            f"Valor proporcionado: {value}"
        )

    return value


def validar_longitud_ecuador(value):
    """
    ✅ NUEVO: Valida que la longitud esté dentro del rango de Ecuador
    Ecuador: -92.0° a -75.0° de longitud
    """
    if value is None:
        return value

    if not isinstance(value, (int, float, Decimal)):
        raise serializers.ValidationError(
            "La longitud debe ser un número."
        )

    if not (-92.0 <= float(value) <= -75.0):
        raise serializers.ValidationError(
            "La longitud debe estar entre -92.0 y -75.0 (rango de Ecuador). "
            f"Valor proporcionado: {value}"
        )

    return value


def validar_direccion(value):
    """
    ✅ NUEVO: Valida que la dirección tenga un formato mínimo aceptable
    """
    if not value or not value.strip():
        raise serializers.ValidationError(
            "La dirección no puede estar vacía."
        )

    # Mínimo 10 caracteres para una dirección válida
    if len(value.strip()) < 10:
        raise serializers.ValidationError(
            "La dirección debe tener al menos 10 caracteres. "
            "Ejemplo: 'Av. Principal 123, Puyo'"
        )

    return value.strip()


# ==========================================================
# 📦 CREACIÓN DE PEDIDO (CLIENTE) - MEJORADO
# ==========================================================
class PedidoCreateSerializer(serializers.ModelSerializer):
    """
    ✅ MEJORADO: Serializer para crear pedidos con validaciones robustas

    Validaciones implementadas:
    - Coordenadas geográficas (rango de Ecuador)
    - Dirección con formato mínimo
    - Total positivo
    - Proveedor activo y verificado
    - Tipo de pedido vs campos requeridos
    """

    # ✅ Campos con validadores personalizados
    latitud_destino = serializers.FloatField(
        required=False,
        allow_null=True,
        validators=[validar_latitud_ecuador],
        help_text="Latitud de destino (-5.0 a 2.0)"
    )

    longitud_destino = serializers.FloatField(
        required=False,
        allow_null=True,
        validators=[validar_longitud_ecuador],
        help_text="Longitud de destino (-92.0 a -75.0)"
    )

    latitud_origen = serializers.FloatField(
        required=False,
        allow_null=True,
        validators=[validar_latitud_ecuador],
        help_text="Latitud de origen (-5.0 a 2.0)"
    )

    longitud_origen = serializers.FloatField(
        required=False,
        allow_null=True,
        validators=[validar_longitud_ecuador],
        help_text="Longitud de origen (-92.0 a -75.0)"
    )

    direccion_entrega = serializers.CharField(
        validators=[validar_direccion],
        help_text="Dirección completa de entrega (mín. 10 caracteres)"
    )

    direccion_origen = serializers.CharField(
        required=False,
        allow_blank=True,
        validators=[validar_direccion],
        help_text="Dirección de origen (para pedidos de proveedor)"
    )

    class Meta:
        model = Pedido
        fields = [
            'tipo',
            'descripcion',
            'proveedor',
            'direccion_origen',
            'latitud_origen',
            'longitud_origen',
            'direccion_entrega',
            'latitud_destino',
            'longitud_destino',
            'metodo_pago',
            'total',
        ]

    def validate_total(self, value):
        """✅ MEJORADO: Valida que el total sea positivo y razonable"""
        if value <= 0:
            raise serializers.ValidationError(
                "El total del pedido debe ser mayor que cero."
            )

        # ✅ NUEVO: Validar que no sea un monto excesivo
        if value > 1000:
            raise serializers.ValidationError(
                "El total del pedido no puede superar $1000. "
                "Para montos mayores, contacte con soporte."
            )

        return value

    def validate_proveedor(self, value):
        """✅ MEJORADO: Valida que el proveedor exista, esté activo y verificado"""
        if value is None:
            return value

        if not value.activo:
            raise serializers.ValidationError(
                f"El proveedor '{value.nombre}' no está disponible actualmente."
            )

        # ✅ NUEVO: Validar que esté verificado
        if not value.verificado:
            raise serializers.ValidationError(
                f"El proveedor '{value.nombre}' aún no ha sido verificado. "
                "Por favor, seleccione otro proveedor."
            )

        return value

    def validate_descripcion(self, value):
        """✅ NUEVO: Valida descripción para encargos directos"""
        if value and len(value.strip()) < 10:
            raise serializers.ValidationError(
                "La descripción debe tener al menos 10 caracteres para ser clara."
            )
        return value.strip() if value else ""

    def validate(self, data):
        """✅ MEJORADO: Validaciones cruzadas con mensajes claros"""
        tipo = data.get('tipo')
        proveedor = data.get('proveedor')
        descripcion = data.get('descripcion', '').strip()
        direccion_entrega = data.get('direccion_entrega', '').strip()

        # ✅ Validar proveedor según tipo
        if tipo == TipoPedido.PROVEEDOR:
            if not proveedor:
                raise serializers.ValidationError({
                    'proveedor': "Debe seleccionar un proveedor para un pedido de tipo proveedor."
                })

            # ✅ NUEVO: Validar direccion_origen para pedidos de proveedor
            if not data.get('direccion_origen'):
                # Auto-completar con dirección del proveedor
                data['direccion_origen'] = proveedor.direccion or "Dirección del proveedor"

                # ✅ Auto-completar coordenadas de origen si existen
                if proveedor.latitud and proveedor.longitud:
                    data['latitud_origen'] = float(proveedor.latitud)
                    data['longitud_origen'] = float(proveedor.longitud)

        elif tipo == TipoPedido.DIRECTO:
            # ✅ Validar descripción para encargo directo
            if not descripcion:
                raise serializers.ValidationError({
                    'descripcion': "Debe indicar una descripción clara para el encargo directo."
                })

            # ✅ NUEVO: Encargo directo no debe tener proveedor
            if proveedor:
                raise serializers.ValidationError({
                    'proveedor': "Un encargo directo no debe tener proveedor asignado."
                })

        # ✅ Validar direccion de entrega
        if not direccion_entrega:
            raise serializers.ValidationError({
                'direccion_entrega': "La dirección de entrega es obligatoria."
            })

        # ✅ NUEVO: Validar que coordenadas estén completas
        lat_dest = data.get('latitud_destino')
        lon_dest = data.get('longitud_destino')

        if (lat_dest is not None) != (lon_dest is not None):
            raise serializers.ValidationError({
                'coordenadas': "Debe proporcionar tanto latitud como longitud de destino, o ninguna."
            })

        # ✅ NUEVO: Similar para origen
        lat_orig = data.get('latitud_origen')
        lon_orig = data.get('longitud_origen')

        if (lat_orig is not None) != (lon_orig is not None):
            raise serializers.ValidationError({
                'coordenadas': "Debe proporcionar tanto latitud como longitud de origen, o ninguna."
            })

        return data

    def create(self, validated_data):
        """✅ MEJORADO: Crea el pedido con logging"""
        user = self.context['request'].user

        if not hasattr(user, 'perfil'):
            raise serializers.ValidationError(
                "El usuario no tiene un perfil asociado. "
                "Contacte con soporte."
            )

        cliente = user.perfil

        # ✅ Crear pedido
        pedido = Pedido.objects.create(cliente=cliente, **validated_data)

        # Logging se hace en signals
        return pedido


# ==========================================================
# 📋 LISTADO / DETALLE DE PEDIDOS - MEJORADO
# ==========================================================
class PedidoListSerializer(serializers.ModelSerializer):
    """✅ MEJORADO: Serializer optimizado para listado de pedidos"""

    cliente_nombre = serializers.CharField(
        source='cliente.user.get_full_name',
        read_only=True
    )
    cliente_email = serializers.EmailField(
        source='cliente.user.email',
        read_only=True
    )
    proveedor_nombre = serializers.CharField(
        source='proveedor.nombre',
        read_only=True,
        allow_null=True
    )
    repartidor_nombre = serializers.CharField(
        source='repartidor.user.get_full_name',
        read_only=True,
        allow_null=True
    )
    tiempo_transcurrido = serializers.SerializerMethodField()
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )
    puede_cancelarse = serializers.BooleanField(
        source='puede_ser_cancelado',
        read_only=True
    )

    # ✅ NUEVO: Indicador de ubicación completa
    tiene_ubicacion = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'estado',
            'estado_display',
            'descripcion',
            'cliente_nombre',
            'cliente_email',
            'proveedor_nombre',
            'repartidor_nombre',
            'direccion_entrega',
            'metodo_pago',
            'total',
            'creado_en',
            'tiempo_transcurrido',
            'puede_cancelarse',
            'tiene_ubicacion',  # ✅ NUEVO
        ]

    def get_tiempo_transcurrido(self, obj):
        """Calcula el tiempo transcurrido desde la creación"""
        return obj.tiempo_transcurrido

    def get_tiene_ubicacion(self, obj):
        """✅ NUEVO: Indica si tiene coordenadas completas"""
        return obj.tiene_ubicacion_completa


# ==========================================================
# 🧭 DETALLE DE PEDIDO COMPLETO - MEJORADO
# ==========================================================
class PedidoDetailSerializer(serializers.ModelSerializer):
    """✅ MEJORADO: Serializer con información completa y optimizada"""

    cliente = serializers.SerializerMethodField()
    proveedor = serializers.SerializerMethodField()
    repartidor = serializers.SerializerMethodField()
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )
    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )
    tiempo_transcurrido = serializers.CharField(read_only=True)
    puede_cancelarse = serializers.BooleanField(
        source='puede_ser_cancelado',
        read_only=True
    )
    es_activo = serializers.BooleanField(
        source='es_pedido_activo',
        read_only=True
    )

    # ✅ NUEVO: Campos de ubicación formateados
    ubicacion_destino = serializers.SerializerMethodField()
    ubicacion_origen = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'

    def get_cliente(self, obj):
        """✅ MEJORADO: Información completa del cliente"""
        try:
            return {
                'id': obj.cliente.id,
                'nombre': obj.cliente.user.get_full_name() or obj.cliente.user.username,
                'email': obj.cliente.user.email,
                'celular': getattr(obj.cliente.user, 'celular', None),
                'verificado': getattr(obj.cliente.user, 'verificado', False),
            }
        except AttributeError as e:
            return {
                'id': obj.cliente.id,
                'error': f"Error al obtener datos del cliente: {str(e)}"
            }

    def get_proveedor(self, obj):
        """✅ MEJORADO: Información completa del proveedor"""
        if not obj.proveedor:
            return None

        try:
            return {
                'id': obj.proveedor.id,
                'nombre': obj.proveedor.nombre,
                'direccion': obj.proveedor.direccion,
                'telefono': obj.proveedor.telefono,
                'ciudad': obj.proveedor.ciudad,
                'verificado': obj.proveedor.verificado,
                'activo': obj.proveedor.activo,
            }
        except AttributeError as e:
            return {
                'id': obj.proveedor.id,
                'error': f"Error al obtener datos del proveedor: {str(e)}"
            }

    def get_repartidor(self, obj):
        """✅ MEJORADO: Información completa del repartidor"""
        if not obj.repartidor:
            return None

        try:
            return {
                'id': obj.repartidor.id,
                'nombre': obj.repartidor.user.get_full_name() or obj.repartidor.user.username,
                'celular': getattr(obj.repartidor.user, 'celular', None),
                'vehiculo': getattr(obj.repartidor, 'tipo_vehiculo', None),
                'disponible': getattr(obj.repartidor, 'disponible', False),
            }
        except AttributeError as e:
            return {
                'id': obj.repartidor.id,
                'error': f"Error al obtener datos del repartidor: {str(e)}"
            }

    def get_ubicacion_destino(self, obj):
        """✅ NUEVO: Ubicación de destino formateada"""
        if obj.latitud_destino and obj.longitud_destino:
            return {
                'latitud': obj.latitud_destino,
                'longitud': obj.longitud_destino,
                'direccion': obj.direccion_entrega,
                'tiene_coordenadas': True
            }
        return {
            'direccion': obj.direccion_entrega,
            'tiene_coordenadas': False
        }

    def get_ubicacion_origen(self, obj):
        """✅ NUEVO: Ubicación de origen formateada"""
        if obj.latitud_origen and obj.longitud_origen:
            return {
                'latitud': obj.latitud_origen,
                'longitud': obj.longitud_origen,
                'direccion': obj.direccion_origen,
                'tiene_coordenadas': True
            }
        return {
            'direccion': obj.direccion_origen or 'No especificada',
            'tiene_coordenadas': False
        }


# ==========================================================
# 🚀 ACCIONES DE ESTADO (PROVEEDOR / REPARTIDOR / ADMIN)
# ==========================================================
class PedidoEstadoUpdateSerializer(serializers.Serializer):
    """✅ MEJORADO: Validación robusta de transiciones de estado"""

    nuevo_estado = serializers.ChoiceField(choices=EstadoPedido.choices)

    def validate_nuevo_estado(self, value):
        """✅ MEJORADO: Valida transiciones con mensajes descriptivos"""
        pedido = self.context.get('pedido')

        if not pedido:
            raise serializers.ValidationError("Pedido no encontrado en el contexto.")

        # ✅ Validar que no esté en estado final
        if pedido.estado == EstadoPedido.ENTREGADO:
            raise serializers.ValidationError(
                "El pedido ya fue entregado y no puede cambiar de estado."
            )

        if pedido.estado == EstadoPedido.CANCELADO:
            raise serializers.ValidationError(
                "El pedido está cancelado y no puede cambiar de estado."
            )

        # ✅ Validar que no sea el mismo estado
        if pedido.estado == value:
            raise serializers.ValidationError(
                f"El pedido ya está en estado '{pedido.get_estado_display()}'."
            )

        # ✅ MEJORADO: Validar transiciones válidas con mensajes claros
        transiciones_validas = {
            EstadoPedido.CONFIRMADO: {
                'permitidos': [EstadoPedido.EN_PREPARACION, EstadoPedido.CANCELADO],
                'mensaje': "Desde 'Confirmado' solo puede pasar a 'En preparación' o 'Cancelado'"
            },
            EstadoPedido.EN_PREPARACION: {
                'permitidos': [EstadoPedido.EN_RUTA, EstadoPedido.CANCELADO],
                'mensaje': "Desde 'En preparación' solo puede pasar a 'En ruta' o 'Cancelado'"
            },
            EstadoPedido.EN_RUTA: {
                'permitidos': [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO],
                'mensaje': "Desde 'En ruta' solo puede pasar a 'Entregado' o 'Cancelado'"
            },
        }

        config = transiciones_validas.get(pedido.estado)
        if config:
            estados_permitidos = config['permitidos']
            if value not in estados_permitidos:
                raise serializers.ValidationError(
                    f"{config['mensaje']}. "
                    f"Estado actual: {pedido.get_estado_display()}, "
                    f"Estado solicitado: {dict(EstadoPedido.choices)[value]}"
                )

        # ✅ NUEVO: Validar repartidor para ciertos estados
        if value == EstadoPedido.EN_RUTA and not pedido.repartidor:
            raise serializers.ValidationError(
                "No se puede marcar 'En ruta' sin un repartidor asignado."
            )

        return value

    def update(self, instance, validated_data):
        """✅ MEJORADO: Ejecuta el cambio de estado con manejo de errores"""
        nuevo_estado = validated_data['nuevo_estado']

        try:
            if nuevo_estado == EstadoPedido.EN_PREPARACION:
                instance.marcar_en_preparacion()
            elif nuevo_estado == EstadoPedido.EN_RUTA:
                instance.marcar_en_ruta()
            elif nuevo_estado == EstadoPedido.ENTREGADO:
                instance.marcar_entregado()
            elif nuevo_estado == EstadoPedido.CANCELADO:
                instance.cancelar(
                    "Cancelado desde cambio de estado",
                    actor="sistema"
                )

        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return instance


# ==========================================================
# 🛵 ACEPTACIÓN DEL PEDIDO (REPARTIDOR) - MEJORADO
# ==========================================================
class PedidoAceptarRepartidorSerializer(serializers.Serializer):
    """✅ MEJORADO: Validación robusta para aceptación de pedidos"""

    repartidor_id = serializers.IntegerField()

    def validate_repartidor_id(self, value):
        """✅ MEJORADO: Valida repartidor con verificaciones adicionales"""
        try:
            repartidor = Repartidor.objects.select_related('user').get(id=value)
        except Repartidor.DoesNotExist:
            raise serializers.ValidationError(
                f"Repartidor con ID {value} no encontrado."
            )

        if not repartidor.disponible:
            raise serializers.ValidationError(
                f"El repartidor '{repartidor.user.get_full_name()}' no está disponible. "
                f"Estado actual: {repartidor.estado}"
            )

        # ✅ NUEVO: Validar que el usuario esté activo
        if not repartidor.user.is_active:
            raise serializers.ValidationError(
                "El repartidor no tiene una cuenta activa."
            )

        return value

    def validate(self, data):
        """✅ MEJORADO: Validación del pedido con mensajes claros"""
        pedido = self.context.get('pedido')

        if not pedido:
            raise serializers.ValidationError("Pedido no encontrado.")

        if pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise serializers.ValidationError(
                f"No se puede aceptar un pedido en estado '{pedido.get_estado_display()}'."
            )

        if pedido.repartidor:
            raise serializers.ValidationError(
                f"Este pedido ya fue aceptado por {pedido.repartidor.user.get_full_name()}."
            )

        return data

    def save(self, **kwargs):
        """✅ MEJORADO: Ejecuta la aceptación con manejo de errores"""
        pedido = self.context['pedido']
        repartidor_id = self.validated_data['repartidor_id']

        try:
            repartidor = Repartidor.objects.get(id=repartidor_id)
            pedido.aceptar_por_repartidor(repartidor)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return pedido


# ==========================================================
# 🍳 CONFIRMACIÓN DEL PROVEEDOR - MEJORADO
# ==========================================================
class PedidoConfirmarProveedorSerializer(serializers.Serializer):
    """✅ MEJORADO: Validación para confirmación de proveedor"""

    proveedor_id = serializers.IntegerField()

    def validate_proveedor_id(self, value):
        """✅ MEJORADO: Valida proveedor"""
        try:
            proveedor = Proveedor.objects.get(id=value)
        except Proveedor.DoesNotExist:
            raise serializers.ValidationError(
                f"Proveedor con ID {value} no encontrado."
            )

        # ✅ NUEVO: Validar que esté activo
        if not proveedor.activo:
            raise serializers.ValidationError(
                f"El proveedor '{proveedor.nombre}' no está activo."
            )

        return value

    def validate(self, data):
        """✅ MEJORADO: Validación del pedido"""
        pedido = self.context.get('pedido')
        proveedor_id = data.get('proveedor_id')

        if not pedido:
            raise serializers.ValidationError("Pedido no encontrado.")

        if pedido.tipo != TipoPedido.PROVEEDOR:
            raise serializers.ValidationError(
                "Solo los pedidos de tipo 'Proveedor' pueden ser confirmados por un proveedor."
            )

        if pedido.proveedor_id != proveedor_id:
            raise serializers.ValidationError(
                f"Este pedido pertenece a otro proveedor. "
                f"Proveedor del pedido: {pedido.proveedor.nombre}"
            )

        if pedido.estado in [EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO]:
            raise serializers.ValidationError(
                f"No se puede confirmar un pedido en estado '{pedido.get_estado_display()}'."
            )

        return data

    def save(self, **kwargs):
        """✅ MEJORADO: Ejecuta la confirmación"""
        pedido = self.context['pedido']

        try:
            pedido.confirmar_por_proveedor()
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return pedido


# ==========================================================
# 🚫 CANCELACIÓN DEL PEDIDO - MEJORADO
# ==========================================================
class PedidoCancelacionSerializer(serializers.Serializer):
    """✅ MEJORADO: Validación robusta para cancelación"""

    motivo = serializers.CharField(
        max_length=500,  # ✅ NUEVO: Límite aumentado
        required=True,
        help_text="Motivo de la cancelación (mínimo 10 caracteres)"
    )

    def validate_motivo(self, value):
        """✅ MEJORADO: Valida que el motivo sea descriptivo"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "Debe proporcionar un motivo para la cancelación."
            )

        # ✅ NUEVO: Validar longitud mínima
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "El motivo debe tener al menos 10 caracteres para ser claro."
            )

        return value.strip()

    def validate(self, data):
        """✅ MEJORADO: Validación del pedido"""
        pedido = self.context.get('pedido')

        if not pedido:
            raise serializers.ValidationError("Pedido no encontrado.")

        if not pedido.puede_ser_cancelado:
            raise serializers.ValidationError(
                f"Este pedido no puede ser cancelado porque está en estado "
                f"'{pedido.get_estado_display()}'."
            )

        return data

    def save(self, **kwargs):
        """✅ MEJORADO: Ejecuta la cancelación con identificación del actor"""
        pedido = self.context['pedido']
        user = self.context['request'].user
        motivo = self.validated_data['motivo']

        # ✅ MEJORADO: Determinar el actor con más detalle
        actor = 'desconocido'
        if user.is_staff or user.is_superuser:
            actor = f'admin:{user.email}'
        elif hasattr(user, 'perfil'):
            rol = user.perfil.rol.upper()
            actor = f'{rol.lower()}:{user.email}'

        try:
            pedido.cancelar(motivo, actor)
        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))

        return pedido


# ==========================================================
# 💰 DISTRIBUCIÓN DE GANANCIAS (SOLO LECTURA) - MEJORADO
# ==========================================================
class PedidoGananciasSerializer(serializers.ModelSerializer):
    """✅ MEJORADO: Muestra distribución con porcentajes calculados"""

    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )
    porcentaje_repartidor = serializers.SerializerMethodField()
    porcentaje_proveedor = serializers.SerializerMethodField()
    porcentaje_app = serializers.SerializerMethodField()

    # ✅ NUEVO: Validación de suma
    suma_correcta = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'total',
            'comision_repartidor',
            'porcentaje_repartidor',
            'comision_proveedor',
            'porcentaje_proveedor',
            'ganancia_app',
            'porcentaje_app',
            'suma_correcta',  # ✅ NUEVO
        ]

    def get_porcentaje_repartidor(self, obj):
        """Calcula el porcentaje del repartidor"""
        if obj.total > 0:
            return round((float(obj.comision_repartidor) / float(obj.total)) * 100, 2)
        return 0

    def get_porcentaje_proveedor(self, obj):
        """Calcula el porcentaje del proveedor"""
        if obj.total > 0:
            return round((float(obj.comision_proveedor) / float(obj.total)) * 100, 2)
        return 0

    def get_porcentaje_app(self, obj):
        """Calcula el porcentaje de la app"""
        if obj.total > 0:
            return round((float(obj.ganancia_app) / float(obj.total)) * 100, 2)
        return 0

    def get_suma_correcta(self, obj):
        """✅ NUEVO: Verifica que la suma de comisiones sea igual al total"""
        suma = float(obj.comision_repartidor) + float(obj.comision_proveedor) + float(obj.ganancia_app)
        diferencia = abs(float(obj.total) - suma)

        # Tolerancia de 1 centavo por redondeo
        es_correcta = diferencia < 0.02

        return {
            'es_correcta': es_correcta,
            'total_pedido': float(obj.total),
            'suma_comisiones': round(suma, 2),
            'diferencia': round(diferencia, 2)
        }
