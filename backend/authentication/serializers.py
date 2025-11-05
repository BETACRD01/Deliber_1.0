from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import secrets
from datetime import timedelta
from allauth.socialaccount.models import SocialAccount
from google.oauth2 import id_token
from google.auth.transport import requests

# ==========================================
# USUARIO (Para respuestas) - CON ROLES
# ==========================================
class UserSerializer(serializers.ModelSerializer):
    rol_display = serializers.CharField(source='get_rol_display', read_only=True)
    es_administrador = serializers.BooleanField(read_only=True)
    es_repartidor = serializers.BooleanField(read_only=True)
    es_proveedor = serializers.BooleanField(read_only=True)
    es_usuario = serializers.BooleanField(read_only=True)
    edad = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'celular', 'fecha_nacimiento', 'created_at', 'edad',
            # Rol
            'rol', 'rol_display',
            # Métodos de verificación de rol
            'es_administrador', 'es_repartidor', 'es_proveedor', 'es_usuario',
            # Campos específicos de Proveedor
            'nombre_negocio', 'ruc', 'direccion_negocio', 'categoria_negocio', 'verificado',
            # Campos específicos de Repartidor
            'vehiculo', 'placa_vehiculo', 'licencia_conducir', 'disponible',
            # Términos
            'terminos_aceptados', 'terminos_fecha_aceptacion', 'terminos_version_aceptada',
            # Notificaciones
            'notificaciones_email', 'notificaciones_marketing',
            'notificaciones_pedidos', 'notificaciones_push',
            # Estado de cuenta
            'cuenta_desactivada', 'fecha_desactivacion',
            # Google
            'google_picture',
        ]
        read_only_fields = [
            'id', 'created_at', 'rol_display', 'edad',
            'terminos_fecha_aceptacion', 'terminos_ip_aceptacion',
            'fecha_desactivacion', 'verificado'
        ]

    def get_edad(self, obj):
        return obj.get_edad()


# ==========================================
# REGISTRO CON ROL Y AUDITORÍA DE TÉRMINOS
# ==========================================
# authentication/serializers.py - FRAGMENTO ACTUALIZADO
# Reemplaza el RegistroSerializer completo

class RegistroSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True, label="Repetir contraseña")
    rol = serializers.ChoiceField(
        choices=User.RolChoices.choices,
        default=User.RolChoices.USUARIO,
        help_text="Selecciona tu rol: USUARIO, REPARTIDOR, PROVEEDOR"
    )

    # ✅ CAMPOS ESPECÍFICOS PARA REPARTIDORES
    cedula = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=10,
        help_text="Requerido para repartidores (10 dígitos)"
    )
    telefono = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Teléfono del repartidor (opcional, usa celular por defecto)"
    )
    tipo_vehiculo = serializers.ChoiceField(
        choices=['motocicleta', 'bicicleta', 'automovil', 'camioneta', 'otro'],
        required=False,
        default='motocicleta',
        help_text="Tipo de vehículo del repartidor"
    )
    placa_vehiculo = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=15,
        help_text="Placa del vehículo (opcional)"
    )
    licencia_conducir = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=50,
        help_text="Número de licencia (opcional)"
    )

    # CAMPOS OPCIONALES PARA PROVEEDORES
    nombre_negocio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    ruc = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    direccion_negocio = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    categoria_negocio = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # Preferencias de notificaciones (opcionales)
    notificaciones_email = serializers.BooleanField(required=False, default=True)
    notificaciones_marketing = serializers.BooleanField(required=False, default=True)
    notificaciones_pedidos = serializers.BooleanField(required=False, default=True)
    notificaciones_push = serializers.BooleanField(required=False, default=True)

    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'celular', 'fecha_nacimiento', 'password', 'password2',
            'terminos_aceptados', 'rol',
            # ✅ Campos de repartidor
            'cedula', 'telefono', 'tipo_vehiculo', 'placa_vehiculo', 'licencia_conducir',
            # Campos de proveedor
            'nombre_negocio', 'ruc', 'direccion_negocio', 'categoria_negocio',
            # Preferencias de notificaciones
            'notificaciones_email', 'notificaciones_marketing',
            'notificaciones_pedidos', 'notificaciones_push',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
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

    def validate_ruc(self, value):
        """Validar que el RUC no esté registrado"""
        if value and User.objects.filter(ruc=value).exists():
            raise serializers.ValidationError("Este RUC ya está registrado")
        return value

    def validate_cedula(self, value):
        """✅ Validar formato de cédula ecuatoriana"""
        if value:
            if not value.isdigit():
                raise serializers.ValidationError("La cédula debe contener solo números")
            if len(value) != 10:
                raise serializers.ValidationError("La cédula debe tener 10 dígitos")

            # Validar que no esté registrada
            from repartidores.models import Repartidor
            if Repartidor.objects.filter(cedula=value).exists():
                raise serializers.ValidationError("Esta cédula ya está registrada")

        return value

    def validate(self, data):
        # Validar contraseñas
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden"})

        # Validar contraseña segura
        User.validar_password(data['password'])

        # Validar términos
        if not data.get('terminos_aceptados'):
            raise serializers.ValidationError({
                "terminos_aceptados": "Debes aceptar los términos y condiciones"
            })

        # ✅ Validar campos específicos para REPARTIDOR
        if data.get('rol') == User.RolChoices.REPARTIDOR:
            if not data.get('cedula'):
                raise serializers.ValidationError({
                    "cedula": "La cédula es requerida para repartidores"
                })

        # Validar campos específicos para PROVEEDOR
        if data.get('rol') == User.RolChoices.PROVEEDOR:
            if not data.get('nombre_negocio'):
                raise serializers.ValidationError({
                    "nombre_negocio": "El nombre del negocio es requerido para proveedores"
                })
            if not data.get('ruc'):
                raise serializers.ValidationError({
                    "ruc": "El RUC es requerido para proveedores"
                })

        return data

    def create(self, validated_data):
        """
        ⚠️ NOTA: La creación del User se hace en la vista (views.py)
        Este método NO se usa actualmente porque la lógica está en la vista.
        Se mantiene por compatibilidad con DRF.
        """
        validated_data.pop('password2')

        # Información de términos
        if validated_data.get('terminos_aceptados'):
            validated_data['terminos_fecha_aceptacion'] = timezone.now()
            validated_data['terminos_version_aceptada'] = '1.0'

            # Obtener IP del request
            request = self.context.get('request')
            if request:
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                validated_data['terminos_ip_aceptacion'] = ip

        user = User.objects.create_user(**validated_data)
        return user

# ==========================================
# LOGIN CON USERNAME Y PASSWORD
# ==========================================
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(label="Usuario o Email")
    password = serializers.CharField(
        write_only=True,
        style={'input_type': 'password'},
        label="Contraseña"
    )

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            raise serializers.ValidationError("Usuario y contraseña son requeridos")

        # Intentar obtener el usuario
        user_obj = None
        try:
            # Intentar con email
            user_obj = User.objects.get(email=username.lower())
        except User.DoesNotExist:
            try:
                # Intentar con username
                user_obj = User.objects.get(username=username.lower())
            except User.DoesNotExist:
                pass

        # Verificar si la cuenta está bloqueada
        if user_obj and user_obj.esta_bloqueado():
            raise serializers.ValidationError(
                "Tu cuenta está temporalmente bloqueada por múltiples intentos fallidos. "
                "Intenta nuevamente en 15 minutos."
            )

        # Intentar autenticar
        user = None
        if user_obj:
            user = authenticate(username=user_obj.username, password=password)

        # Si la autenticación falla, registrar intento fallido
        if not user and user_obj:
            user_obj.registrar_login_fallido()
            raise serializers.ValidationError("Credenciales incorrectas")

        if not user:
            raise serializers.ValidationError("Credenciales incorrectas")

        if not user.is_active:
            raise serializers.ValidationError("Esta cuenta está desactivada")

        if user.cuenta_desactivada:
            raise serializers.ValidationError(
                "Tu cuenta ha sido desactivada. Contacta con soporte para más información."
            )

        # Registrar login exitoso con IP
        request = self.context.get('request')
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

        user.registrar_login_exitoso(ip_address)

        data['user'] = user
        return data


# ==========================================
# LOGIN CON GOOGLE
# ==========================================
class GoogleLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField(
        write_only=True,
        help_text="Token de acceso de Google obtenido desde Flutter"
    )

    def validate_access_token(self, value):
        """Valida el token de Google y obtiene la información del usuario"""
        try:
            # Verificar el token con Google
            idinfo = id_token.verify_oauth2_token(
                value,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID
            )

            # Verificar que el token es válido
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise serializers.ValidationError('Token inválido')

            return idinfo

        except ValueError:
            raise serializers.ValidationError('Token de Google inválido o expirado')

    def validate(self, data):
        idinfo = data['access_token']

        email = idinfo.get('email')
        if not email:
            raise serializers.ValidationError('No se pudo obtener el email de Google')

        # Verificar si el usuario ya existe
        try:
            user = User.objects.get(email=email)

            # Verificar estado de la cuenta
            if not user.is_active:
                raise serializers.ValidationError("Esta cuenta está desactivada")

            if user.cuenta_desactivada:
                raise serializers.ValidationError(
                    "Tu cuenta ha sido desactivada. Contacta con soporte."
                )

            # Actualizar foto de perfil si cambió
            picture_url = idinfo.get('picture')
            if picture_url and user.google_picture != picture_url:
                user.google_picture = picture_url
                user.save(update_fields=['google_picture'])

        except User.DoesNotExist:
            # Crear nuevo usuario con datos de Google
            user = User.objects.create_user(
                email=email,
                username=email.split('@')[0] + '_' + secrets.token_hex(4),
                first_name=idinfo.get('given_name', ''),
                last_name=idinfo.get('family_name', ''),
                celular='',  # Se pedirá completar después
                google_picture=idinfo.get('picture', ''),
                terminos_aceptados=True,
                terminos_fecha_aceptacion=timezone.now(),
                terminos_version_aceptada='1.0',
            )

            # Crear SocialAccount para vincular con Google
            SocialAccount.objects.create(
                user=user,
                provider='google',
                uid=idinfo.get('sub'),
                extra_data=idinfo
            )

        # Registrar login exitoso
        request = self.context.get('request')
        ip_address = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')

        user.registrar_login_exitoso(ip_address)

        data['user'] = user
        return data


# ==========================================
# ACTUALIZAR PERFIL
# ==========================================
class ActualizarPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'celular', 'fecha_nacimiento',
            # Campos de proveedor (solo si es proveedor)
            'nombre_negocio', 'direccion_negocio', 'categoria_negocio',
            # Campos de repartidor (solo si es repartidor)
            'vehiculo', 'placa_vehiculo', 'licencia_conducir', 'disponible',
        ]

    def validate(self, data):
        user = self.context['request'].user

        # Validar campos específicos según rol
        if user.es_proveedor():
            if 'nombre_negocio' in data and not data['nombre_negocio']:
                raise serializers.ValidationError({
                    'nombre_negocio': 'El nombre del negocio no puede estar vacío'
                })

        if user.es_repartidor():
            if 'vehiculo' in data and not data['vehiculo']:
                raise serializers.ValidationError({
                    'vehiculo': 'El vehículo no puede estar vacío'
                })

        return data

    def update(self, instance, validated_data):
        # Solo permitir actualizar ciertos campos según el rol
        if not instance.es_proveedor():
            validated_data.pop('nombre_negocio', None)
            validated_data.pop('direccion_negocio', None)
            validated_data.pop('categoria_negocio', None)

        if not instance.es_repartidor():
            validated_data.pop('vehiculo', None)
            validated_data.pop('placa_vehiculo', None)
            validated_data.pop('licencia_conducir', None)
            validated_data.pop('disponible', None)

        return super().update(instance, validated_data)


# ==========================================
# CAMBIAR CONTRASEÑA (ESTANDO AUTENTICADO)
# ==========================================
class CambiarPasswordSerializer(serializers.Serializer):
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
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta")
        return value

    def validate(self, data):
        # Validar que las contraseñas nuevas coincidan
        if data['password_nueva'] != data['password_nueva2']:
            raise serializers.ValidationError({
                "password_nueva2": "Las contraseñas no coinciden"
            })

        # Validar que la nueva contraseña sea diferente
        if data['password_actual'] == data['password_nueva']:
            raise serializers.ValidationError({
                "password_nueva": "La nueva contraseña debe ser diferente a la actual"
            })

        # Validar contraseña segura
        User.validar_password(data['password_nueva'])

        return data

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['password_nueva'])
        user.save()
        return user


# ==========================================
# ACTUALIZAR PREFERENCIAS DE NOTIFICACIONES
# ==========================================
class PreferenciasNotificacionesSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'notificaciones_email',
            'notificaciones_marketing',
            'notificaciones_pedidos',
            'notificaciones_push',
        ]


# ==========================================
# DESACTIVAR CUENTA
# ==========================================
class DesactivarCuentaSerializer(serializers.Serializer):
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
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña incorrecta")
        return value

    def save(self):
        user = self.context['request'].user
        razon = self.validated_data.get('razon', '')
        user.desactivar_cuenta(razon=razon)
        return user


# ==========================================
# RECUPERACIÓN DE CONTRASEÑA
# ==========================================
class SolicitarResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField(label="Correo electrónico")

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value.lower())
            if user.cuenta_desactivada:
                raise serializers.ValidationError(
                    "Esta cuenta está desactivada. No se puede recuperar la contraseña."
                )
        except User.DoesNotExist:
            raise serializers.ValidationError("No existe una cuenta con este correo electrónico")
        return value.lower()

    def save(self):
        email = self.validated_data['email']
        user = User.objects.get(email=email)

        # Verificar si puede recibir emails
        if not user.notificaciones_email:
            raise serializers.ValidationError(
                "No podemos enviarte un correo porque has desactivado las notificaciones por email"
            )

        # Generar token único
        token = secrets.token_urlsafe(32)
        user.reset_password_token = token
        user.reset_password_expire = timezone.now() + timedelta(hours=1)
        user.save()

        # Construir URL desde settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
        reset_url = f"{frontend_url}/reset-password/{token}/"

        # Enviar email
        send_mail(
            subject='Recuperación de contraseña - JP Express',
            message=f'''
Hola {user.get_full_name()},

Recibimos una solicitud para restablecer tu contraseña.

Haz clic en el siguiente enlace para crear una nueva contraseña:
{reset_url}

Este enlace expira en 1 hora.

Si no solicitaste este cambio, ignora este correo.

Saludos,
Equipo JP Express
            ''',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user


class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
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

    def validate(self, data):
        # Validar que las contraseñas coincidan
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Las contraseñas no coinciden"})

        # Validar contraseña segura
        User.validar_password(data['password'])

        # Validar token
        try:
            user = User.objects.get(reset_password_token=data['token'])

            # Verificar que no haya expirado (usando timezone.now())
            if user.reset_password_expire < timezone.now():
                raise serializers.ValidationError({"token": "El token ha expirado"})

            data['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError({"token": "Token inválido"})

        return data

    def save(self):
        user = self.validated_data['user']
        user.set_password(self.validated_data['password'])
        user.reset_password_token = None
        user.reset_password_expire = None
        user.save()
        return user
