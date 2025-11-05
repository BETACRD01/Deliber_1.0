# utils/firebase_service.py

"""
Servicio Unificado de Notificaciones Push con Firebase Cloud Messaging (FCM)
✅ Combina inicialización robusta + integración con BD + notificaciones tipificadas
✅ Auto-limpieza de tokens inválidos + validación de preferencias
"""
import firebase_admin
from firebase_admin import credentials, messaging
import logging
from django.conf import settings
import os

logger = logging.getLogger('firebase')


class FirebaseService:
    """
    Servicio centralizado para enviar notificaciones push con Firebase
    Combina inicialización robusta con integración directa a modelos Django
    """

    _initialized = False
    _app = None

    # ==========================================
    # INICIALIZACIÓN
    # ==========================================

    @classmethod
    def initialize(cls):
        """
        Inicializa Firebase Admin SDK
        ⚠️ DEBE llamarse una sola vez al iniciar Django (en apps.py)
        """
        if cls._initialized:
            logger.info("Firebase ya está inicializado")
            return True

        try:
            # Buscar archivo de credenciales
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)

            if not cred_path:
                cred_path = os.path.join(settings.BASE_DIR, 'firebase-credentials.json')

            if not os.path.exists(cred_path):
                logger.warning(
                    f"⚠️ Archivo de credenciales de Firebase no encontrado en: {cred_path}\n"
                    "Las notificaciones push NO funcionarán hasta que configures Firebase.\n"
                    "Para configurar:\n"
                    "1. Ve a Firebase Console > Configuración del proyecto > Cuentas de servicio\n"
                    "2. Genera una nueva clave privada\n"
                    "3. Guarda el archivo como 'firebase-credentials.json' en la raíz del proyecto"
                )
                return False

            # Inicializar Firebase
            cred = credentials.Certificate(cred_path)
            cls._app = firebase_admin.initialize_app(cred)
            cls._initialized = True

            logger.info("✅ Firebase inicializado correctamente")
            return True

        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {e}", exc_info=True)
            return False

    @classmethod
    def is_initialized(cls):
        """Verifica si Firebase está inicializado"""
        return cls._initialized

    # ==========================================
    # ENVÍO DE NOTIFICACIONES - NIVEL BAJO
    # ==========================================

    @staticmethod
    def enviar_notificacion(token, titulo, mensaje, data=None, imagen_url=None):
        """
        Envía una notificación push a UN dispositivo (nivel bajo)

        Args:
            token (str): Token FCM del dispositivo
            titulo (str): Título de la notificación
            mensaje (str): Cuerpo de la notificación
            data (dict, optional): Datos adicionales para la app
            imagen_url (str, optional): URL de imagen para mostrar

        Returns:
            dict: {'success': bool, 'message_id': str, 'error': str}

        Ejemplo:
            result = FirebaseService.enviar_notificacion(
                token='fcm_token_del_usuario',
                titulo='¡Pedido Confirmado!',
                mensaje='Tu pedido #12345 ha sido confirmado',
                data={'tipo': 'pedido_confirmado', 'pedido_id': '12345'}
            )
        """
        if not FirebaseService.is_initialized():
            logger.warning("Firebase no está inicializado")
            return {'success': False, 'error': 'Firebase no inicializado'}

        if not token:
            logger.warning("Token FCM vacío")
            return {'success': False, 'error': 'Token vacío'}

        try:
            # Construir la notificación
            notification = messaging.Notification(
                title=titulo,
                body=mensaje,
                image=imagen_url
            )

            # Construir mensaje
            message = messaging.Message(
                notification=notification,
                data=data if isinstance(data, dict) else {},
                token=token,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        color=getattr(settings, 'FCM_ANDROID_COLOR', '#4FC3F7'),
                        channel_id=getattr(settings, 'FCM_ANDROID_CHANNEL_ID', 'pedidos')
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

            # Enviar mensaje
            response = messaging.send(message)

            logger.info(f"✅ Notificación enviada correctamente: {response}")
            return {'success': True, 'message_id': response}

        except messaging.UnregisteredError:
            logger.warning(f"⚠️ Token FCM no registrado o expirado: {token[:20]}...")
            return {'success': False, 'error': 'Token inválido o expirado', 'token_invalido': True}

        except messaging.SenderIdMismatchError:
            logger.error(f"❌ Error de configuración FCM: Sender ID incorrecto")
            return {'success': False, 'error': 'Error de configuración FCM'}

        except Exception as e:
            logger.error(f"❌ Error enviando notificación: {e}", exc_info=True)
            return {'success': False, 'error': str(e)}

    @staticmethod
    def enviar_notificacion_multiple(tokens, titulo, mensaje, data=None, imagen_url=None):
        """
        Envía una notificación push a MÚLTIPLES dispositivos

        Args:
            tokens (list): Lista de tokens FCM (máx 500 por lote)
            titulo (str): Título de la notificación
            mensaje (str): Cuerpo de la notificación
            data (dict, optional): Datos adicionales
            imagen_url (str, optional): URL de imagen

        Returns:
            dict: {'success': int, 'failure': int, 'tokens_invalidos': list, 'total': int}
        """
        if not FirebaseService.is_initialized():
            logger.warning("Firebase no está inicializado")
            return {'success': 0, 'failure': len(tokens), 'tokens_invalidos': tokens, 'total': len(tokens)}

        if not tokens or len(tokens) == 0:
            logger.warning("Lista de tokens vacía")
            return {'success': 0, 'failure': 0, 'tokens_invalidos': [], 'total': 0}

        # Limitar a 500 tokens (límite de FCM)
        batch_size = getattr(settings, 'FCM_BATCH_SIZE', 500)
        if len(tokens) > batch_size:
            logger.warning(f"⚠️ Tokens exceden límite de {batch_size}. Procesando en lotes...")
            return FirebaseService._enviar_notificacion_lotes(tokens, titulo, mensaje, data, imagen_url, batch_size)

        try:
            # Construir notificación
            notification = messaging.Notification(
                title=titulo,
                body=mensaje,
                image=imagen_url
            )

            # Construir mensaje multicast
            message = messaging.MulticastMessage(
                notification=notification,
                data=data if isinstance(data, dict) else {},
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        sound='default',
                        color=getattr(settings, 'FCM_ANDROID_COLOR', '#4FC3F7'),
                        channel_id=getattr(settings, 'FCM_ANDROID_CHANNEL_ID', 'pedidos')
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

            # Enviar mensaje
            response = messaging.send_multicast(message)

            # Identificar tokens inválidos
            tokens_invalidos = []
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        tokens_invalidos.append(tokens[idx])

            logger.info(
                f"📨 Notificaciones enviadas: {response.success_count}/{len(tokens)} exitosas, "
                f"{response.failure_count} fallidas"
            )

            return {
                'success': response.success_count,
                'failure': response.failure_count,
                'tokens_invalidos': tokens_invalidos,
                'total': len(tokens)
            }

        except Exception as e:
            logger.error(f"❌ Error enviando notificaciones múltiples: {e}", exc_info=True)
            return {'success': 0, 'failure': len(tokens), 'tokens_invalidos': tokens, 'total': len(tokens)}

    @staticmethod
    def _enviar_notificacion_lotes(tokens, titulo, mensaje, data, imagen_url, batch_size):
        """
        Procesa envío de notificaciones en lotes para grandes cantidades
        """
        total_success = 0
        total_failure = 0
        total_invalidos = []

        for i in range(0, len(tokens), batch_size):
            batch = tokens[i:i + batch_size]
            logger.info(f"📦 Procesando lote {i//batch_size + 1} ({len(batch)} tokens)")

            result = FirebaseService.enviar_notificacion_multiple(
                batch, titulo, mensaje, data, imagen_url
            )

            total_success += result['success']
            total_failure += result['failure']
            total_invalidos.extend(result['tokens_invalidos'])

        return {
            'success': total_success,
            'failure': total_failure,
            'tokens_invalidos': total_invalidos,
            'total': len(tokens)
        }

    # ==========================================
    # ENVÍO CON INTEGRACIÓN A MODELOS DJANGO
    # ==========================================

    @staticmethod
    def enviar_a_usuario(user_id, titulo, mensaje, data=None, imagen_url=None):
        """
        Envía notificación a un usuario específico con validación de BD
        ✅ Valida preferencias del usuario
        ✅ Auto-limpia tokens inválidos

        Args:
            user_id (int): ID del usuario destinatario
            titulo (str): Título de la notificación
            mensaje (str): Cuerpo del mensaje
            data (dict, optional): Datos adicionales
            imagen_url (str, optional): URL de imagen

        Returns:
            dict: {'success': bool, 'message': str, 'usuario': str}
        """
        from usuarios.models import Perfil

        try:
            # Obtener perfil con token FCM
            perfil = Perfil.objects.select_related('user').filter(
                user_id=user_id,
                fcm_token__isnull=False
            ).exclude(fcm_token='').first()

            if not perfil or not perfil.fcm_token:
                logger.warning(f'⚠️ Usuario {user_id} sin token FCM activo')
                return {
                    'success': False,
                    'message': 'Usuario sin dispositivo registrado'
                }

            # Verificar si el usuario tiene notificaciones habilitadas
            if not perfil.puede_recibir_notificaciones:
                logger.info(f'ℹ️ Usuario {user_id} tiene notificaciones deshabilitadas')
                return {
                    'success': False,
                    'message': 'Usuario tiene notificaciones deshabilitadas'
                }

            logger.info(f'📤 Enviando notificación a {perfil.user.email}')

            # Enviar notificación
            result = FirebaseService.enviar_notificacion(
                token=perfil.fcm_token,
                titulo=titulo,
                mensaje=mensaje,
                data=data,
                imagen_url=imagen_url
            )

            # Auto-limpiar token inválido
            if not result['success'] and result.get('token_invalido'):
                logger.warning(f'🗑️ Limpiando token inválido para usuario {user_id}')
                perfil.eliminar_fcm_token()

            return {
                'success': result['success'],
                'message': result.get('error', 'Enviado correctamente'),
                'usuario': perfil.user.email,
                'message_id': result.get('message_id')
            }

        except Exception as e:
            logger.error(f'❌ Error enviando notificación a usuario {user_id}: {str(e)}', exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    @staticmethod
    def enviar_a_usuarios(user_ids, titulo, mensaje, data=None, imagen_url=None):
        """
        Envía notificaciones a múltiples usuarios con validación de BD
        ✅ Filtra usuarios con notificaciones habilitadas
        ✅ Auto-limpia tokens inválidos en batch

        Args:
            user_ids (list): Lista de IDs de usuarios
            titulo (str): Título de la notificación
            mensaje (str): Cuerpo del mensaje
            data (dict, optional): Datos adicionales
            imagen_url (str, optional): URL de imagen

        Returns:
            dict: {'success': int, 'failure': int, 'total': int}
        """
        from usuarios.models import Perfil

        try:
            # Obtener tokens válidos
            perfiles = Perfil.objects.filter(
                user_id__in=user_ids,
                fcm_token__isnull=False,
                notificaciones_pedido=True
            ).exclude(fcm_token='')

            tokens = [p.fcm_token for p in perfiles]

            if not tokens:
                logger.warning('⚠️ No hay usuarios con tokens FCM activos')
                return {
                    'success': False,
                    'message': 'No hay destinatarios con notificaciones habilitadas'
                }

            logger.info(f'📤 Enviando notificación masiva a {len(tokens)} usuario(s)')

            # Enviar notificaciones
            result = FirebaseService.enviar_notificacion_multiple(
                tokens=tokens,
                titulo=titulo,
                mensaje=mensaje,
                data=data,
                imagen_url=imagen_url
            )

            # Limpiar tokens inválidos
            if result['tokens_invalidos']:
                Perfil.objects.filter(
                    fcm_token__in=result['tokens_invalidos']
                ).update(
                    fcm_token=None,
                    fcm_token_actualizado=None
                )
                logger.warning(f'🗑️ {len(result["tokens_invalidos"])} token(s) inválido(s) limpiados')

            return {
                'success': True,
                'success_count': result['success'],
                'failure_count': result['failure'],
                'total': result['total']
            }

        except Exception as e:
            logger.error(f'❌ Error en notificación masiva: {str(e)}', exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    # ==========================================
    # NOTIFICACIONES ESPECÍFICAS PARA PEDIDOS
    # ==========================================

    @staticmethod
    def notificar_pedido_confirmado(perfil, pedido):
        """
        Notifica cuando un pedido es confirmado

        Args:
            perfil (Perfil): Perfil del usuario
            pedido (Pedido): Instancia del pedido

        Returns:
            dict: Resultado del envío
        """
        if not perfil.puede_recibir_notificaciones:
            logger.info(f"Usuario {perfil.user.email} tiene notificaciones desactivadas")
            return {'success': False, 'message': 'Notificaciones desactivadas'}

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo='¡Pedido Confirmado! 🎉',
            mensaje=f'Tu pedido #{pedido.numero_pedido} ha sido confirmado y está siendo preparado',
            data={
                'tipo': 'pedido_confirmado',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'accion': 'abrir_detalle'
            }
        )

        # Auto-limpiar si token inválido
        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    @staticmethod
    def notificar_pedido_en_camino(perfil, pedido, repartidor_nombre):
        """
        Notifica cuando el pedido está en camino

        Args:
            perfil (Perfil): Perfil del usuario
            pedido (Pedido): Instancia del pedido
            repartidor_nombre (str): Nombre del repartidor

        Returns:
            dict: Resultado del envío
        """
        if not perfil.puede_recibir_notificaciones:
            return {'success': False, 'message': 'Notificaciones desactivadas'}

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo='¡Tu pedido está en camino! 🚚',
            mensaje=f'{repartidor_nombre} está llevando tu pedido #{pedido.numero_pedido}',
            data={
                'tipo': 'pedido_en_camino',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'repartidor': repartidor_nombre,
                'accion': 'rastrear_pedido'
            }
        )

        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    @staticmethod
    def notificar_pedido_entregado(perfil, pedido):
        """
        Notifica cuando el pedido ha sido entregado

        Args:
            perfil (Perfil): Perfil del usuario
            pedido (Pedido): Instancia del pedido

        Returns:
            dict: Resultado del envío
        """
        if not perfil.puede_recibir_notificaciones:
            return {'success': False, 'message': 'Notificaciones desactivadas'}

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo='¡Pedido Entregado! ✅',
            mensaje='Tu pedido ha sido entregado. ¡Califica el servicio!',
            data={
                'tipo': 'pedido_entregado',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'puede_calificar': 'true',
                'accion': 'calificar_servicio'
            }
        )

        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    @staticmethod
    def notificar_pedido_cancelado(perfil, pedido, razon=''):
        """
        Notifica cuando un pedido es cancelado

        Args:
            perfil (Perfil): Perfil del usuario
            pedido (Pedido): Instancia del pedido
            razon (str): Razón de cancelación

        Returns:
            dict: Resultado del envío
        """
        if not perfil.puede_recibir_notificaciones:
            return {'success': False, 'message': 'Notificaciones desactivadas'}

        mensaje = f'Tu pedido #{pedido.numero_pedido} ha sido cancelado'
        if razon:
            mensaje += f'. Razón: {razon}'

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo='Pedido Cancelado ❌',
            mensaje=mensaje,
            data={
                'tipo': 'pedido_cancelado',
                'pedido_id': str(pedido.id),
                'numero_pedido': pedido.numero_pedido,
                'razon': razon,
                'accion': 'ver_detalle'
            }
        )

        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    # ==========================================
    # NOTIFICACIONES DE PROMOCIONES
    # ==========================================

    @staticmethod
    def notificar_promocion(perfil, titulo, mensaje, imagen_url=None, data=None):
        """
        Envía notificación de promoción

        Args:
            perfil (Perfil): Perfil del usuario
            titulo (str): Título de la promoción
            mensaje (str): Descripción de la promoción
            imagen_url (str, optional): URL de imagen de la promoción
            data (dict, optional): Datos adicionales

        Returns:
            dict: Resultado del envío
        """
        if not perfil.notificaciones_promociones or not perfil.tiene_fcm_token:
            return {'success': False, 'message': 'Promociones desactivadas o sin token'}

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo=titulo,
            mensaje=mensaje,
            imagen_url=imagen_url,
            data=data or {
                'tipo': 'promocion',
                'accion': 'ver_promociones'
            }
        )

        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    # ==========================================
    # UTILIDADES
    # ==========================================

    @staticmethod
    def validar_token(token):
        """
        Valida si un token FCM es válido usando dry run

        Args:
            token (str): Token FCM

        Returns:
            bool: True si es válido, False si no
        """
        if not token or len(token) < 50:
            return False

        try:
            # Intentar enviar un mensaje de prueba (dry run)
            message = messaging.Message(
                data={'test': 'true'},
                token=token
            )
            messaging.send(message, dry_run=True)
            return True

        except Exception as e:
            logger.warning(f"Token inválido: {e}")
            return False


# ==========================================
# FUNCIONES DE CONVENIENCIA GLOBAL
# ==========================================

def enviar_notificacion_a_usuario(user, titulo, mensaje, data=None, imagen_url=None):
    """
    Función de conveniencia para enviar notificación a un usuario Django

    Args:
        user (User): Usuario de Django
        titulo (str): Título
        mensaje (str): Mensaje
        data (dict, optional): Datos adicionales
        imagen_url (str, optional): URL de imagen

    Returns:
        dict: Resultado del envío
    """
    try:
        perfil = user.perfil_usuario

        if not perfil.puede_recibir_notificaciones:
            logger.info(f"Usuario {user.email} no puede recibir notificaciones")
            return {'success': False, 'message': 'Notificaciones desactivadas'}

        result = FirebaseService.enviar_notificacion(
            token=perfil.fcm_token,
            titulo=titulo,
            mensaje=mensaje,
            data=data,
            imagen_url=imagen_url
        )

        # Auto-limpiar token inválido
        if not result['success'] and result.get('token_invalido'):
            perfil.eliminar_fcm_token()

        return result

    except Exception as e:
        logger.error(f"Error enviando notificación a usuario {user.email}: {e}")
        return {'success': False, 'error': str(e)}


def enviar_notificacion_masiva(usuarios, titulo, mensaje, data=None, imagen_url=None):
    """
    Envía notificación a múltiples usuarios (QuerySet)

    Args:
        usuarios (QuerySet): QuerySet de usuarios
        titulo (str): Título
        mensaje (str): Mensaje
        data (dict, optional): Datos adicionales
        imagen_url (str, optional): URL de imagen

    Returns:
        dict: Estadísticas de envío
    """
    # Obtener tokens válidos
    tokens = []
    for user in usuarios:
        try:
            perfil = user.perfil_usuario
            if perfil.puede_recibir_notificaciones:
                tokens.append(perfil.fcm_token)
        except:
            pass

    if not tokens:
        logger.warning("No hay tokens válidos para enviar notificaciones")
        return {'success': 0, 'failure': 0, 'tokens_invalidos': []}

    result = FirebaseService.enviar_notificacion_multiple(
        tokens=tokens,
        titulo=titulo,
        mensaje=mensaje,
        data=data,
        imagen_url=imagen_url
    )

    # Limpiar tokens inválidos
    if result.get('tokens_invalidos'):
        from usuarios.models import Perfil
        Perfil.objects.filter(
            fcm_token__in=result['tokens_invalidos']
        ).update(
            fcm_token=None,
            fcm_token_actualizado=None
        )

    return result
