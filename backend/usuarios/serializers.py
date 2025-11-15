# -*- coding: utf-8 -*-
# usuarios/serializers.py

from rest_framework import serializers
from django.db import transaction
from authentication.models import User
from .models import Perfil, DireccionFavorita, MetodoPago, UbicacionUsuario
import re
import os
import logging

logger = logging.getLogger("usuarios")

# ============================================
# SERIALIZERS PARA PERFIL
# ============================================


class PerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para el perfil del usuario
    ✅ telefono viene del User.celular
    """

    usuario_email = serializers.CharField(source="user.email", read_only=True)
    usuario_nombre = serializers.CharField(source="user.get_full_name", read_only=True)
    telefono = serializers.CharField(source="user.celular", read_only=True)
    edad = serializers.IntegerField(read_only=True)
    es_cliente_frecuente = serializers.BooleanField(read_only=True)
    tiene_telefono = serializers.BooleanField(read_only=True)
    puede_participar_rifa = serializers.BooleanField(read_only=True)
    puede_recibir_notificaciones = serializers.BooleanField(read_only=True)
    foto_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = [
            "id",
            "usuario_email",
            "usuario_nombre",
            "foto_perfil",
            "telefono",
            "fecha_nacimiento",
            "edad",
            "calificacion",
            "total_resenas",
            "total_pedidos",
            "es_cliente_frecuente",
            "tiene_telefono",
            "puede_participar_rifa",
            "notificaciones_pedido",
            "notificaciones_promociones",
            "puede_recibir_notificaciones",
            "fcm_token_actualizado",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = [
            "id",
            "telefono",
            "calificacion",
            "total_resenas",
            "total_pedidos",
            "edad",
            "es_cliente_frecuente",
            "tiene_telefono",
            "puede_participar_rifa",
            "puede_recibir_notificaciones",
            "fcm_token_actualizado",
            "creado_en",
            "actualizado_en",
        ]

    def get_foto_perfil(self, obj):
        """Devuelve URL completa sin duplicación"""
        if obj.foto_perfil:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto_perfil.url)
            return obj.foto_perfil.url
        return None


class PerfilPublicoSerializer(serializers.ModelSerializer):
    """Serializer para mostrar perfil público (sin datos sensibles)"""

    usuario_nombre = serializers.CharField(source="user.get_full_name", read_only=True)
    foto_perfil = serializers.SerializerMethodField()

    class Meta:
        model = Perfil
        fields = [
            "usuario_nombre",
            "foto_perfil",
            "calificacion",
            "total_resenas",
            "total_pedidos",
        ]

    def get_foto_perfil(self, obj):
        """URL completa o null"""
        if obj.foto_perfil:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.foto_perfil.url)
            return obj.foto_perfil.url
        return None


class ActualizarPerfilSerializer(serializers.ModelSerializer):
    """Serializer para actualizar el perfil del usuario"""

    class Meta:
        model = Perfil
        fields = [
            "foto_perfil",
            "fecha_nacimiento",
            "notificaciones_pedido",
            "notificaciones_promociones",
            "participa_en_sorteos",
        ]

    def validate_telefono(self, value):
        """Valida el formato del teléfono"""
        if value and not re.match(r"^\+?1?\d{9,15}$", value):
            raise serializers.ValidationError(
                "El número de teléfono debe tener entre 9 y 15 dígitos."
            )
        return value

    def validate_fecha_nacimiento(self, value):
        """Valida que la fecha de nacimiento sea válida"""
        from datetime import date

        if value and value > date.today():
            raise serializers.ValidationError(
                "La fecha de nacimiento no puede ser futura."
            )

        if value:
            today = date.today()
            edad = (
                today.year
                - value.year
                - ((today.month, today.day) < (value.month, value.day))
            )
            if edad < 13:
                raise serializers.ValidationError(
                    "Debes tener al menos 13 años para usar la aplicación."
                )

        return value

    def validate_foto_perfil(self, value):
        """Validación flexible de imágenes"""
        if value:
            max_size = 5 * 1024 * 1024
            if value.size > max_size:
                tamano_mb = value.size / (1024 * 1024)
                raise serializers.ValidationError(
                    f"La imagen no puede superar 5MB (actual: {tamano_mb:.1f}MB)"
                )

            valid_extensions = [".jpg", ".jpeg", ".png", ".webp"]
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Formato no válido. Use: {', '.join(valid_extensions)}"
                )

            if hasattr(value, "content_type") and value.content_type:
                valid_mime_types = [
                    "image/jpeg",
                    "image/png",
                    "image/webp",
                    "image/jpg",
                ]
                if value.content_type not in valid_mime_types:
                    raise serializers.ValidationError(
                        "El archivo debe ser una imagen válida (JPEG, PNG o WebP)"
                    )

        return value

    def update(self, instance, validated_data):
        """Método personalizado para manejar actualizaciones"""
        foto_nueva = validated_data.get("foto_perfil")

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()

        if foto_nueva:
            logger.info(f"📸 Foto de perfil actualizada: {instance.user.email}")

        return instance


# ============================================
# SERIALIZERS PARA DIRECCIONES
# ============================================


class DireccionFavoritaSerializer(serializers.ModelSerializer):
    """Serializer para direcciones guardadas"""

    direccion_completa = serializers.CharField(read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = DireccionFavorita
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "etiqueta",
            "direccion",
            "referencia",
            "latitud",
            "longitud",
            "ciudad",
            "es_predeterminada",
            "activa",
            "veces_usada",
            "ultimo_uso",
            "direccion_completa",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "veces_usada",
            "ultimo_uso",
            "direccion_completa",
            "created_at",
            "updated_at",
        ]


class CrearDireccionSerializer(serializers.ModelSerializer):
    """
    Serializer para crear nuevas direcciones
    ✅ MEJORADO: Genera etiqueta automática si no viene del frontend
    """

    # ✅ Etiqueta OPCIONAL (no requerida)
    etiqueta = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = DireccionFavorita
        fields = [
            "tipo",
            "etiqueta",
            "direccion",
            "referencia",
            "latitud",
            "longitud",
            "ciudad",
            "es_predeterminada",
        ]

    def validate_etiqueta(self, value):
        """✅ Validación solo si viene etiqueta del frontend"""
        if value and value.strip():
            value = value.strip()

            if len(value) < 2:
                raise serializers.ValidationError(
                    "La etiqueta debe tener al menos 2 caracteres"
                )

            if len(value) > 50:
                raise serializers.ValidationError(
                    "La etiqueta no puede exceder 50 caracteres"
                )

            return value

        # Si viene vacía, retornar None (se generará después)
        return None

    def validate_direccion(self, value):
        """Validar que la dirección no esté vacía"""
        if not value or not value.strip():
            raise serializers.ValidationError("La dirección no puede estar vacía")

        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "La dirección debe tener al menos 10 caracteres"
            )

        return value

    def validate_latitud(self, value):
        """Validación de latitud para Ecuador"""
        if not (-5.0 <= value <= 2.0):
            raise serializers.ValidationError(
                f"La latitud debe estar dentro del territorio ecuatoriano (-5° a 2°). "
                f"Valor recibido: {value}"
            )
        return value

    def validate_longitud(self, value):
        """Validación de longitud para Ecuador"""
        if not (-92.0 <= value <= -75.0):
            raise serializers.ValidationError(
                f"La longitud debe estar dentro del territorio ecuatoriano (-92° a -75°). "
                f"Valor recibido: {value}"
            )
        return value

    def validate_ciudad(self, value):
        """Validar ciudad"""
        if value:
            value = value.strip()
            if len(value) < 2:
                raise serializers.ValidationError(
                    "El nombre de la ciudad debe tener al menos 2 caracteres"
                )
        return value

    def validate(self, data):
        """
        ✅ VALIDACIÓN PRINCIPAL:
        1. Genera etiqueta automática si no viene
        2. Valida duplicados
        3. Valida ubicación cercana (COMENTADO para desarrollo)
        """
        user = self.context["request"].user

        # 1️⃣ Validar campos obligatorios
        required_fields = ["direccion", "latitud", "longitud"]
        for field in required_fields:
            if not data.get(field):
                raise serializers.ValidationError({field: "Este campo es obligatorio"})

        lat = data.get("latitud")
        lon = data.get("longitud")
        etiqueta = data.get("etiqueta")

        # 2️⃣ ✅ GENERAR ETIQUETA AUTOMÁTICA si no viene o viene vacía
        if not etiqueta or not str(etiqueta).strip():
            etiqueta = self._generar_etiqueta_unica(user)
            data["etiqueta"] = etiqueta
            logger.info(
                f"📝 Etiqueta generada automáticamente: '{etiqueta}' para {user.email}"
            )
        else:
            # Si viene etiqueta, limpiar espacios
            etiqueta = str(etiqueta).strip()
            data["etiqueta"] = etiqueta

            # ✅ MEJORADO: Validar contra TODAS las direcciones (activas e inactivas)
            if DireccionFavorita.objects.filter(
                user=user, etiqueta__iexact=etiqueta
            ).exists():
                raise serializers.ValidationError(
                    {
                        "etiqueta": f'Ya tienes una dirección con la etiqueta "{etiqueta}". Usa otra.'
                    }
                )

        # 3️⃣ ✅ COMENTADO: Validar ubicación muy cercana (para permitir pruebas)
        # if lat and lon:
        #     direccion_similar = DireccionFavorita.objects.filter(
        #         user=user,
        #         activa=True,
        #         latitud__range=(lat - 0.0005, lat + 0.0005),
        #         longitud__range=(lon - 0.0005, lon + 0.0005)
        #     ).first()
        #
        #     if direccion_similar:
        #         logger.warning(
        #             f"⚠️ Dirección cercana detectada: '{direccion_similar.etiqueta}' "
        #             f"en ({direccion_similar.latitud}, {direccion_similar.longitud})"
        #         )
        #         raise serializers.ValidationError({
        #             'latitud': (
        #                 f'Ya tienes una dirección muy cercana: "{direccion_similar.etiqueta}". '
        #                 f'Si es la misma ubicación, actualiza la existente.'
        #             )
        #         })

        return data

    def _generar_etiqueta_unica(self, user):
        """
        ✅ Genera una etiqueta única para el usuario
        MEJORADO: Busca números disponibles incluso si hay etiquetas eliminadas

        Args:
            user: Usuario autenticado

        Returns:
            str: Etiqueta única generada
        """
        # Obtener TODAS las etiquetas existentes (incluyendo inactivas)
        etiquetas_existentes = set(
            DireccionFavorita.objects.filter(user=user).values_list(
                "etiqueta", flat=True
            )
        )

        logger.info(
            f"📋 Etiquetas existentes para {user.email}: {etiquetas_existentes}"
        )

        # Buscar el primer número disponible
        for numero in range(1, 101):
            etiqueta_propuesta = f"Dirección {numero}"

            if etiqueta_propuesta not in etiquetas_existentes:
                logger.info(
                    f"✅ Etiqueta disponible encontrada: '{etiqueta_propuesta}'"
                )
                return etiqueta_propuesta

        # Fallback: usar timestamp si no se encontró número libre (muy improbable)
        from django.utils import timezone

        timestamp = timezone.now().strftime("%d%m_%H%M%S")
        etiqueta_fallback = f"Dirección {timestamp}"

        logger.warning(f"⚠️ Usando fallback timestamp: '{etiqueta_fallback}'")
        return etiqueta_fallback

    @transaction.atomic
    def create(self, validated_data):
        """Creación con transacción atómica"""
        user = self.context["request"].user

        # Si es predeterminada, desmarcar las demás
        if validated_data.get("es_predeterminada"):
            user.direcciones_favoritas.filter(activa=True).update(
                es_predeterminada=False
            )

        direccion = DireccionFavorita.objects.create(user=user, **validated_data)

        logger.info(
            f"✅ Dirección creada: {user.email} - '{direccion.etiqueta}' - "
            f"({direccion.latitud}, {direccion.longitud})"
        )

        return direccion


class ActualizarDireccionSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar direcciones existentes
    ✅ MEJORADO: Etiqueta opcional en actualización
    """

    # ✅ Etiqueta OPCIONAL también en actualización
    etiqueta = serializers.CharField(required=False, allow_blank=True, max_length=50)

    class Meta:
        model = DireccionFavorita
        fields = [
            "tipo",
            "etiqueta",
            "direccion",
            "referencia",
            "latitud",
            "longitud",
            "ciudad",
            "es_predeterminada",
            "activa",
        ]

    def validate_etiqueta(self, value):
        """
        ✅ Validación solo si viene etiqueta nueva
        Si no viene o viene vacía, se mantiene la existente
        """
        # Si no viene o viene vacía, retornar None (se mantendrá la existente)
        if not value or not value.strip():
            return None

        value = value.strip()

        if len(value) < 2:
            raise serializers.ValidationError(
                "La etiqueta debe tener al menos 2 caracteres"
            )

        if len(value) > 50:
            raise serializers.ValidationError(
                "La etiqueta no puede exceder 50 caracteres"
            )

        user = self.context["request"].user
        instance = self.instance

        # Validar duplicados solo si es una etiqueta diferente
        if (
            DireccionFavorita.objects.filter(
                user=user, etiqueta__iexact=value, activa=True
            )
            .exclude(pk=instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                f"Ya tienes una dirección con la etiqueta '{value}'."
            )

        return value

    def validate(self, data):
        """
        ✅ Si no viene etiqueta o viene vacía, mantener la existente
        """
        # Si viene etiqueta vacía, mantener la existente
        if "etiqueta" in data:
            etiqueta = data.get("etiqueta")

            if not etiqueta or not str(etiqueta).strip():
                # Mantener la existente
                data.pop("etiqueta", None)
                logger.info(
                    f"📝 Manteniendo etiqueta existente: '{self.instance.etiqueta}'"
                )

        return data

    def validate_direccion(self, value):
        """Validar dirección en actualización"""
        if not value or not value.strip():
            raise serializers.ValidationError("La dirección no puede estar vacía")

        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "La dirección debe tener al menos 10 caracteres"
            )

        return value

    def validate_latitud(self, value):
        """Valida que la latitud esté dentro de Ecuador"""
        if not (-5.0 <= value <= 2.0):
            raise serializers.ValidationError(
                "La latitud debe estar dentro del territorio ecuatoriano (-5° a 2°)"
            )
        return value

    def validate_longitud(self, value):
        """Valida que la longitud esté dentro de Ecuador"""
        if not (-92.0 <= value <= -75.0):
            raise serializers.ValidationError(
                "La longitud debe estar dentro del territorio ecuatoriano (-92° a -75°)"
            )
        return value


# ============================================
# SERIALIZERS PARA MÉTODOS DE PAGO
# ============================================


class MetodoPagoSerializer(serializers.ModelSerializer):
    """Serializer para métodos de pago"""

    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    tiene_comprobante = serializers.BooleanField(read_only=True)
    requiere_verificacion = serializers.BooleanField(read_only=True)
    comprobante_pago = serializers.SerializerMethodField()

    class Meta:
        model = MetodoPago
        fields = [
            "id",
            "tipo",
            "tipo_display",
            "alias",
            "comprobante_pago",
            "observaciones",
            "tiene_comprobante",
            "requiere_verificacion",
            "es_predeterminado",
            "activo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "tiene_comprobante",
            "requiere_verificacion",
            "created_at",
            "updated_at",
        ]

    def get_comprobante_pago(self, obj):
        """URL completa o null para comprobante"""
        if obj.comprobante_pago:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.comprobante_pago.url)
            return obj.comprobante_pago.url
        return None


class CrearMetodoPagoSerializer(serializers.ModelSerializer):
    """Serializer para crear métodos de pago"""

    class Meta:
        model = MetodoPago
        fields = [
            "tipo",
            "alias",
            "comprobante_pago",
            "observaciones",
            "es_predeterminado",
        ]

    def validate_alias(self, value):
        """Validación estricta del alias"""
        if not value or not value.strip():
            raise serializers.ValidationError(
                "El nombre del método de pago no puede estar vacío"
            )

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 3 caracteres"
            )

        if len(value) > 50:
            raise serializers.ValidationError(
                "El nombre no puede exceder 50 caracteres"
            )

        user = self.context["request"].user
        if MetodoPago.objects.filter(
            user=user, alias__iexact=value, activo=True
        ).exists():
            raise serializers.ValidationError(
                f"Ya tienes un método de pago con el nombre '{value}'."
            )

        return value

    def validate_observaciones(self, value):
        """Validación de observaciones"""
        if value:
            value = value.strip()

            if len(value) > 100:
                raise serializers.ValidationError(
                    f"Las observaciones no pueden exceder 100 caracteres (actual: {len(value)})"
                )

            if not value:
                return None

        return value

    def validate_comprobante_pago(self, value):
        """Validación robusta del comprobante"""
        if value:
            max_size = 5 * 1024 * 1024
            if value.size > max_size:
                tamano_mb = value.size / (1024 * 1024)
                raise serializers.ValidationError(
                    f"El comprobante no puede superar 5MB (actual: {tamano_mb:.1f}MB)"
                )

            valid_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Formato no válido. Use: {', '.join(valid_extensions)}"
                )

            valid_mime_types = [
                "image/jpeg",
                "image/png",
                "image/jpg",
                "application/pdf",
            ]
            if hasattr(value, "content_type"):
                if value.content_type and value.content_type not in valid_mime_types:
                    raise serializers.ValidationError(
                        f"Formato no válido. Use: {', '.join(valid_mime_types)}"
                    )

        return value

    def validate(self, data):
        """Validación estricta según tipo de pago"""
        tipo = data.get("tipo")
        comprobante = data.get("comprobante_pago")

        if tipo == "transferencia":
            if not comprobante:
                raise serializers.ValidationError(
                    {
                        "comprobante_pago": "El comprobante es obligatorio para transferencias",
                        "tipo": "Las transferencias requieren verificación mediante comprobante",
                    }
                )

        if tipo == "efectivo":
            if comprobante:
                raise serializers.ValidationError(
                    {
                        "comprobante_pago": "El pago en efectivo no requiere comprobante",
                        "tipo": "Elimina el comprobante para pagos en efectivo",
                    }
                )
            data["comprobante_pago"] = None

        if "alias" in data and not data["alias"].strip():
            raise serializers.ValidationError(
                {"alias": "El nombre del método de pago no puede estar vacío"}
            )

        return data

    @transaction.atomic
    def create(self, validated_data):
        """Creación con transacción atómica"""
        user = self.context["request"].user

        if validated_data.get("es_predeterminado"):
            user.metodos_pago.filter(activo=True).update(es_predeterminado=False)

        return MetodoPago.objects.create(user=user, **validated_data)


class ActualizarMetodoPagoSerializer(serializers.ModelSerializer):
    """Serializer para actualizar métodos de pago"""

    class Meta:
        model = MetodoPago
        fields = [
            "tipo",
            "alias",
            "comprobante_pago",
            "observaciones",
            "es_predeterminado",
        ]

    def validate_alias(self, value):
        """Validación de alias en actualización"""
        if not value or not value.strip():
            raise serializers.ValidationError("El nombre no puede estar vacío")

        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "El nombre debe tener al menos 3 caracteres"
            )

        if len(value) > 50:
            raise serializers.ValidationError(
                "El nombre no puede exceder 50 caracteres"
            )

        user = self.context["request"].user
        instance = self.instance

        if (
            MetodoPago.objects.filter(user=user, alias__iexact=value, activo=True)
            .exclude(pk=instance.pk)
            .exists()
        ):
            raise serializers.ValidationError(
                f"Ya tienes un método de pago con el nombre '{value}'."
            )

        return value

    def validate_observaciones(self, value):
        """Valida longitud de observaciones"""
        if value:
            value = value.strip()
            if len(value) > 100:
                raise serializers.ValidationError(
                    f"Las observaciones no pueden exceder 100 caracteres (actual: {len(value)})"
                )
            if not value:
                return None

        return value

    def validate_comprobante_pago(self, value):
        """Validación de comprobante en actualización"""
        if value:
            max_size = 5 * 1024 * 1024
            if value.size > max_size:
                tamano_mb = value.size / (1024 * 1024)
                raise serializers.ValidationError(
                    f"El comprobante no puede superar 5MB (actual: {tamano_mb:.1f}MB)"
                )

            valid_extensions = [".jpg", ".jpeg", ".png", ".pdf"]
            ext = os.path.splitext(value.name)[1].lower()
            if ext not in valid_extensions:
                raise serializers.ValidationError(
                    f"Formato no válido. Use: {', '.join(valid_extensions)}"
                )

            valid_mime_types = [
                "image/jpeg",
                "image/png",
                "image/jpg",
                "application/pdf",
            ]
            if (
                hasattr(value, "content_type")
                and value.content_type not in valid_mime_types
            ):
                raise serializers.ValidationError(
                    "El archivo debe ser una imagen (JPEG, PNG) o PDF válido"
                )

        return value

    def validate(self, data):
        """Validación estricta en actualización"""
        instance = self.instance
        tipo = data.get("tipo", instance.tipo)

        if "comprobante_pago" in data:
            comprobante = data["comprobante_pago"]
        else:
            comprobante = instance.comprobante_pago

        if tipo == "transferencia":
            if not comprobante:
                raise serializers.ValidationError(
                    {
                        "comprobante_pago": "Debes subir el comprobante de transferencia",
                        "tipo": "Las transferencias requieren verificación mediante comprobante",
                    }
                )

        if tipo == "efectivo":
            if comprobante:
                raise serializers.ValidationError(
                    {
                        "comprobante_pago": "El pago en efectivo no requiere comprobante",
                        "tipo": "Elimina el comprobante o cambia el tipo de pago",
                    }
                )
            data["comprobante_pago"] = None

        if "alias" in data and not data["alias"].strip():
            raise serializers.ValidationError(
                {"alias": "El nombre del método de pago no puede estar vacío"}
            )

        return data


# ============================================
# SERIALIZERS PARA ESTADÍSTICAS
# ============================================


class EstadisticasUsuarioSerializer(serializers.Serializer):
    """Serializer para mostrar estadísticas del usuario"""

    total_pedidos = serializers.IntegerField()
    pedidos_mes_actual = serializers.IntegerField()
    calificacion = serializers.FloatField()
    total_resenas = serializers.IntegerField()
    es_cliente_frecuente = serializers.BooleanField()
    puede_participar_rifa = serializers.BooleanField()
    total_direcciones = serializers.IntegerField()
    total_metodos_pago = serializers.IntegerField()


# ============================================
# SERIALIZERS PARA NOTIFICACIONES FCM
# ============================================


class FCMTokenSerializer(serializers.Serializer):
    """Serializer para registrar token FCM"""

    fcm_token = serializers.CharField(
        required=True,
        min_length=50,
        max_length=255,
        help_text="Token FCM del dispositivo",
    )

    def validate_fcm_token(self, value):
        """Validación robusta del token"""
        if not value or not value.strip():
            raise serializers.ValidationError("El token FCM no puede estar vacío")

        value = value.strip()

        if len(value) < 50:
            raise serializers.ValidationError(
                "El token FCM parece inválido (muy corto)"
            )

        if not re.match(r"^[A-Za-z0-9_\-:.]+$", value):
            raise serializers.ValidationError(
                "El token FCM contiene caracteres no válidos"
            )

        return value


class EstadoNotificacionesSerializer(serializers.Serializer):
    """Serializer para mostrar el estado de las notificaciones"""

    puede_recibir_notificaciones = serializers.BooleanField()
    notificaciones_pedido = serializers.BooleanField()
    notificaciones_promociones = serializers.BooleanField()
    token_actualizado = serializers.DateTimeField(allow_null=True)


# ============================================
# SERIALIZERS PARA ADMIN/REPARTIDOR
# ============================================


class ComprobanteVerificacionSerializer(serializers.Serializer):
    """Serializer para que admin/repartidor vea comprobantes"""

    id = serializers.UUIDField()
    usuario_email = serializers.EmailField(source="user.email")
    tipo = serializers.CharField()
    alias = serializers.CharField()
    comprobante_pago = serializers.SerializerMethodField()
    observaciones = serializers.CharField()
    created_at = serializers.DateTimeField()

    def get_comprobante_pago(self, obj):
        """URL completa del comprobante"""
        if hasattr(obj, "comprobante_pago") and obj.comprobante_pago:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(obj.comprobante_pago.url)
            return obj.comprobante_pago.url
        return None


# ============================================
# SERIALIZERS PARA UBICACIÓN (REST "lite")
# ============================================


class UbicacionUsuarioSerializer(serializers.ModelSerializer):
    """Serializer para ubicación del usuario"""

    usuario_email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = UbicacionUsuario
        fields = ["usuario_email", "latitud", "longitud", "actualizado_en"]


class ActualizarUbicacionSerializer(serializers.Serializer):
    """Serializer para actualizar ubicación del usuario"""

    latitud = serializers.FloatField()
    longitud = serializers.FloatField()

    def validate(self, data):
        """Validar coordenadas dentro de Ecuador"""
        lat, lon = data["latitud"], data["longitud"]

        if not (-5.0 <= lat <= 2.0):
            raise serializers.ValidationError(
                {"latitud": "Fuera de Ecuador (-5° a 2°)."}
            )

        if not (-92.0 <= lon <= -75.0):
            raise serializers.ValidationError(
                {"longitud": "Fuera de Ecuador (-92° a -75°)."}
            )

        return data


# ============================================
# SERIALIZERS PARA SOLICITUDES DE CAMBIO ROL
# ============================================


class SolicitudCambioRolListSerializer(serializers.ModelSerializer):
    """Serializer para listar solicitudes (usuario)"""

    rol_solicitado_display = serializers.CharField(
        source="get_rol_solicitado_display", read_only=True
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    usuario_email = serializers.EmailField(source="user.email", read_only=True)
    dias_pendiente = serializers.IntegerField(read_only=True)

    class Meta:
        from .models import SolicitudCambioRol

        model = SolicitudCambioRol
        fields = [
            "id",
            "usuario_email",
            "rol_solicitado",
            "rol_solicitado_display",
            "motivo",
            "estado",
            "estado_display",
            "creado_en",
            "respondido_en",
            "dias_pendiente",
            "motivo_respuesta",
        ]
        read_only_fields = [
            "id",
            "creado_en",
            "respondido_en",
            "dias_pendiente",
            "motivo_respuesta",
            "estado",
        ]


class CrearSolicitudCambioRolSerializer(serializers.Serializer):
    """Serializer para crear solicitud de cambio de rol"""

    rol_solicitado = serializers.ChoiceField(
        choices=["PROVEEDOR", "REPARTIDOR"], label="¿A qué rol deseas cambiar?"
    )
    motivo = serializers.CharField(
        max_length=500,
        min_length=10,
        label="¿Por qué deseas cambiar de rol?",
        help_text="Mínimo 10 caracteres",
    )

    def validate_motivo(self, value):
        """Validar que el motivo sea significativo"""
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "El motivo debe tener al menos 10 caracteres"
            )

        if len(value) > 500:
            raise serializers.ValidationError(
                "El motivo no puede exceder 500 caracteres"
            )

        return value

    def validate(self, data):
        """Validar que no tenga solicitud pendiente para ese rol"""
        from .models import SolicitudCambioRol

        user = self.context["request"].user
        rol_solicitado = data["rol_solicitado"]

        # Verificar si ya tiene ese rol
        if user.tiene_rol(rol_solicitado):
            raise serializers.ValidationError(
                {"rol_solicitado": f"Ya tienes el rol {rol_solicitado}"}
            )

        # Verificar si ya tiene solicitud pendiente
        solicitud_pendiente = SolicitudCambioRol.objects.filter(
            user=user, rol_solicitado=rol_solicitado, estado="PENDIENTE"
        ).exists()

        if solicitud_pendiente:
            raise serializers.ValidationError(
                {
                    "rol_solicitado": f"Ya tienes una solicitud pendiente para {rol_solicitado}"
                }
            )

        return data

    def create(self, validated_data):
        """Crear la solicitud"""
        from .models import SolicitudCambioRol

        user = self.context["request"].user

        solicitud = SolicitudCambioRol.objects.create(
            user=user,
            rol_solicitado=validated_data["rol_solicitado"],
            motivo=validated_data["motivo"],
        )

        logger.info(
            f"📝 Solicitud de cambio de rol creada: {user.email} → "
            f"{validated_data['rol_solicitado']}"
        )

        return solicitud


class SolicitudCambioRolDetalleSerializer(serializers.ModelSerializer):
    """Serializer detallado para una solicitud"""

    rol_solicitado_display = serializers.CharField(
        source="get_rol_solicitado_display", read_only=True
    )
    estado_display = serializers.CharField(source="get_estado_display", read_only=True)
    usuario_email = serializers.EmailField(source="user.email", read_only=True)
    usuario_nombre = serializers.CharField(source="user.get_full_name", read_only=True)
    admin_email = serializers.EmailField(
        source="admin_responsable.email", read_only=True, allow_null=True
    )
    dias_pendiente = serializers.IntegerField(read_only=True)

    class Meta:
        from .models import SolicitudCambioRol

        model = SolicitudCambioRol
        fields = [
            "id",
            "usuario_email",
            "usuario_nombre",
            "rol_solicitado",
            "rol_solicitado_display",
            "motivo",
            "estado",
            "estado_display",
            "creado_en",
            "respondido_en",
            "dias_pendiente",
            "admin_email",
            "motivo_respuesta",
        ]
        read_only_fields = fields


class ResponderSolicitudCambioRolSerializer(serializers.Serializer):
    """Serializer para que admin responda solicitud"""

    aceptada = serializers.BooleanField(label="¿Aceptar solicitud?")
    motivo_respuesta = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        label="Motivo de la respuesta (opcional)",
        help_text="Explicación al usuario",
    )

    def validate_motivo_respuesta(self, value):
        """Validar motivo si se proporciona"""
        if value:
            value = value.strip()

            if len(value) > 500:
                raise serializers.ValidationError(
                    "El motivo no puede exceder 500 caracteres"
                )

        return value

    def validate(self, data):
        """Validaciones adicionales"""
        aceptada = data.get("aceptada")
        motivo = data.get("motivo_respuesta", "").strip()

        # Si se rechaza, el motivo es altamente recomendado
        if not aceptada and not motivo:
            raise serializers.ValidationError(
                {
                    "motivo_respuesta": "Se recomienda proporcionar un motivo cuando se rechaza"
                }
            )

        return data


"""
SERIALIZERS PARA SOLICITUDES CON DATOS ESPECÍFICOS
===================================================

Agregar estas clases al final de usuarios/serializers.py existente
Reemplazan a CrearSolicitudCambioRolSerializer (línea 973)
"""

from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
import logging

logger = logging.getLogger("usuarios")


# ============================================
# SERIALIZER PARA SOLICITUD DE PROVEEDOR
# ============================================


class CrearSolicitudProveedorSerializer(serializers.Serializer):
    """
    ✅ FORMULARIO PARA PROVEEDOR

    Campos requeridos:
    - ruc (13 dígitos exactos)
    - nombre_comercial (3-200 caracteres)
    - tipo_negocio (restaurante, farmacia, supermercado, tienda, otro)
    - descripcion_negocio (10-500 caracteres)
    - motivo (10-500 caracteres)

    Opcionales:
    - horario_apertura (HH:MM)
    - horario_cierre (HH:MM)
    """

    # ==================== REQUERIDOS ====================

    ruc = serializers.CharField(
        max_length=13,
        min_length=13,
        required=True,
        trim_whitespace=True,
        help_text="RUC de 13 dígitos",
    )

    nombre_comercial = serializers.CharField(
        max_length=200,
        min_length=3,
        required=True,
        trim_whitespace=True,
        help_text="Nombre del negocio o razón social",
    )

    tipo_negocio = serializers.ChoiceField(
        choices=["restaurante", "farmacia", "supermercado", "tienda", "otro"],
        required=True,
        help_text="Categoría de tu negocio",
    )

    descripcion_negocio = serializers.CharField(
        max_length=500,
        min_length=10,
        required=True,
        trim_whitespace=True,
        help_text="¿Qué vende tu negocio? (10-500 caracteres)",
    )

    motivo = serializers.CharField(
        max_length=500,
        min_length=10,
        required=True,
        trim_whitespace=True,
        help_text="¿Por qué quieres ser proveedor? (10-500 caracteres)",
    )

    # ==================== OPCIONALES ====================

    horario_apertura = serializers.TimeField(
        required=False,
        allow_null=True,
        format="%H:%M",
    )

    horario_cierre = serializers.TimeField(
        required=False,
        allow_null=True,
        format="%H:%M",
    )

    # ================================================
    # VALIDACIONES
    # ================================================

    def validate_ruc(self, value):
        """Valida RUC: 13 dígitos exactos"""
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError(
                "❌ RUC solo debe contener números (sin guiones)"
            )

        # Verificar que no exista en Proveedor
        try:
            from proveedores.models import Proveedor

            if Proveedor.objects.filter(ruc=value).exists():
                raise serializers.ValidationError("❌ Este RUC ya está registrado")
        except ImportError:
            pass

        return value

    def validate_nombre_comercial(self, value):
        """Valida que no sea spam"""
        value = value.strip()

        palabras_spam = ["prueba", "test", "abc"]
        if any(palabra in value.lower() for palabra in palabras_spam):
            raise serializers.ValidationError(
                "❌ Nombre parece inválido. Usa un nombre real"
            )

        return value

    def validate_descripcion_negocio(self, value):
        """Valida descripción"""
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "❌ Descripción muy corta (mín. 10 caracteres)"
            )

        return value

    def validate_motivo(self, value):
        """Valida motivo"""
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "❌ Motivo muy corto (mín. 10 caracteres)"
            )

        return value

    def validate(self, data):
        """Validaciones transversales"""
        # Verificar que no tenga solicitud pendiente
        from .models import SolicitudCambioRol

        user = self.context["request"].user

        solicitud_pendiente = SolicitudCambioRol.objects.filter(
            user=user, rol_solicitado="PROVEEDOR", estado="PENDIENTE"
        ).exists()

        if solicitud_pendiente:
            raise serializers.ValidationError(
                {"rol_solicitado": "Ya tienes una solicitud PENDIENTE para PROVEEDOR"}
            )

        # Verificar que no tenga ya ese rol
        if user.tiene_rol("PROVEEDOR"):
            raise serializers.ValidationError({"rol_solicitado": "Ya eres PROVEEDOR"})

        return data

    def create(self, validated_data):
        """Crear solicitud con datos de proveedor"""
        from .models import SolicitudCambioRol

        user = self.context["request"].user

        solicitud = SolicitudCambioRol.objects.create(
            user=user,
            rol_solicitado="PROVEEDOR",
            motivo=validated_data["motivo"],
            # Datos específicos del proveedor
            ruc=validated_data["ruc"],
            nombre_comercial=validated_data["nombre_comercial"],
            tipo_negocio=validated_data["tipo_negocio"],
            descripcion_negocio=validated_data["descripcion_negocio"],
            horario_apertura=validated_data.get("horario_apertura"),
            horario_cierre=validated_data.get("horario_cierre"),
        )

        logger.info(
            f"📝 Solicitud PROVEEDOR creada: {user.email} - RUC:{validated_data['ruc']}"
        )

        return solicitud


# ============================================
# SERIALIZER PARA SOLICITUD DE REPARTIDOR
# ============================================


class CrearSolicitudRepartidorSerializer(serializers.Serializer):
    """
    ✅ FORMULARIO PARA REPARTIDOR

    Campos requeridos:
    - cedula_identidad (10-20 dígitos)
    - tipo_vehiculo (bicicleta, moto, auto, camion, otro)
    - zona_cobertura (3-200 caracteres)
    - motivo (10-500 caracteres)

    Opcionales:
    - disponibilidad (JSON con horarios)
    """

    # ==================== REQUERIDOS ====================

    cedula_identidad = serializers.CharField(
        max_length=20,
        min_length=10,
        required=True,
        trim_whitespace=True,
        help_text="Cédula de identidad (10-20 dígitos)",
    )

    tipo_vehiculo = serializers.ChoiceField(
        choices=["bicicleta", "moto", "auto", "camion", "otro"],
        required=True,
        help_text="Tipo de vehículo para repartir",
    )

    zona_cobertura = serializers.CharField(
        max_length=200,
        min_length=3,
        required=True,
        trim_whitespace=True,
        help_text="Zonas donde puedes repartir (ej: Centro, Sur)",
    )

    motivo = serializers.CharField(
        max_length=500,
        min_length=10,
        required=True,
        trim_whitespace=True,
        help_text="¿Por qué quieres ser repartidor? (10-500 caracteres)",
    )

    # ==================== OPCIONALES ====================

    disponibilidad = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text="Horarios de disponibilidad por día (JSON)",
    )

    # ================================================
    # VALIDACIONES
    # ================================================

    def validate_cedula_identidad(self, value):
        """Valida cédula: 10-20 dígitos"""
        value = value.strip()

        if not value.isdigit():
            raise serializers.ValidationError("❌ Cédula solo debe contener números")

        if len(value) < 10 or len(value) > 20:
            raise serializers.ValidationError("❌ Cédula debe tener 10-20 dígitos")

        return value

    def validate_zona_cobertura(self, value):
        """Valida zona"""
        value = value.strip()

        if len(value) < 3:
            raise serializers.ValidationError(
                "❌ Zona de cobertura muy corta (mín. 3 caracteres)"
            )

        return value

    def validate_motivo(self, value):
        """Valida motivo"""
        value = value.strip()

        if len(value) < 10:
            raise serializers.ValidationError(
                "❌ Motivo muy corto (mín. 10 caracteres)"
            )

        return value

    def validate_disponibilidad(self, value):
        """Valida estructura JSON de disponibilidad"""
        if value and not isinstance(value, dict):
            raise serializers.ValidationError(
                "❌ Disponibilidad debe ser un objeto JSON"
            )

        return value or {}

    def validate(self, data):
        """Validaciones transversales"""
        from .models import SolicitudCambioRol

        user = self.context["request"].user

        # Verificar que no tenga solicitud pendiente
        solicitud_pendiente = SolicitudCambioRol.objects.filter(
            user=user, rol_solicitado="REPARTIDOR", estado="PENDIENTE"
        ).exists()

        if solicitud_pendiente:
            raise serializers.ValidationError(
                {"rol_solicitado": "Ya tienes una solicitud PENDIENTE para REPARTIDOR"}
            )

        # Verificar que no tenga ya ese rol
        if user.tiene_rol("REPARTIDOR"):
            raise serializers.ValidationError({"rol_solicitado": "Ya eres REPARTIDOR"})

        return data

    def create(self, validated_data):
        """Crear solicitud con datos de repartidor"""
        from .models import SolicitudCambioRol

        user = self.context["request"].user

        solicitud = SolicitudCambioRol.objects.create(
            user=user,
            rol_solicitado="REPARTIDOR",
            motivo=validated_data["motivo"],
            # Datos específicos del repartidor
            cedula_identidad=validated_data["cedula_identidad"],
            tipo_vehiculo=validated_data["tipo_vehiculo"],
            zona_cobertura=validated_data["zona_cobertura"],
            disponibilidad=validated_data.get("disponibilidad", {}),
        )

        logger.info(
            f"📝 Solicitud REPARTIDOR creada: {user.email} - Cédula:{validated_data['cedula_identidad']}"
        )

        return solicitud
