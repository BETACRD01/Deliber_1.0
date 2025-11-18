# -*- coding: utf-8 -*-
# authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.utils import timezone
from .models import User
import logging

logger = logging.getLogger('authentication')

# ==========================================
# SERIALIZER DE USUARIO - RESPUESTAS
# ==========================================
class UserSerializer(serializers.ModelSerializer):
    """
    Serializer para retornar datos básicos del usuario
    Usado en respuestas de login, registro y perfil
    """
    edad = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'celular', 'fecha_nacimiento', 'edad', 'created_at',
            # Administración
            'is_superuser', 'is_staff', 'is_active', 'rol',
            # Términos
            'terminos_aceptados', 'terminos_fecha_aceptacion', 'terminos_version_aceptada',
            # Notificaciones
            'notificaciones_email', 'notificaciones_marketing', 'notificaciones_push',
            # Estado de cuenta
            'cuenta_desactivada', 'fecha_desactivacion',
        ]
        read_only_fields = [
            'id', 'created_at', 'edad',
            'terminos_fecha_aceptacion', 'terminos_ip_aceptacion',
            'fecha_desactivacion',
        ]

    def get_edad(self, obj):
        """Calcula la edad del usuario"""
        return obj.get_edad()


# ==========================================
# SERIALIZER DE REGISTRO
# ==========================================

class RegistroSerializer(serializers.ModelSerializer):
    """
    Serializer para el registro de nuevos usuarios
    Valida todos los campos requeridos y opcionales
    """
    password2 = serializers.CharField(
        write_only=True,
        label="Repetir contraseña",
        style={'input_type': 'password'}
    )
    terminos_aceptados = serializers.BooleanField(
        help_text="Debes aceptar los términos y condiciones"
    )

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'celular', 'fecha_nacimiento', 'password', 'password2',
            'terminos_aceptados',
            'notificaciones_email', 'notificaciones_marketing', 'notificaciones_push',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'style': {'input_type': 'password'}},
            'first_name': {'required': True},
            'last_name': {'required': True},
            'username': {'required': True},
            'email': {'required': True},
            'celular': {'required': True},
        }

    def validate_email(self, value):
        """Validar que el email no esté registrado"""
        if User.objects.filter(email=value.lower()).exists():
            raise serializers.ValidationError("Este correo electrónico ya está registrado")
        return value.lower()

    def validate_username(self, value):
        """Validar que el username no esté registrado"""
        if User.objects.filter(username=value.lower()).exists():
            raise serializers.ValidationError("Este nombre de usuario ya está en uso")
        return value.lower()

    def validate_celular(self, value):
        """Validar que el celular no esté registrado"""
        if User.objects.filter(celular=value).exists():
            raise serializers.ValidationError("Este número de celular ya está registrado")
        return value

    def validate(self, data):
        """Validaciones combinadas"""
        # Validar que las contraseñas coincidan
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                "password2": "Las contraseñas no coinciden"
            })

        # Validar contraseña segura
        try:
            User.validar_password(data['password'])
        except Exception as e:
            raise serializers.ValidationError({
                "password": str(e)
            })

        # Validar términos
        if not data.get('terminos_aceptados'):
            raise serializers.ValidationError({
                "terminos_aceptados": "Debes aceptar los términos y condiciones"
            })

        return data

    def create(self, validated_data):
        """Crea el usuario con los datos validados"""
        validated_data.pop('password2')

        # Información de términos
        validated_data['terminos_aceptados'] = True
        validated_data['terminos_fecha_aceptacion'] = timezone.now()
        validated_data['terminos_version_aceptada'] = '1.0'

        # Obtener IP del request
        request = self.context.get('request')
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
            else:
                ip = request.META.get('REMOTE_ADDR')
            validated_data['terminos_ip_aceptacion'] = ip

        # Crear usuario
        user = User.objects.create_user(**validated_data)
        logger.info(f"✅ Usuario registrado: {user.email}")
        return user


# ==========================================
# SERIALIZER DE LOGIN
# ==========================================

class LoginSerializer(serializers.Serializer):
    """
    Serializer para login con email/username y contraseña
    Maneja la autenticación y validación de cuenta
    """
    identificador = serializers.CharField(
        label="Email o Usuario",
        help_text="Ingresa tu email o nombre de usuario"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Contraseña"
    )

    def validate(self, data):
        """Valida credenciales y estado de cuenta"""
        identificador = data.get('identificador', '').strip().lower()
        password = data.get('password')

        if not identificador or not password:
            raise serializers.ValidationError("Email/Usuario y contraseña son requeridos")

        # Buscar usuario por email o username
        user = None
        try:
            if '@' in identificador:
                user = User.objects.get(email=identificador)
            else:
                user = User.objects.get(username=identificador)
        except User.DoesNotExist:
            raise serializers.ValidationError("Credenciales inválidas")

        # Verificar si la cuenta está bloqueada
        if user.esta_bloqueado():
            tiempo_restante = (user.cuenta_bloqueada_hasta - timezone.now()).seconds // 60
            raise serializers.ValidationError(
                f"Cuenta bloqueada por múltiples intentos fallidos. Intenta en {tiempo_restante} minutos"
            )

        # Verificar si la cuenta está desactivada
        if user.cuenta_desactivada:
            raise serializers.ValidationError(
                "Esta cuenta ha sido desactivada. Contacta con soporte si necesitas reactivarla"
            )

        # Autenticar
        authenticated_user = authenticate(username=user.email, password=password)

        if authenticated_user is not None:
            data['user'] = authenticated_user
        else:
            user.registrar_login_fallido()
            raise serializers.ValidationError("Credenciales inválidas")

        return data


# ==========================================
# SERIALIZER DE CAMBIO DE CONTRASEÑA
# ==========================================

class CambiarPasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña (usuario autenticado)
    Requiere contraseña actual y validación de la nueva
    """
    password_actual = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Contraseña actual"
    )
    password_nueva = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Nueva contraseña"
    )
    password_nueva2 = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Confirmar nueva contraseña"
    )

    def validate_password_actual(self, value):
        """Verificar que la contraseña actual sea correcta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta")
        return value

    def validate(self, data):
        """Validaciones combinadas"""
        # Validar que las nuevas contraseñas coincidan
        if data['password_nueva'] != data['password_nueva2']:
            raise serializers.ValidationError({
                "password_nueva2": "Las contraseñas no coinciden"
            })

        # Validar que sea diferente a la actual
        if data['password_actual'] == data['password_nueva']:
            raise serializers.ValidationError({
                "password_nueva": "La nueva contraseña debe ser diferente a la actual"
            })

        # Validar que sea segura
        try:
            User.validar_password(data['password_nueva'])
        except Exception as e:
            raise serializers.ValidationError({
                "password_nueva": str(e)
            })

        return data

    def save(self):
        """Guarda la nueva contraseña"""
        user = self.context['request'].user
        user.set_password(self.validated_data['password_nueva'])
        user.save()
        logger.info(f"✅ Contraseña cambiada: {user.email}")
        return user


# ==========================================
# SERIALIZER DE RECUPERACIÓN DE CONTRASEÑA
# ==========================================

class SolicitarCodigoRecuperacionSerializer(serializers.Serializer):
    """
    Serializer para solicitar código de recuperación de contraseña
    Genera un código de 6 dígitos hasheado
    """
    email = serializers.EmailField(label="Correo electrónico")

    def validate_email(self, value):
        """Validar que el email exista"""
        email_lower = value.lower()
        try:
            user = User.objects.get(email=email_lower)
            if user.cuenta_desactivada:
                raise serializers.ValidationError(
                    "Esta cuenta está desactivada. Contacta con soporte."
                )
            if not user.notificaciones_email:
                raise serializers.ValidationError(
                    "No podemos enviarte un correo porque has desactivado las notificaciones por email"
                )
        except User.DoesNotExist:
            # Por seguridad, no revelamos si el email existe
            pass

        return email_lower


class VerificarCodigoRecuperacionSerializer(serializers.Serializer):
    """
    Serializer para verificar código de 6 dígitos
    Valida el código hasheado almacenado
    """
    email = serializers.EmailField(label="Correo electrónico")
    codigo = serializers.CharField(
        max_length=6,
        min_length=6,
        label="Código de 6 dígitos"
    )

    def validate_codigo(self, value):
        """Validar que sea 6 dígitos"""
        if not value.isdigit():
            raise serializers.ValidationError("El código debe contener solo números")
        return value


class ResetPasswordConCodigoSerializer(serializers.Serializer):
    """
    Serializer para resetear contraseña con código de 6 dígitos
    Verifica el código y establece nueva contraseña
    """
    email = serializers.EmailField(label="Correo electrónico")
    codigo = serializers.CharField(
        max_length=6,
        min_length=6,
        label="Código de 6 dígitos"
    )
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Nueva contraseña"
    )
    password2 = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Confirmar contraseña"
    )

    def validate_codigo(self, value):
        """Validar que sea 6 dígitos"""
        if not value.isdigit():
            raise serializers.ValidationError("El código debe contener solo números")
        return value

    def validate(self, data):
        """Validaciones combinadas"""
        # Validar que las contraseñas coincidan
        if data['password'] != data['password2']:
            raise serializers.ValidationError({
                "password2": "Las contraseñas no coinciden"
            })

        # Validar que sea segura
        try:
            User.validar_password(data['password'])
        except Exception as e:
            raise serializers.ValidationError({
                "password": str(e)
            })

        return data


# ==========================================
# SERIALIZER DE ACTUALIZAR PERFIL
# ==========================================

class ActualizarPerfilSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar información básica del perfil
    Permite cambiar datos personales y preferencias
    """
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'celular', 'fecha_nacimiento',
            'notificaciones_email', 'notificaciones_marketing', 'notificaciones_push',
        ]


# ==========================================
# SERIALIZER DE PREFERENCIAS DE NOTIFICACIONES
# ==========================================

class PreferenciasNotificacionesSerializer(serializers.ModelSerializer):
    """
    Serializer para gestionar preferencias de notificaciones
    """
    class Meta:
        model = User
        fields = [
            'notificaciones_email',
            'notificaciones_marketing',
            'notificaciones_push',
        ]


# ==========================================
# SERIALIZER DE DESACTIVACIÓN DE CUENTA
# ==========================================

class DesactivarCuentaSerializer(serializers.Serializer):
    """
    Serializer para desactivar la cuenta del usuario
    Requiere confirmación con contraseña
    """
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        label="Confirma tu contraseña"
    )
    razon = serializers.CharField(
        required=False,
        allow_blank=True,
        label="Razón de desactivación (opcional)"
    )

    def validate_password(self, value):
        """Verificar que la contraseña sea correcta"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña incorrecta")
        return value

    def save(self):
        """Desactiva la cuenta"""
        user = self.context['request'].user
        razon = self.validated_data.get('razon', '')
        user.desactivar_cuenta(razon=razon)
        logger.info(f"✅ Cuenta desactivada: {user.email}")
        return user