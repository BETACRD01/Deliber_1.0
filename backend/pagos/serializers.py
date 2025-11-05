# pagos/serializers.py
"""
Serializers para el módulo de Pagos (Django REST Framework).

✅ CARACTERÍSTICAS:
- Serialización completa de pagos
- Validaciones robustas
- Campos calculados
- Anidación de relaciones
- Soporte para crear/actualizar pagos
- Serializers específicos por caso de uso
"""
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
from .models import (
    MetodoPago, Pago, Transaccion, EstadisticasPago,
    EstadoPago, TipoMetodoPago, TipoTransaccion
)
import logging

logger = logging.getLogger('pagos')


# ==========================================================
# 💳 SERIALIZER: MÉTODO DE PAGO
# ==========================================================

class MetodoPagoSerializer(serializers.ModelSerializer):
    """Serializer para métodos de pago"""

    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )

    total_pagos_hoy = serializers.SerializerMethodField()

    class Meta:
        model = MetodoPago
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'nombre',
            'descripcion',
            'activo',
            'requiere_verificacion',
            'permite_reembolso',
            'pasarela_nombre',
            'total_pagos_hoy',
            'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']

    def get_total_pagos_hoy(self, obj):
        """Cuenta pagos del día con este método"""
        hoy = timezone.now().date()
        return obj.pagos.filter(creado_en__date=hoy).count()


class MetodoPagoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar métodos (sin datos sensibles)"""

    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )

    class Meta:
        model = MetodoPago
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'nombre',
            'descripcion',
            'activo',
            'requiere_verificacion'
        ]


# ==========================================================
# 📝 SERIALIZER: TRANSACCIÓN
# ==========================================================

class TransaccionSerializer(serializers.ModelSerializer):
    """Serializer para transacciones"""

    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )

    estado_visual = serializers.SerializerMethodField()

    class Meta:
        model = Transaccion
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'monto',
            'exitosa',
            'estado_visual',
            'descripcion',
            'codigo_respuesta',
            'mensaje_respuesta',
            'metadata',
            'creado_en'
        ]
        read_only_fields = ['id', 'creado_en']

    def get_estado_visual(self, obj):
        """Estado con ícono"""
        if obj.exitosa is True:
            return {'icono': '✓', 'texto': 'Exitosa', 'color': 'green'}
        elif obj.exitosa is False:
            return {'icono': '✗', 'texto': 'Fallida', 'color': 'red'}
        else:
            return {'icono': '⏳', 'texto': 'En proceso', 'color': 'orange'}


class TransaccionListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar transacciones"""

    tipo_display = serializers.CharField(
        source='get_tipo_display',
        read_only=True
    )

    class Meta:
        model = Transaccion
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'monto',
            'exitosa',
            'descripcion',
            'creado_en'
        ]


# ==========================================================
# 💰 SERIALIZER: PAGO (Detallado)
# ==========================================================

class PagoDetailSerializer(serializers.ModelSerializer):
    """Serializer detallado para pagos (lectura)"""

    # Relaciones anidadas
    metodo_pago = MetodoPagoListSerializer(read_only=True)
    transacciones = TransaccionListSerializer(many=True, read_only=True)

    # Campos del pedido
    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    pedido_estado = serializers.CharField(
        source='pedido.get_estado_display',
        read_only=True
    )

    # Cliente
    cliente_nombre = serializers.SerializerMethodField()
    cliente_email = serializers.CharField(
        source='pedido.cliente.user.email',
        read_only=True
    )

    # Displays
    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    # Campos calculados
    monto_pendiente_reembolso = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    fue_reembolsado_parcialmente = serializers.BooleanField(read_only=True)
    fue_reembolsado_totalmente = serializers.BooleanField(read_only=True)
    requiere_verificacion_manual = serializers.BooleanField(read_only=True)
    es_tarjeta = serializers.BooleanField(read_only=True)
    es_efectivo = serializers.BooleanField(read_only=True)
    es_transferencia = serializers.BooleanField(read_only=True)
    tiempo_desde_creacion = serializers.CharField(read_only=True)

    # Verificación
    verificado_por_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = [
            'id',
            'referencia',
            'pedido_id',
            'pedido_estado',
            'cliente_nombre',
            'cliente_email',
            'metodo_pago',
            'monto',
            'monto_reembolsado',
            'monto_pendiente_reembolso',
            'estado',
            'estado_display',
            'tarjeta_ultimos_digitos',
            'tarjeta_marca',
            'transferencia_banco',
            'transferencia_numero_operacion',
            'transferencia_comprobante',
            'pasarela_id_transaccion',
            'pasarela_respuesta',
            'metadata',
            'notas',
            'verificado_por_nombre',
            'fecha_verificacion',
            'creado_en',
            'actualizado_en',
            'fecha_completado',
            'fecha_reembolso',
            'fue_reembolsado_parcialmente',
            'fue_reembolsado_totalmente',
            'requiere_verificacion_manual',
            'es_tarjeta',
            'es_efectivo',
            'es_transferencia',
            'tiempo_desde_creacion',
            'transacciones'
        ]
        read_only_fields = [
            'id',
            'referencia',
            'creado_en',
            'actualizado_en',
            'fecha_completado',
            'fecha_reembolso',
            'fecha_verificacion'
        ]

    def get_cliente_nombre(self, obj):
        """Nombre completo del cliente"""
        return obj.pedido.cliente.user.get_full_name()

    def get_verificado_por_nombre(self, obj):
        """Nombre de quien verificó"""
        if obj.verificado_por:
            return obj.verificado_por.get_full_name()
        return None


# ==========================================================
# 💰 SERIALIZER: PAGO (Lista)
# ==========================================================

class PagoListSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listar pagos"""

    metodo_pago_nombre = serializers.CharField(
        source='metodo_pago.nombre',
        read_only=True
    )

    metodo_pago_tipo = serializers.CharField(
        source='metodo_pago.tipo',
        read_only=True
    )

    estado_display = serializers.CharField(
        source='get_estado_display',
        read_only=True
    )

    pedido_id = serializers.IntegerField(source='pedido.id', read_only=True)
    cliente_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Pago
        fields = [
            'id',
            'referencia',
            'pedido_id',
            'cliente_nombre',
            'metodo_pago_nombre',
            'metodo_pago_tipo',
            'monto',
            'estado',
            'estado_display',
            'creado_en'
        ]

    def get_cliente_nombre(self, obj):
        """Nombre del cliente"""
        return obj.pedido.cliente.user.get_full_name()


# ==========================================================
# 💰 SERIALIZER: CREAR PAGO
# ==========================================================

class PagoCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear nuevos pagos"""

    metodo_pago_id = serializers.IntegerField(write_only=True)
    pedido_id = serializers.IntegerField(write_only=True)

    # Campos opcionales según método
    tarjeta_token = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        help_text='Token de la tarjeta (generado por pasarela)'
    )

    transferencia_comprobante_file = serializers.FileField(
        write_only=True,
        required=False,
        allow_null=True,
        help_text='Archivo del comprobante de transferencia'
    )

    class Meta:
        model = Pago
        fields = [
            'pedido_id',
            'metodo_pago_id',
            'monto',
            'tarjeta_token',
            'tarjeta_ultimos_digitos',
            'tarjeta_marca',
            'transferencia_banco',
            'transferencia_numero_operacion',
            'transferencia_comprobante_file',
            'metadata',
            'notas'
        ]

    def validate(self, data):
        """Validaciones personalizadas"""
        pedido_id = data.get('pedido_id')
        metodo_pago_id = data.get('metodo_pago_id')
        monto = data.get('monto')

        # Validar que el pedido existe
        from pedidos.models import Pedido
        try:
            pedido = Pedido.objects.get(pk=pedido_id)
        except Pedido.DoesNotExist:
            raise serializers.ValidationError({
                'pedido_id': 'El pedido no existe'
            })

        # Validar que no tenga un pago ya
        if hasattr(pedido, 'pago'):
            raise serializers.ValidationError({
                'pedido_id': 'El pedido ya tiene un pago asociado'
            })

        # Validar método de pago
        try:
            metodo = MetodoPago.objects.get(pk=metodo_pago_id)
        except MetodoPago.DoesNotExist:
            raise serializers.ValidationError({
                'metodo_pago_id': 'El método de pago no existe'
            })

        if not metodo.activo:
            raise serializers.ValidationError({
                'metodo_pago_id': f'El método {metodo.nombre} no está disponible'
            })

        # Validar monto
        if abs(float(monto) - float(pedido.total)) > 0.01:
            raise serializers.ValidationError({
                'monto': f'El monto debe ser igual al total del pedido (${pedido.total})'
            })

        # Validar campos según método
        if metodo.tipo == TipoMetodoPago.TRANSFERENCIA:
            if not data.get('transferencia_banco'):
                raise serializers.ValidationError({
                    'transferencia_banco': 'Debe especificar el banco de origen'
                })
            if not data.get('transferencia_numero_operacion'):
                raise serializers.ValidationError({
                    'transferencia_numero_operacion': 'Debe proporcionar el número de operación'
                })

        if metodo.tipo in [TipoMetodoPago.TARJETA_CREDITO, TipoMetodoPago.TARJETA_DEBITO]:
            if not data.get('tarjeta_token') and not data.get('tarjeta_ultimos_digitos'):
                raise serializers.ValidationError({
                    'tarjeta_token': 'Debe proporcionar el token de la tarjeta o los últimos dígitos'
                })

        data['pedido'] = pedido
        data['metodo_pago'] = metodo

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Crea el pago"""
        # Extraer datos procesados
        pedido = validated_data.pop('pedido')
        metodo_pago = validated_data.pop('metodo_pago')

        # Extraer campos write_only que no van al modelo
        validated_data.pop('pedido_id', None)
        validated_data.pop('metodo_pago_id', None)
        tarjeta_token = validated_data.pop('tarjeta_token', None)
        comprobante_file = validated_data.pop('transferencia_comprobante_file', None)

        # Crear pago
        pago = Pago.objects.create(
            pedido=pedido,
            metodo_pago=metodo_pago,
            **validated_data
        )

        # Manejar comprobante de transferencia
        if comprobante_file:
            pago.transferencia_comprobante = comprobante_file
            pago.save(update_fields=['transferencia_comprobante'])

        # Procesar según método
        if metodo_pago.tipo == TipoMetodoPago.EFECTIVO:
            # Efectivo se marca como pendiente hasta la entrega
            logger.info(f"✅ Pago en efectivo creado: {pago.referencia}")

        elif metodo_pago.tipo == TipoMetodoPago.TRANSFERENCIA:
            # Transferencia queda pendiente de verificación
            logger.info(
                f"✅ Pago por transferencia creado: {pago.referencia}. "
                f"Requiere verificación manual"
            )

        elif metodo_pago.tipo in [TipoMetodoPago.TARJETA_CREDITO, TipoMetodoPago.TARJETA_DEBITO]:
            # Tarjeta: intentar procesar con pasarela
            if tarjeta_token:
                try:
                    pago.marcar_procesando()
                    # Aquí iría la integración con la pasarela
                    # Por ahora solo logging
                    logger.info(
                        f"⏳ Pago con tarjeta en proceso: {pago.referencia}. "
                        f"Token: {tarjeta_token[:8]}..."
                    )
                except Exception as e:
                    logger.error(f"Error al procesar tarjeta: {e}")
                    pago.marcar_fallido(str(e))

        return pago


# ==========================================================
# 💰 SERIALIZER: ACTUALIZAR ESTADO DE PAGO
# ==========================================================

class PagoUpdateEstadoSerializer(serializers.Serializer):
    """Serializer para actualizar estado del pago"""

    estado = serializers.ChoiceField(
        choices=EstadoPago.choices,
        required=True
    )

    motivo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=500
    )

    pasarela_respuesta = serializers.JSONField(
        required=False,
        allow_null=True
    )

    def validate(self, data):
        """Validar transición de estado"""
        pago = self.context.get('pago')
        nuevo_estado = data.get('estado')

        if not pago:
            raise serializers.ValidationError('Pago no encontrado en contexto')

        # Validar transición
        es_valida, mensaje = pago.validar_transicion_estado(nuevo_estado)
        if not es_valida:
            raise serializers.ValidationError({'estado': mensaje})

        return data

    @transaction.atomic
    def save(self):
        """Actualiza el estado del pago"""
        pago = self.context.get('pago')
        estado = self.validated_data.get('estado')
        motivo = self.validated_data.get('motivo', '')
        pasarela_respuesta = self.validated_data.get('pasarela_respuesta')

        if estado == EstadoPago.COMPLETADO:
            usuario = self.context.get('request').user if self.context.get('request') else None
            pago.marcar_completado(
                verificado_por=usuario,
                pasarela_respuesta=pasarela_respuesta
            )

        elif estado == EstadoPago.FALLIDO:
            pago.marcar_fallido(
                motivo=motivo or 'Marcado como fallido',
                pasarela_respuesta=pasarela_respuesta
            )

        elif estado == EstadoPago.CANCELADO:
            pago.marcar_cancelado(motivo=motivo or 'Cancelado')

        elif estado == EstadoPago.PROCESANDO:
            pago.marcar_procesando()

        return pago


# ==========================================================
# 💰 SERIALIZER: REEMBOLSO
# ==========================================================

class PagoReembolsoSerializer(serializers.Serializer):
    """Serializer para procesar reembolsos"""

    monto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal('0.01'),
        help_text='Monto a reembolsar (null o vacío = reembolso total)'
    )

    motivo = serializers.CharField(
        required=True,
        max_length=500,
        help_text='Razón del reembolso'
    )

    def validate(self, data):
        """Validaciones del reembolso"""
        pago = self.context.get('pago')
        monto = data.get('monto')

        if not pago:
            raise serializers.ValidationError('Pago no encontrado en contexto')

        # Validar estado
        if pago.estado != EstadoPago.COMPLETADO:
            raise serializers.ValidationError({
                'estado': 'Solo se pueden reembolsar pagos completados'
            })

        # Validar método
        if not pago.metodo_pago.permite_reembolso:
            raise serializers.ValidationError({
                'metodo_pago': f'El método {pago.metodo_pago.nombre} no permite reembolsos'
            })

        # Validar monto
        if monto is not None:
            monto_disponible = pago.monto_pendiente_reembolso
            if monto > monto_disponible:
                raise serializers.ValidationError({
                    'monto': f'El monto máximo a reembolsar es ${monto_disponible}'
                })

        return data

    @transaction.atomic
    def save(self):
        """Procesa el reembolso"""
        pago = self.context.get('pago')
        monto = self.validated_data.get('monto')
        motivo = self.validated_data.get('motivo')

        monto_reembolsado = pago.procesar_reembolso(
            monto=monto,
            motivo=motivo
        )

        logger.info(
            f"💰 Reembolso procesado - Pago {pago.referencia}: "
            f"${monto_reembolsado}. Motivo: {motivo}"
        )

        return pago


# ==========================================================
# 📊 SERIALIZER: ESTADÍSTICAS
# ==========================================================

class EstadisticasPagoSerializer(serializers.ModelSerializer):
    """Serializer para estadísticas de pagos"""

    # Métricas calculadas
    porcentaje_completados = serializers.SerializerMethodField()
    porcentaje_fallidos = serializers.SerializerMethodField()

    # Distribución por método
    distribucion_metodos = serializers.SerializerMethodField()

    class Meta:
        model = EstadisticasPago
        fields = [
            'id',
            'fecha',
            'total_pagos',
            'pagos_completados',
            'pagos_pendientes',
            'pagos_fallidos',
            'pagos_reembolsados',
            'porcentaje_completados',
            'porcentaje_fallidos',
            'monto_total',
            'monto_efectivo',
            'monto_transferencias',
            'monto_tarjetas',
            'monto_reembolsado',
            'ticket_promedio',
            'tasa_exito',
            'distribucion_metodos',
            'actualizado_en'
        ]

    def get_porcentaje_completados(self, obj):
        """Porcentaje de pagos completados"""
        if obj.total_pagos > 0:
            return round((obj.pagos_completados / obj.total_pagos) * 100, 2)
        return 0

    def get_porcentaje_fallidos(self, obj):
        """Porcentaje de pagos fallidos"""
        if obj.total_pagos > 0:
            return round((obj.pagos_fallidos / obj.total_pagos) * 100, 2)
        return 0

    def get_distribucion_metodos(self, obj):
        """Distribución de montos por método"""
        total = float(obj.monto_total) if obj.monto_total > 0 else 1

        return {
            'efectivo': {
                'monto': float(obj.monto_efectivo or 0),
                'porcentaje': round((float(obj.monto_efectivo or 0) / total) * 100, 2)
            },
            'transferencias': {
                'monto': float(obj.monto_transferencias or 0),
                'porcentaje': round((float(obj.monto_transferencias or 0) / total) * 100, 2)
            },
            'tarjetas': {
                'monto': float(obj.monto_tarjetas or 0),
                'porcentaje': round((float(obj.monto_tarjetas or 0) / total) * 100, 2)
            }
        }


# ==========================================================
# 📊 SERIALIZER: RESUMEN DE PAGO
# ==========================================================

class PagoResumenSerializer(serializers.Serializer):
    """Serializer para resumen rápido del pago"""

    referencia = serializers.UUIDField()
    pedido_id = serializers.IntegerField()
    metodo = serializers.CharField()
    monto = serializers.DecimalField(max_digits=10, decimal_places=2)
    estado = serializers.CharField()
    estado_display = serializers.CharField()
    reembolsado = serializers.DecimalField(max_digits=10, decimal_places=2)
    pendiente_reembolso = serializers.DecimalField(max_digits=10, decimal_places=2)
    creado_en = serializers.DateTimeField()
    completado_en = serializers.DateTimeField(allow_null=True)
