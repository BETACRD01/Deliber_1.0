# chat/views.py
"""
APIs REST para el sistema de chat

✅ ENDPOINTS:
- GET /chats/ - Listar chats del usuario
- GET /chats/{id}/ - Detalle de un chat
- POST /chats/soporte/ - Crear chat de soporte
- GET /chats/{id}/mensajes/ - Listar mensajes de un chat
- POST /chats/{id}/mensajes/ - Enviar mensaje
- POST /chats/{id}/marcar-leidos/ - Marcar mensajes como leídos
- POST /chats/{id}/escribiendo/ - Indicar que está escribiendo
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404
from django.db.models import Q, Prefetch
from .models import Chat, Mensaje, TipoChat
from .serializers import (
    ChatSerializer,
    ChatListSerializer,
    MensajeSerializer,
    MensajeCreateSerializer,
    ChatSoporteCreateSerializer
)
from .utils import enviar_notificacion_nuevo_mensaje
import logging

logger = logging.getLogger('chat')


# ============================================
# VIEWSET: CHAT
# ============================================

class ChatViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para gestionar chats

    ✅ FUNCIONALIDADES:
    - Listar chats del usuario autenticado
    - Ver detalle de un chat
    - Crear chat de soporte (proveedores)
    - Marcar mensajes como leídos
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retorna chats donde el usuario es participante

        Admin puede ver todos los chats
        """
        user = self.request.user

        # Admin puede ver todos
        if user.es_admin():
            return Chat.objects.all().prefetch_related(
                'participantes',
                Prefetch('mensajes', queryset=Mensaje.objects.filter(eliminado=False))
            ).select_related('pedido', 'proveedor')

        # Usuario normal: solo sus chats
        return Chat.objects.filter(
            participantes=user,
            activo=True
        ).prefetch_related(
            'participantes',
            Prefetch('mensajes', queryset=Mensaje.objects.filter(eliminado=False))
        ).select_related('pedido', 'proveedor').distinct()

    def get_serializer_class(self):
        """Selecciona serializer según la acción"""
        if self.action == 'list':
            return ChatListSerializer
        elif self.action == 'crear_soporte':
            return ChatSoporteCreateSerializer
        return ChatSerializer

    def list(self, request, *args, **kwargs):
        """
        Lista chats del usuario ordenados por actividad reciente
        """
        queryset = self.get_queryset().order_by('-actualizado_en')

        # Filtro por tipo (opcional)
        tipo = request.query_params.get('tipo')
        if tipo and tipo in dict(TipoChat.choices).keys():
            queryset = queryset.filter(tipo=tipo)

        # Filtro por activo (opcional)
        activo = request.query_params.get('activo')
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')

        serializer = self.get_serializer(queryset, many=True)

        return Response({
            'success': True,
            'count': queryset.count(),
            'chats': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """Detalle de un chat específico"""
        chat = self.get_object()

        # Verificar permisos
        if not chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para ver este chat'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(chat)

        return Response({
            'success': True,
            'chat': serializer.data
        })

    @action(detail=False, methods=['post'], url_path='soporte')
    def crear_soporte(self, request):
        """
        Crea un chat de soporte (solo proveedores)

        Body:
        {
            "mensaje_inicial": "Necesito ayuda con..."
        }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        chat = serializer.save()

        # Serializar respuesta
        response_serializer = ChatSerializer(chat, context={'request': request})

        return Response({
            'success': True,
            'message': 'Chat de soporte creado exitosamente',
            'chat': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='mensajes')
    def listar_mensajes(self, request, pk=None):
        """
        Lista mensajes de un chat con paginación

        Query params:
        - limit: Cantidad de mensajes (default: 50)
        - offset: Saltar mensajes (default: 0)
        - antes_de: ID de mensaje para cargar anteriores
        """
        chat = self.get_object()

        # Verificar permisos
        if not chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para ver los mensajes de este chat'
            }, status=status.HTTP_403_FORBIDDEN)

        # Obtener mensajes
        mensajes = chat.mensajes.filter(eliminado=False).select_related('remitente')

        # Filtro: mensajes antes de un ID específico (para scroll infinito)
        antes_de = request.query_params.get('antes_de')
        if antes_de:
            try:
                mensaje_ref = Mensaje.objects.get(id=antes_de)
                mensajes = mensajes.filter(creado_en__lt=mensaje_ref.creado_en)
            except Mensaje.DoesNotExist:
                pass

        # Paginación
        limit = int(request.query_params.get('limit', 50))
        offset = int(request.query_params.get('offset', 0))

        # Ordenar (más recientes primero) y paginar
        mensajes = mensajes.order_by('-creado_en')[offset:offset+limit]

        # Invertir para mostrar en orden cronológico
        mensajes = list(reversed(mensajes))

        serializer = MensajeSerializer(
            mensajes,
            many=True,
            context={'request': request}
        )

        return Response({
            'success': True,
            'count': len(mensajes),
            'mensajes': serializer.data,
            'tiene_mas': chat.mensajes.filter(eliminado=False).count() > (offset + limit)
        })

    @action(detail=True, methods=['post'], url_path='mensajes')
    def enviar_mensaje(self, request, pk=None):
        """
        Envía un mensaje en el chat

        Soporta:
        - Texto: {"tipo": "texto", "contenido": "Hola"}
        - Imagen: {"tipo": "imagen", "archivo": <file>}
        - Audio: {"tipo": "audio", "archivo": <file>, "duracion_audio": 15}
        """
        chat = self.get_object()

        # Verificar permisos
        if not chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para enviar mensajes en este chat'
            }, status=status.HTTP_403_FORBIDDEN)

        # Verificar que el chat esté activo
        if not chat.activo:
            return Response({
                'success': False,
                'error': 'Este chat está cerrado'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Crear mensaje
        data = request.data.copy()
        data['chat'] = chat.id

        serializer = MensajeCreateSerializer(
            data=data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        mensaje = serializer.save()

        # Enviar notificación push al otro participante
        try:
            enviar_notificacion_nuevo_mensaje(mensaje, request.user)
        except Exception as e:
            logger.warning(f"⚠️ Error enviando notificación: {e}")

        # Serializar respuesta
        response_serializer = MensajeSerializer(
            mensaje,
            context={'request': request}
        )

        return Response({
            'success': True,
            'message': 'Mensaje enviado exitosamente',
            'mensaje': response_serializer.data
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='marcar-leidos')
    def marcar_leidos(self, request, pk=None):
        """
        Marca todos los mensajes del chat como leídos
        """
        chat = self.get_object()

        # Verificar permisos
        if not chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para realizar esta acción'
            }, status=status.HTTP_403_FORBIDDEN)

        # Marcar mensajes como leídos
        count = chat.marcar_todos_como_leidos(request.user)

        return Response({
            'success': True,
            'message': f'{count} mensajes marcados como leídos',
            'mensajes_marcados': count
        })

    @action(detail=True, methods=['post'], url_path='escribiendo')
    def indicar_escribiendo(self, request, pk=None):
        """
        Indica que el usuario está escribiendo (para indicador en tiempo real)

        Body:
        {
            "escribiendo": true
        }

        NOTA: Esto es para el frontend, no se guarda en BD.
        En producción se implementaría con WebSockets.
        """
        chat = self.get_object()

        # Verificar permisos
        if not chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para realizar esta acción'
            }, status=status.HTTP_403_FORBIDDEN)

        escribiendo = request.data.get('escribiendo', False)

        # TODO: Implementar con WebSockets/Channels para notificar en tiempo real
        # Por ahora solo retornamos OK

        return Response({
            'success': True,
            'escribiendo': escribiendo
        })

    @action(detail=True, methods=['post'], url_path='cerrar')
    def cerrar_chat(self, request, pk=None):
        """
        Cierra/archiva un chat (solo admin)
        """
        if not request.user.es_admin():
            return Response({
                'success': False,
                'error': 'Solo administradores pueden cerrar chats'
            }, status=status.HTTP_403_FORBIDDEN)

        chat = self.get_object()
        chat.cerrar_chat()

        return Response({
            'success': True,
            'message': 'Chat cerrado exitosamente'
        })


# ============================================
# VIEWSET: MENSAJE
# ============================================

class MensajeViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para mensajes individuales

    ✅ FUNCIONALIDADES:
    - Ver detalle de un mensaje
    - Marcar como leído
    - Eliminar (soft delete)
    """

    permission_classes = [IsAuthenticated]
    serializer_class = MensajeSerializer

    def get_queryset(self):
        """Retorna mensajes de chats donde el usuario participa"""
        user = self.request.user

        # Admin puede ver todos
        if user.es_admin():
            return Mensaje.objects.filter(eliminado=False).select_related(
                'chat', 'remitente'
            )

        # Usuario normal: solo mensajes de sus chats
        return Mensaje.objects.filter(
            chat__participantes=user,
            eliminado=False
        ).select_related('chat', 'remitente').distinct()

    def retrieve(self, request, *args, **kwargs):
        """Detalle de un mensaje"""
        mensaje = self.get_object()

        # Verificar permisos
        if not mensaje.chat.usuario_puede_participar(request.user):
            return Response({
                'success': False,
                'error': 'No tienes permiso para ver este mensaje'
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(mensaje)

        return Response({
            'success': True,
            'mensaje': serializer.data
        })

    @action(detail=True, methods=['post'], url_path='marcar-leido')
    def marcar_leido(self, request, pk=None):
        """Marca un mensaje específico como leído"""
        mensaje = self.get_object()

        # Solo si no es el remitente
        if mensaje.remitente != request.user:
            mensaje.marcar_como_leido()

            return Response({
                'success': True,
                'message': 'Mensaje marcado como leído'
            })

        return Response({
            'success': False,
            'error': 'No puedes marcar tu propio mensaje como leído'
        }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['delete'], url_path='eliminar')
    def eliminar_mensaje(self, request, pk=None):
        """Elimina un mensaje (soft delete)"""
        mensaje = self.get_object()

        # Solo el remitente o admin pueden eliminar
        if mensaje.remitente != request.user and not request.user.es_admin():
            return Response({
                'success': False,
                'error': 'Solo puedes eliminar tus propios mensajes'
            }, status=status.HTTP_403_FORBIDDEN)

        mensaje.eliminar_mensaje()

        return Response({
            'success': True,
            'message': 'Mensaje eliminado exitosamente'
        })
