# chat/utils.py
"""
Utilidades para notificaciones push Firebase

✅ FUNCIONALIDADES:
- Enviar notificación cuando llega un mensaje nuevo
- Configuración Firebase Cloud Messaging
- Manejo de errores y tokens inválidos
"""

import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os

logger = logging.getLogger('chat')

# ============================================
# INICIALIZAR FIREBASE
# ============================================

def inicializar_firebase():
    """
    Inicializa Firebase Admin SDK si no está inicializado
    """
    if not firebase_admin._apps:
        try:
            # Buscar archivo de credenciales
            cred_path = getattr(
                settings,
                'FIREBASE_CREDENTIALS_PATH',
                'firebase-credentials.json'
            )

            if not os.path.exists(cred_path):
                # Intentar ruta alternativa
                cred_path = os.path.join(settings.BASE_DIR, cred_path)

            if not os.path.exists(cred_path):
                logger.warning(
                    f"⚠️ No se encontró el archivo de credenciales Firebase: {cred_path}"
                )
                return False

            # Inicializar
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)

            logger.info("✅ Firebase Admin SDK inicializado correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {e}", exc_info=True)
            return False

    return True


# ============================================
# ENVIAR NOTIFICACIÓN NUEVO MENSAJE
# ============================================

def enviar_notificacion_nuevo_mensaje(mensaje, remitente):
    """
    Envía notificación push cuando llega un mensaje nuevo

    Args:
        mensaje (Mensaje): Instancia del mensaje enviado
        remitente (User): Usuario que envió el mensaje
    """
    # Verificar que Firebase esté inicializado
    if not inicializar_firebase():
        logger.warning("⚠️ Firebase no está inicializado, no se enviará notificación")
        return

    try:
        # Obtener destinatarios (otros participantes del chat)
        destinatarios = mensaje.chat.participantes.exclude(id=remitente.id)

        for destinatario in destinatarios:
            try:
                # Verificar que tenga token FCM
                if not hasattr(destinatario, 'perfil_usuario'):
                    continue

                perfil = destinatario.perfil_usuario

                if not perfil.fcm_token:
                    logger.debug(
                        f"ℹ️ Usuario {destinatario.email} no tiene token FCM"
                    )
                    continue

                # Verificar preferencias de notificaciones
                if not perfil.puede_recibir_notificaciones:
                    logger.debug(
                        f"ℹ️ Usuario {destinatario.email} tiene notificaciones desactivadas"
                    )
                    continue

                # Construir mensaje de notificación
                titulo, cuerpo = _construir_mensaje_notificacion(mensaje, remitente)

                # Crear notificación
                notification = messaging.Notification(
                    title=titulo,
                    body=cuerpo
                )

                # Datos adicionales
                data = {
                    'tipo': 'nuevo_mensaje',
                    'chat_id': str(mensaje.chat.id),
                    'mensaje_id': str(mensaje.id),
                    'mensaje_tipo': mensaje.tipo,
                    'remitente_id': str(remitente.id),
                    'remitente_nombre': remitente.get_full_name()
                }

                # Mensaje completo
                message = messaging.Message(
                    notification=notification,
                    data=data,
                    token=perfil.fcm_token,
                    android=messaging.AndroidConfig(
                        priority='high',
                        notification=messaging.AndroidNotification(
                            sound='default',
                            channel_id='chat_mensajes'
                        )
                    ),
                    apns=messaging.APNSConfig(
                        payload=messaging.APNSPayload(
                            aps=messaging.Aps(
                                sound='default',
                                badge=1
                            )
                        )
                    )
                )

                # Enviar
                response = messaging.send(message)

                logger.info(
                    f"✅ Notificación enviada a {destinatario.email}. "
                    f"Response: {response}"
                )

            except messaging.UnregisteredError:
                # Token inválido, limpiar
                logger.warning(
                    f"⚠️ Token FCM inválido para {destinatario.email}, limpiando..."
                )
                perfil.eliminar_fcm_token()

            except Exception as e:
                logger.error(
                    f"❌ Error enviando notificación a {destinatario.email}: {e}",
                    exc_info=True
                )

    except Exception as e:
        logger.error(
            f"❌ Error en enviar_notificacion_nuevo_mensaje: {e}",
            exc_info=True
        )


def _construir_mensaje_notificacion(mensaje, remitente):
    """
    Construye título y cuerpo de la notificación

    Args:
        mensaje (Mensaje): Mensaje enviado
        remitente (User): Usuario remitente

    Returns:
        tuple: (titulo, cuerpo)
    """
    from .models import TipoMensaje

    nombre_remitente = remitente.get_full_name() or remitente.email

    # Título según tipo de chat
    if mensaje.chat.tipo == 'pedido_cliente':
        titulo = f"Mensaje del repartidor"
    elif mensaje.chat.tipo == 'pedido_proveedor':
        if remitente.es_proveedor():
            titulo = "Mensaje del proveedor"
        else:
            titulo = "Mensaje del repartidor"
    elif mensaje.chat.tipo == 'soporte':
        if remitente.es_admin():
            titulo = "Respuesta de soporte"
        else:
            titulo = "Mensaje de soporte"
    else:
        titulo = f"Mensaje de {nombre_remitente}"

    # Cuerpo según tipo de mensaje
    if mensaje.tipo == TipoMensaje.TEXTO:
        # Limitar a 100 caracteres
        cuerpo = mensaje.contenido[:100]
        if len(mensaje.contenido) > 100:
            cuerpo += "..."
    elif mensaje.tipo == TipoMensaje.IMAGEN:
        cuerpo = "📷 Envió una imagen"
    elif mensaje.tipo == TipoMensaje.AUDIO:
        if mensaje.duracion_audio:
            cuerpo = f"🎤 Envió un audio ({mensaje.duracion_audio}s)"
        else:
            cuerpo = "🎤 Envió un audio"
    else:
        cuerpo = "Nuevo mensaje"

    return titulo, cuerpo


# ============================================
# NOTIFICAR NUEVO CHAT
# ============================================

def enviar_notificacion_nuevo_chat(chat, usuario_notificar):
    """
    Envía notificación cuando se crea un nuevo chat

    Args:
        chat (Chat): Chat creado
        usuario_notificar (User): Usuario a notificar
    """
    if not inicializar_firebase():
        return

    try:
        if not hasattr(usuario_notificar, 'perfil_usuario'):
            return

        perfil = usuario_notificar.perfil_usuario

        if not perfil.fcm_token or not perfil.puede_recibir_notificaciones:
            return

        # Construir notificación
        if chat.tipo == 'pedido_cliente':
            titulo = "Nuevo chat de pedido"
            cuerpo = f"Chat iniciado para el pedido #{chat.pedido.pk}"
        elif chat.tipo == 'pedido_proveedor':
            titulo = "Coordinación de recojo"
            cuerpo = f"Chat con repartidor para pedido #{chat.pedido.pk}"
        elif chat.tipo == 'soporte':
            titulo = "Chat de soporte iniciado"
            cuerpo = "Un administrador te ayudará pronto"
        else:
            titulo = "Nuevo chat"
            cuerpo = chat.titulo

        notification = messaging.Notification(
            title=titulo,
            body=cuerpo
        )

        data = {
            'tipo': 'nuevo_chat',
            'chat_id': str(chat.id),
            'chat_tipo': chat.tipo
        }

        message = messaging.Message(
            notification=notification,
            data=data,
            token=perfil.fcm_token
        )

        response = messaging.send(message)
        logger.info(f"✅ Notificación de nuevo chat enviada a {usuario_notificar.email}")

    except Exception as e:
        logger.error(f"❌ Error enviando notificación de nuevo chat: {e}", exc_info=True)


# ============================================
# FUNCIONES AUXILIARES
# ============================================

def test_notificacion_firebase(token_fcm, titulo="Test", mensaje="Mensaje de prueba"):
    """
    Función de prueba para verificar que Firebase funciona

    Args:
        token_fcm (str): Token FCM del dispositivo
        titulo (str): Título de la notificación
        mensaje (str): Cuerpo de la notificación

    Returns:
        bool: True si se envió correctamente
    """
    if not inicializar_firebase():
        logger.error("❌ No se pudo inicializar Firebase")
        return False

    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje
            ),
            token=token_fcm
        )

        response = messaging.send(message)
        logger.info(f"✅ Notificación de prueba enviada. Response: {response}")
        return True

    except Exception as e:
        logger.error(f"❌ Error en test de notificación: {e}", exc_info=True)
        return False


def enviar_notificacion_multiple(usuarios, titulo, mensaje, data=None):
    """
    Envía notificación a múltiples usuarios

    Args:
        usuarios (list): Lista de usuarios
        titulo (str): Título
        mensaje (str): Mensaje
        data (dict): Datos adicionales

    Returns:
        dict: Resultados del envío
    """
    if not inicializar_firebase():
        return {'success': False, 'error': 'Firebase no inicializado'}

    tokens = []
    usuarios_con_token = []

    # Recolectar tokens
    for usuario in usuarios:
        if hasattr(usuario, 'perfil_usuario'):
            perfil = usuario.perfil_usuario
            if perfil.fcm_token and perfil.puede_recibir_notificaciones:
                tokens.append(perfil.fcm_token)
                usuarios_con_token.append(usuario)

    if not tokens:
        return {'success': False, 'error': 'Ningún usuario tiene token FCM'}

    try:
        # Crear mensaje multicast
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje
            ),
            data=data or {},
            tokens=tokens
        )

        # Enviar
        response = messaging.send_multicast(message)

        logger.info(
            f"✅ Notificación múltiple enviada. "
            f"Éxitos: {response.success_count}, Fallos: {response.failure_count}"
        )

        return {
            'success': True,
            'success_count': response.success_count,
            'failure_count': response.failure_count
        }

    except Exception as e:
        logger.error(f"❌ Error en notificación múltiple: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}
