# chat/serializers.py
"""
Serializers para el sistema de chat

✅ SERIALIZERS DISPONIBLES:
- ChatSerializer: Detalle completo de un chat
- ChatListSerializer: Lista resumida de chats
- MensajeSerializer: Detalle de un mensaje
- MensajeCreateSerializer: Crear nuevo mensaje
- ChatSoporteCreateSerializer: Crear chat de soporte
"""

from rest_framework import serializers
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Chat, Mensaje, TipoChat, TipoMensaje
from authentication.models import User
from proveedores.models import Proveedor
import logging

logger = logging.getLogger('chat')


# ============================================
# SERIALIZER: USER (NESTED)
# ============================================

class UserBasicSerializer(serializers.ModelSerializer):
    """Información básica del usuario para chats"""

    nombre_completo = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'first_name',
            'last_name',
            'nombre_completo',
            'rol',
            'avatar'
        ]
        read_only_fields = fields

    def get_nombre_completo(self, obj):
        """Retorna nombre completo o email"""
        return obj.get_full_name() or obj.email

    def get_avatar(self, obj):
        """URL del avatar si existe"""
        if hasattr(obj, 'perfil_usuario') and obj.perfil_usuario.foto_perfil:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.perfil_usuario.foto_perfil.url)
        return None


# ============================================
# SERIALIZER: PEDIDO (NESTED)
# ============================================

class PedidoBasicSerializer(serializers.Serializer):
    """Información básica del pedido para contexto del chat"""

    id = serializers.IntegerField()
    numero = serializers.CharField(source='numero_pedido', read_only=True)
    estado = serializers.CharField()
    direccion_entrega = serializers.CharField()
    total = serializers.DecimalField(max_digits=10, decimal_places=2)
    creado_en = serializers.DateTimeField()


# ============================================
# SERIALIZER: PROVEEDOR (NESTED)
# ============================================

class ProveedorBasicSerializer(serializers.Serializer):
    """Información básica del proveedor para chats de soporte"""

    id = serializers.IntegerField()
    nombre = serializers.CharField()
    telefono = serializers.CharField()
    direccion = serializers.CharField()


# ============================================
# SERIALIZER: MENSAJE
# ============================================

class MensajeSerializer(serializers.ModelSerializer):
    """
    Serializer completo para mensajes

    Incluye información del remitente y archivos adjuntos
    """

    remitente = UserBasicSerializer(read_only=True)
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)

    # Propiedades del modelo
    es_imagen = serializers.BooleanField(read_only=True)
    es_audio = serializers.BooleanField(read_only=True)
    es_sistema = serializers.BooleanField(read_only=True)
    url_archivo = serializers.SerializerMethodField()
    tamano_archivo_mb = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    # Estado del mensaje para el usuario actual
    es_propio = serializers.SerializerMethodField()

    class Meta:
        model = Mensaje
        fields = [
            'id',
            'chat',
            'remitente',
            'tipo',
            'tipo_display',
            'contenido',
            'archivo',
            'nombre_archivo',
            'tamano_archivo',
            'tamano_archivo_mb',
            'duracion_audio',
            'url_archivo',
            'es_imagen',
            'es_audio',
            'es_sistema',
            'leido',
            'leido_en',
            'eliminado',
            'es_propio',
            'creado_en',
            'actualizado_en'
        ]
        read_only_fields = [
            'id',
            'remitente',
            'tipo_display',
            'nombre_archivo',
            'tamano_archivo',
            'leido',
            'leido_en',
            'eliminado',
            'creado_en',
            'actualizado_en'
        ]

    def get_url_archivo(self, obj):
        """URL completa del archivo adjunto"""
        if obj.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.archivo.url)
            return obj.archivo.url
        return None

    def get_es_propio(self, obj):
        """Verifica si el mensaje es del usuario autenticado"""
        request = self.context.get('request')
        if request and request.user:
            return obj.remitente == request.user
        return False


# ============================================
# SERIALIZER: MENSAJE CREATE
# ============================================

class MensajeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer para crear mensajes

    Soporta texto, imagen y audio
    """

    class Meta:
        model = Mensaje
        fields = [
            'chat',
            'tipo',
            'contenido',
            'archivo',
            'duracion_audio'
        ]

    def validate(self, data):
        """Validaciones personalizadas"""
        tipo = data.get('tipo')
        contenido = data.get('contenido', '').strip()
        archivo = data.get('archivo')

        # Validar mensaje de texto
        if tipo == TipoMensaje.TEXTO:
            if not contenido:
                raise serializers.ValidationError({
                    'contenido': 'El mensaje de texto no puede estar vacío'
                })

        # Validar mensaje de imagen
        elif tipo == TipoMensaje.IMAGEN:
            if not archivo:
                raise serializers.ValidationError({
                    'archivo': 'Debes adjuntar una imagen'
                })

            # Validar extensión
            nombre_archivo = archivo.name if hasattr(archivo, 'name') else str(archivo)
            ext = nombre_archivo.split('.')[-1].lower()
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                raise serializers.ValidationError({
                    'archivo': f'Formato de imagen no válido: {ext}. Usa JPG, PNG o WEBP'
                })

        # Validar mensaje de audio
        elif tipo == TipoMensaje.AUDIO:
            if not archivo:
                raise serializers.ValidationError({
                    'archivo': 'Debes adjuntar un audio'
                })

            # Validar extensión
            nombre_archivo = archivo.name if hasattr(archivo, 'name') else str(archivo)
            ext = nombre_archivo.split('.')[-1].lower()
            if ext not in ['mp3', 'ogg', 'm4a', 'wav']:
                raise serializers.ValidationError({
                    'archivo': f'Formato de audio no válido: {ext}. Usa MP3, OGG, M4A o WAV'
                })

        return data

    def create(self, validated_data):
        """Crea el mensaje con el usuario autenticado como remitente"""
        request = self.context.get('request')

        # Asignar remitente
        validated_data['remitente'] = request.user

        try:
            mensaje = Mensaje.objects.create(**validated_data)

            logger.info(
                f"✅ Mensaje {mensaje.tipo} creado por {request.user.email} "
                f"en chat {mensaje.chat.id}"
            )

            return mensaje

        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict)


# ============================================
# SERIALIZER: CHAT LIST
# ============================================

class ChatListSerializer(serializers.ModelSerializer):
    """
    Serializer resumido para listar chats

    Incluye último mensaje y contador de no leídos
    """

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    participantes = UserBasicSerializer(many=True, read_only=True)

    # Información adicional
    ultimo_mensaje = serializers.SerializerMethodField()
    mensajes_no_leidos = serializers.SerializerMethodField()
    total_mensajes = serializers.IntegerField(read_only=True)

    # Relaciones opcionales
    pedido = PedidoBasicSerializer(read_only=True)
    proveedor = ProveedorBasicSerializer(read_only=True)

    class Meta:
        model = Chat
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'activo',
            'participantes',
            'pedido',
            'proveedor',
            'ultimo_mensaje',
            'mensajes_no_leidos',
            'total_mensajes',
            'creado_en',
            'actualizado_en'
        ]
        read_only_fields = fields

    def get_ultimo_mensaje(self, obj):
        """Retorna el último mensaje del chat"""
        ultimo = obj.obtener_ultimo_mensaje()

        if ultimo:
            return {
                'id': str(ultimo.id),
                'tipo': ultimo.tipo,
                'contenido': self._get_preview_contenido(ultimo),
                'remitente': {
                    'id': ultimo.remitente.id if ultimo.remitente else None,
                    'nombre': ultimo.remitente.get_full_name() if ultimo.remitente else 'Sistema'
                },
                'creado_en': ultimo.creado_en
            }

        return None

    def _get_preview_contenido(self, mensaje):
        """Genera preview del contenido según tipo"""
        if mensaje.tipo == TipoMensaje.TEXTO:
            # Limitar a 100 caracteres
            texto = mensaje.contenido[:100]
            if len(mensaje.contenido) > 100:
                texto += '...'
            return texto
        elif mensaje.tipo == TipoMensaje.IMAGEN:
            return '📷 Imagen'
        elif mensaje.tipo == TipoMensaje.AUDIO:
            if mensaje.duracion_audio:
                return f'🎤 Audio ({mensaje.duracion_audio}s)'
            return '🎤 Audio'
        return mensaje.contenido

    def get_mensajes_no_leidos(self, obj):
        """Cuenta mensajes no leídos para el usuario actual"""
        request = self.context.get('request')
        if request and request.user:
            return obj.contar_no_leidos(request.user)
        return 0


# ============================================
# SERIALIZER: CHAT DETAIL
# ============================================

class ChatSerializer(serializers.ModelSerializer):
    """
    Serializer completo para detalle de chat

    Incluye todos los participantes, pedido y estadísticas
    """

    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    participantes = UserBasicSerializer(many=True, read_only=True)

    # Relaciones
    pedido = PedidoBasicSerializer(read_only=True)
    proveedor = ProveedorBasicSerializer(read_only=True)

    # Estadísticas
    total_mensajes = serializers.IntegerField(read_only=True)
    tiene_mensajes_sin_leer = serializers.BooleanField(read_only=True)
    mensajes_no_leidos = serializers.SerializerMethodField()

    # Último mensaje
    ultimo_mensaje = serializers.SerializerMethodField()

    # Info adicional para el usuario
    puede_enviar_mensajes = serializers.SerializerMethodField()

    class Meta:
        model = Chat
        fields = [
            'id',
            'tipo',
            'tipo_display',
            'titulo',
            'activo',
            'participantes',
            'pedido',
            'proveedor',
            'total_mensajes',
            'tiene_mensajes_sin_leer',
            'mensajes_no_leidos',
            'ultimo_mensaje',
            'puede_enviar_mensajes',
            'creado_en',
            'actualizado_en',
            'cerrado_en'
        ]
        read_only_fields = fields

    def get_ultimo_mensaje(self, obj):
        """Serializa el último mensaje completo"""
        ultimo = obj.obtener_ultimo_mensaje()

        if ultimo:
            # Evitar importación circular - serializar manualmente
            return {
                'id': str(ultimo.id),
                'tipo': ultimo.tipo,
                'tipo_display': ultimo.get_tipo_display(),
                'contenido': self._get_preview_contenido(ultimo),
                'remitente': {
                    'id': ultimo.remitente.id if ultimo.remitente else None,
                    'nombre': ultimo.remitente.get_full_name() if ultimo.remitente else 'Sistema',
                    'email': ultimo.remitente.email if ultimo.remitente else None
                },
                'es_imagen': ultimo.es_imagen,
                'es_audio': ultimo.es_audio,
                'url_archivo': self._get_url_archivo_mensaje(ultimo),
                'duracion_audio': ultimo.duracion_audio,
                'leido': ultimo.leido,
                'creado_en': ultimo.creado_en
            }

        return None

    def _get_preview_contenido(self, mensaje):
        """Genera preview del contenido según tipo"""
        if mensaje.tipo == TipoMensaje.TEXTO:
            # Limitar a 100 caracteres
            texto = mensaje.contenido[:100]
            if len(mensaje.contenido) > 100:
                texto += '...'
            return texto
        elif mensaje.tipo == TipoMensaje.IMAGEN:
            return '📷 Imagen'
        elif mensaje.tipo == TipoMensaje.AUDIO:
            if mensaje.duracion_audio:
                return f'🎤 Audio ({mensaje.duracion_audio}s)'
            return '🎤 Audio'
        return mensaje.contenido

    def _get_url_archivo_mensaje(self, mensaje):
        """Obtiene URL del archivo del mensaje"""
        if mensaje.archivo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(mensaje.archivo.url)
            return mensaje.archivo.url
        return None

    def get_mensajes_no_leidos(self, obj):
        """Cuenta no leídos para el usuario actual"""
        request = self.context.get('request')
        if request and request.user:
            return obj.contar_no_leidos(request.user)
        return 0

    def get_puede_enviar_mensajes(self, obj):
        """Verifica si el usuario puede enviar mensajes"""
        request = self.context.get('request')
        if not request or not request.user:
            return False

        # El chat debe estar activo
        if not obj.activo:
            return False

        # El usuario debe ser participante
        return obj.usuario_puede_participar(request.user)


# ============================================
# SERIALIZER: CREAR CHAT DE SOPORTE
# ============================================

class ChatSoporteCreateSerializer(serializers.Serializer):
    """
    Serializer para crear chat de soporte

    Solo proveedores pueden crear chats de soporte
    """

    mensaje_inicial = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        help_text='Mensaje inicial opcional'
    )

    def validate(self, data):
        """Validar que el usuario sea proveedor"""
        request = self.context.get('request')

        if not request or not request.user:
            raise serializers.ValidationError('Usuario no autenticado')

        if not request.user.es_proveedor():
            raise serializers.ValidationError(
                'Solo proveedores pueden crear chats de soporte'
            )

        # Verificar que tenga proveedor asociado
        try:
            proveedor = request.user.proveedor
        except Proveedor.DoesNotExist:
            raise serializers.ValidationError(
                'No se encontró perfil de proveedor para este usuario'
            )

        data['proveedor'] = proveedor

        return data

    def create(self, validated_data):
        """Crea el chat de soporte"""
        proveedor = validated_data['proveedor']
        mensaje_inicial = validated_data.get('mensaje_inicial', '')

        try:
            # Crear chat de soporte
            chat = Chat.crear_chat_soporte(proveedor)

            # Si hay mensaje inicial, enviarlo
            if mensaje_inicial:
                Mensaje.objects.create(
                    chat=chat,
                    remitente=proveedor.user,
                    tipo=TipoMensaje.TEXTO,
                    contenido=mensaje_inicial
                )

                logger.info(
                    f"✅ Chat de soporte creado con mensaje inicial "
                    f"para proveedor {proveedor.id}"
                )
            else:
                logger.info(
                    f"✅ Chat de soporte creado para proveedor {proveedor.id}"
                )

            return chat

        except DjangoValidationError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            logger.error(f"❌ Error creando chat de soporte: {e}", exc_info=True)
            raise serializers.ValidationError(
                'Error al crear el chat de soporte. Intenta nuevamente.'
            )


# ============================================
# SERIALIZER: MARCAR MENSAJES COMO LEÍDOS
# ============================================

class MarcarLeidosSerializer(serializers.Serializer):
    """
    Serializer para marcar mensajes como leídos

    Puede recibir IDs específicos o marcar todos
    """

    mensaje_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        allow_empty=True,
        help_text='IDs de mensajes específicos (opcional)'
    )

    marcar_todos = serializers.BooleanField(
        default=True,
        help_text='Marcar todos los mensajes como leídos'
    )


# ============================================
# SERIALIZER: INDICADOR DE ESCRITURA
# ============================================

class EscribiendoSerializer(serializers.Serializer):
    """
    Serializer para indicador de escritura

    Para implementación futura con WebSockets
    """

    escribiendo = serializers.BooleanField(
        required=True,
        help_text='True si está escribiendo, False si dejó de escribir'
    )
