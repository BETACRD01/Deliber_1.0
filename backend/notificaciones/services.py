# notificaciones/services.py
"""
Servicio de Firebase Cloud Messaging (FCM)
✅ Envío de notificaciones push
✅ Inicialización automática de Firebase
✅ Manejo robusto de errores
"""

import logging
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
from typing import Optional, Dict, List
import os

logger = logging.getLogger('notificaciones')

# Variable global para verificar si Firebase está inicializado
_firebase_initialized = False


def inicializar_firebase():
    """
    ✅ Inicializa Firebase Admin SDK (solo una vez)

    Raises:
        Exception: Si no se puede inicializar Firebase
    """
    global _firebase_initialized

    if _firebase_initialized:
        return

    try:
        # Verificar si ya hay una app inicializada
        if firebase_admin._apps:
            logger.info("✅ Firebase ya estaba inicializado")
            _firebase_initialized = True
            return

        # Obtener ruta del archivo de credenciales
        credentials_path = getattr(
            settings,
            'FIREBASE_CREDENTIALS_PATH',
            os.path.join(settings.BASE_DIR, 'firebase-credentials.json')
        )

        # Verificar que el archivo existe
        if not os.path.exists(credentials_path):
            raise FileNotFoundError(
                f"Archivo de credenciales no encontrado: {credentials_path}"
            )

        # Inicializar Firebase
        cred = credentials.Certificate(credentials_path)
        firebase_admin.initialize_app(cred)

        _firebase_initialized = True
        logger.info(f"✅ Firebase inicializado correctamente: {credentials_path}")

    except Exception as e:
        logger.error(f"❌ Error inicializando Firebase: {e}", exc_info=True)
        raise


def enviar_notificacion_push(
    usuario,
    titulo: str,
    mensaje: str,
    datos_extra: Optional[Dict] = None,
    guardar_en_bd: bool = True
) -> tuple[bool, Optional[str]]:
    """
    ✅ Envía una notificación push a un usuario específico

    Args:
        usuario (User): Usuario destinatario
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación
        datos_extra (dict, optional): Datos adicionales
        guardar_en_bd (bool): Si debe guardar en BD (default: True)

    Returns:
        tuple: (éxito: bool, error: str o None)
    """
    from notificaciones.models import Notificacion

    # Inicializar Firebase si no está inicializado
    try:
        inicializar_firebase()
    except Exception as e:
        error_msg = f"Error inicializando Firebase: {e}"
        logger.error(f"❌ {error_msg}")

        # Guardar en BD aunque falle el envío push
        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg

    # Verificar si el usuario tiene FCM token
    if not hasattr(usuario, 'perfil_usuario'):
        error_msg = "Usuario no tiene perfil asociado"
        logger.warning(f"⚠️ {error_msg}: {usuario.email}")

        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg

    perfil = usuario.perfil_usuario

    if not perfil.fcm_token:
        error_msg = "Usuario no tiene FCM token registrado"
        logger.warning(f"⚠️ {error_msg}: {usuario.email}")

        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg

    # Verificar preferencias de notificación
    if not perfil.puede_recibir_notificaciones:
        error_msg = "Usuario tiene notificaciones deshabilitadas"
        logger.info(f"ℹ️ {error_msg}: {usuario.email}")

        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg

    # Preparar datos adicionales
    if datos_extra is None:
        datos_extra = {}

    # Convertir todos los valores a string (FCM solo acepta strings)
    datos_str = {str(k): str(v) for k, v in datos_extra.items()}

    # Crear mensaje de Firebase
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje
            ),
            data=datos_str,
            token=perfil.fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    color='#FF6B35',  # Color naranja de tu app
                    channel_id='pedidos_channel'
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

        # Enviar notificación
        response = messaging.send(message)

        logger.info(
            f"✅ Notificación push enviada: {usuario.email} | "
            f"Response: {response}"
        )

        # Guardar en BD
        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=True,
                error_envio=None
            )

        return True, None

    except messaging.UnregisteredError:
        error_msg = "Token FCM inválido o expirado"
        logger.warning(f"⚠️ {error_msg}: {usuario.email}")

        # Limpiar token inválido
        perfil.eliminar_fcm_token()

        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg

    except Exception as e:
        error_msg = f"Error enviando notificación push: {str(e)}"
        logger.error(f"❌ {error_msg}", exc_info=True)

        if guardar_en_bd:
            _guardar_notificacion_en_bd(
                usuario=usuario,
                titulo=titulo,
                mensaje=mensaje,
                datos_extra=datos_extra,
                enviada_push=False,
                error_envio=error_msg
            )

        return False, error_msg


def enviar_notificacion_masiva(
    usuarios: List,
    titulo: str,
    mensaje: str,
    datos_extra: Optional[Dict] = None,
    guardar_en_bd: bool = True
) -> Dict[str, int]:
    """
    ✅ Envía notificaciones push a múltiples usuarios

    Args:
        usuarios (List[User]): Lista de usuarios
        titulo (str): Título de la notificación
        mensaje (str): Mensaje de la notificación
        datos_extra (dict, optional): Datos adicionales
        guardar_en_bd (bool): Si debe guardar en BD

    Returns:
        dict: Estadísticas del envío {exitosos, fallidos, sin_token}
    """
    estadisticas = {
        'exitosos': 0,
        'fallidos': 0,
        'sin_token': 0
    }

    for usuario in usuarios:
        exito, error = enviar_notificacion_push(
            usuario=usuario,
            titulo=titulo,
            mensaje=mensaje,
            datos_extra=datos_extra,
            guardar_en_bd=guardar_en_bd
        )

        if exito:
            estadisticas['exitosos'] += 1
        elif error and 'no tiene FCM token' in error:
            estadisticas['sin_token'] += 1
        else:
            estadisticas['fallidos'] += 1

    logger.info(
        f"📊 Envío masivo completado: "
        f"Exitosos: {estadisticas['exitosos']}, "
        f"Fallidos: {estadisticas['fallidos']}, "
        f"Sin token: {estadisticas['sin_token']}"
    )

    return estadisticas


def _guardar_notificacion_en_bd(
    usuario,
    titulo: str,
    mensaje: str,
    datos_extra: Optional[Dict],
    enviada_push: bool,
    error_envio: Optional[str],
    tipo: str = 'pedido',
    pedido=None
):
    """
    ✅ Guarda la notificación en la base de datos

    Función interna para guardar notificaciones en BD
    """
    from notificaciones.models import Notificacion

    try:
        Notificacion.objects.create(
            usuario=usuario,
            pedido=pedido,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_extra=datos_extra or {},
            enviada_push=enviada_push,
            error_envio=error_envio
        )

        logger.debug(
            f"💾 Notificación guardada en BD: {usuario.email} | "
            f"Push: {enviada_push}"
        )

    except Exception as e:
        logger.error(
            f"❌ Error guardando notificación en BD: {e}",
            exc_info=True
        )


def crear_y_enviar_notificacion(
    usuario,
    titulo: str,
    mensaje: str,
    tipo: str = 'pedido',
    pedido=None,
    datos_extra: Optional[Dict] = None
) -> bool:
    """
    ✅ Crea y envía una notificación (push + BD)

    Función de alto nivel que combina envío push y guardado en BD

    Args:
        usuario (User): Usuario destinatario
        titulo (str): Título
        mensaje (str): Mensaje
        tipo (str): Tipo de notificación (default: 'pedido')
        pedido (Pedido, optional): Pedido relacionado
        datos_extra (dict, optional): Datos adicionales

    Returns:
        bool: True si se guardó en BD (independiente del push)
    """
    from notificaciones.models import Notificacion

    # Intentar enviar push
    exito_push, error = enviar_notificacion_push(
        usuario=usuario,
        titulo=titulo,
        mensaje=mensaje,
        datos_extra=datos_extra,
        guardar_en_bd=False  # Lo haremos manualmente
    )

    # Guardar en BD
    try:
        Notificacion.objects.create(
            usuario=usuario,
            pedido=pedido,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            datos_extra=datos_extra or {},
            enviada_push=exito_push,
            error_envio=error
        )

        logger.info(
            f"✅ Notificación creada: {usuario.email} | "
            f"Tipo: {tipo} | Push: {exito_push}"
        )

        return True

    except Exception as e:
        logger.error(
            f"❌ Error creando notificación: {e}",
            exc_info=True
        )
        return False
