# chat/models.py
"""
Sistema de Chat Multi-propósito para Delivery App

✅ FLUJOS SOPORTADOS:
1. Pedido de Proveedor → 2 chats: Proveedor↔Repartidor + Cliente↔Repartidor
2. Encargo Directo → 1 chat: Cliente↔Repartidor
3. Soporte Proveedor → 1 chat: Proveedor↔Admin

✅ FUNCIONALIDADES:
- Mensajes multimedia: texto, foto, audio
- Notificaciones push Firebase
- Privacidad por participantes
- Soft delete y auditoría
"""

from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from authentication.models import User
from pedidos.models import Pedido
from proveedores.models import Proveedor
import uuid
import logging

logger = logging.getLogger('chat')


# ============================================
# 🔧 UTILIDADES Y VALIDADORES
# ============================================

def validar_tamano_archivo(archivo):
    """Valida que el archivo no exceda 10MB"""
    limite_mb = 10
    limite_bytes = limite_mb * 1024 * 1024

    if archivo.size > limite_bytes:
        tamano_actual = archivo.size / (1024 * 1024)
        raise ValidationError(
            f'El archivo no puede superar {limite_mb}MB '
            f'(tamaño actual: {tamano_actual:.1f}MB)'
        )


# ============================================
# 📋 ENUMS
# ============================================

class TipoChat(models.TextChoices):
    """Tipos de chat disponibles"""
    PEDIDO_CLIENTE = 'pedido_cliente', 'Chat Cliente-Repartidor (Entrega)'
    PEDIDO_PROVEEDOR = 'pedido_proveedor', 'Chat Proveedor-Repartidor (Recojo)'
    SOPORTE = 'soporte', 'Chat Soporte (Proveedor-Admin)'


class TipoMensaje(models.TextChoices):
    """Tipos de mensaje"""
    TEXTO = 'texto', 'Texto'
    IMAGEN = 'imagen', 'Imagen'
    AUDIO = 'audio', 'Audio'
    SISTEMA = 'sistema', 'Mensaje del Sistema'


# ============================================
# 💬 MODELO: CHAT
# ============================================

class Chat(models.Model):
    """
    Sala de chat entre participantes

    ✅ 3 TIPOS:
    1. PEDIDO_CLIENTE: Cliente ↔ Repartidor (coordinación entrega)
    2. PEDIDO_PROVEEDOR: Proveedor ↔ Repartidor (coordinación recojo)
    3. SOPORTE: Proveedor ↔ Admin (consultas/problemas)

    ⚙️ LÓGICA AUTOMÁTICA:
    - Pedido de Proveedor → Se crean 2 chats (cliente+proveedor)
    - Encargo Directo → Se crea 1 chat (solo cliente)
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    tipo = models.CharField(
        max_length=30,
        choices=TipoChat.choices,
        verbose_name='Tipo de Chat',
        db_index=True
    )

    # ============================================
    # RELACIONES
    # ============================================

    # Para CHATS DE PEDIDO (ambos tipos)
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chats',
        verbose_name='Pedido',
        help_text='Para tipos PEDIDO_CLIENTE y PEDIDO_PROVEEDOR'
    )

    # Para CHAT DE SOPORTE
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='chats_soporte',
        verbose_name='Proveedor',
        help_text='Solo para tipo SOPORTE'
    )

    # Participantes (siempre 2 usuarios)
    participantes = models.ManyToManyField(
        User,
        related_name='chats_participando',
        verbose_name='Participantes'
    )

    # ============================================
    # METADATA
    # ============================================

    titulo = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Título del Chat',
        help_text='Generado automáticamente'
    )

    activo = models.BooleanField(
        default=True,
        verbose_name='Chat Activo',
        db_index=True
    )

    # ============================================
    # AUDITORÍA
    # ============================================

    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Creación',
        db_index=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Actualización'
    )

    cerrado_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Cierre',
        help_text='Cuando se cierra/archiva el chat'
    )

    class Meta:
        db_table = 'chats'
        verbose_name = 'Chat'
        verbose_name_plural = 'Chats'
        ordering = ['-actualizado_en']
        indexes = [
            models.Index(fields=['tipo', 'activo']),
            models.Index(fields=['pedido']),
            models.Index(fields=['proveedor']),
            models.Index(fields=['-actualizado_en']),
        ]
        constraints = [
            # Chat de pedido DEBE tener pedido
            models.CheckConstraint(
                check=(
                    ~models.Q(tipo__in=['pedido_cliente', 'pedido_proveedor']) |
                    models.Q(pedido__isnull=False)
                ),
                name='chat_pedido_require_pedido'
            ),
            # Chat de soporte DEBE tener proveedor
            models.CheckConstraint(
                check=~models.Q(tipo='soporte') | models.Q(proveedor__isnull=False),
                name='chat_soporte_require_proveedor'
            ),
        ]

    def __str__(self):
        if self.tipo == TipoChat.PEDIDO_CLIENTE and self.pedido:
            return f"Cliente↔Repartidor - Pedido #{self.pedido.pk}"
        elif self.tipo == TipoChat.PEDIDO_PROVEEDOR and self.pedido:
            return f"Proveedor↔Repartidor - Pedido #{self.pedido.pk}"
        elif self.tipo == TipoChat.SOPORTE and self.proveedor:
            return f"Soporte: {self.proveedor.nombre}"
        return f"Chat {self.id}"

    # ============================================
    # ✅ VALIDACIONES
    # ============================================

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        errors = {}

        # Validar tipos de pedido
        if self.tipo in [TipoChat.PEDIDO_CLIENTE, TipoChat.PEDIDO_PROVEEDOR]:
            if not self.pedido:
                errors['pedido'] = f'Chat tipo {self.get_tipo_display()} requiere un pedido'

        # Validar tipo SOPORTE
        if self.tipo == TipoChat.SOPORTE:
            if not self.proveedor:
                errors['proveedor'] = 'Chat de SOPORTE requiere un proveedor'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save para generar título automático"""
        self.full_clean()

        # Generar título si está vacío
        if not self.titulo:
            if self.tipo == TipoChat.PEDIDO_CLIENTE and self.pedido:
                self.titulo = f"Pedido #{self.pedido.pk} - Entrega"
            elif self.tipo == TipoChat.PEDIDO_PROVEEDOR and self.pedido:
                self.titulo = f"Pedido #{self.pedido.pk} - Recojo"
            elif self.tipo == TipoChat.SOPORTE and self.proveedor:
                self.titulo = f"Soporte - {self.proveedor.nombre}"

        super().save(*args, **kwargs)

    # ============================================
    # ✅ MÉTODOS DE NEGOCIO
    # ============================================

    def agregar_participante(self, usuario):
        """
        Agrega un participante al chat

        Args:
            usuario (User): Usuario a agregar
        """
        if self.participantes.count() >= 2:
            if usuario not in self.participantes.all():
                raise ValidationError('El chat ya tiene 2 participantes')

        self.participantes.add(usuario)
        logger.info(f"✅ Usuario {usuario.email} agregado al chat {self.id}")

    def usuario_puede_participar(self, usuario):
        """
        Verifica si un usuario puede participar en este chat

        Args:
            usuario (User): Usuario a verificar

        Returns:
            bool: True si puede participar
        """
        # Admin puede ver todos
        if usuario.es_admin():
            return True

        # Verificar si es participante
        return self.participantes.filter(id=usuario.id).exists()

    def cerrar_chat(self):
        """Cierra/archiva el chat"""
        self.activo = False
        self.cerrado_en = timezone.now()
        self.save(update_fields=['activo', 'cerrado_en', 'actualizado_en'])
        logger.info(f"🔒 Chat {self.id} cerrado")

    def reabrir_chat(self):
        """Reabre un chat cerrado"""
        self.activo = True
        self.cerrado_en = None
        self.save(update_fields=['activo', 'cerrado_en', 'actualizado_en'])
        logger.info(f"🔓 Chat {self.id} reabierto")

    def obtener_mensajes_no_leidos(self, usuario):
        """
        Obtiene mensajes no leídos para un usuario

        Args:
            usuario (User): Usuario que consulta

        Returns:
            QuerySet: Mensajes no leídos
        """
        return self.mensajes.filter(
            leido=False,
            eliminado=False
        ).exclude(
            remitente=usuario
        )

    def contar_no_leidos(self, usuario):
        """
        Cuenta mensajes no leídos para un usuario

        Args:
            usuario (User): Usuario que consulta

        Returns:
            int: Cantidad de mensajes no leídos
        """
        return self.obtener_mensajes_no_leidos(usuario).count()

    def marcar_todos_como_leidos(self, usuario):
        """
        Marca todos los mensajes como leídos para un usuario

        Args:
            usuario (User): Usuario que leyó los mensajes
        """
        mensajes_no_leidos = self.obtener_mensajes_no_leidos(usuario)
        count = mensajes_no_leidos.update(
            leido=True,
            leido_en=timezone.now()
        )

        if count > 0:
            logger.debug(f"✅ {count} mensajes marcados como leídos para {usuario.email}")

        return count

    def obtener_ultimo_mensaje(self):
        """
        Obtiene el último mensaje del chat

        Returns:
            Mensaje: Último mensaje o None
        """
        return self.mensajes.filter(eliminado=False).order_by('-creado_en').first()

    def enviar_mensaje_sistema(self, contenido):
        """
        Envía un mensaje automático del sistema

        Args:
            contenido (str): Texto del mensaje

        Returns:
            Mensaje: Mensaje creado
        """
        mensaje = Mensaje.objects.create(
            chat=self,
            tipo=TipoMensaje.SISTEMA,
            contenido=contenido,
            leido=True  # Mensajes del sistema se marcan como leídos
        )

        logger.info(f"🤖 Mensaje del sistema enviado en chat {self.id}")
        return mensaje

    @classmethod
    def crear_chats_para_pedido(cls, pedido):
        """
        ✅ MÉTODO PRINCIPAL: Crea los chats necesarios según el tipo de pedido

        Args:
            pedido (Pedido): Instancia del pedido

        Returns:
            dict: {'cliente_repartidor': Chat, 'proveedor_repartidor': Chat o None}
        """
        if not pedido.repartidor:
            raise ValidationError('El pedido debe tener un repartidor asignado')

        chats_creados = {}

        # ✅ SIEMPRE SE CREA: Chat Cliente ↔ Repartidor
        chat_cliente, created = cls.objects.get_or_create(
            tipo=TipoChat.PEDIDO_CLIENTE,
            pedido=pedido,
            defaults={
                'titulo': f"Pedido #{pedido.pk} - Entrega"
            }
        )

        if created:
            chat_cliente.participantes.add(pedido.cliente.user, pedido.repartidor.user)
            chat_cliente.enviar_mensaje_sistema(
                f"Chat iniciado para el pedido #{pedido.pk}. "
                f"El repartidor {pedido.repartidor.user.get_full_name()} está en camino."
            )
            logger.info(f"✅ Chat Cliente↔Repartidor creado para pedido {pedido.pk}")

        chats_creados['cliente_repartidor'] = chat_cliente

        # ✅ CONDICIONAL: Chat Proveedor ↔ Repartidor (solo si hay proveedor)
        if pedido.proveedor:
            chat_proveedor, created = cls.objects.get_or_create(
                tipo=TipoChat.PEDIDO_PROVEEDOR,
                pedido=pedido,
                defaults={
                    'titulo': f"Pedido #{pedido.pk} - Recojo"
                }
            )

            if created:
                chat_proveedor.participantes.add(
                    pedido.proveedor.user,
                    pedido.repartidor.user
                )
                chat_proveedor.enviar_mensaje_sistema(
                    f"Chat iniciado para coordinación de recojo del pedido #{pedido.pk}."
                )
                logger.info(f"✅ Chat Proveedor↔Repartidor creado para pedido {pedido.pk}")

            chats_creados['proveedor_repartidor'] = chat_proveedor
        else:
            chats_creados['proveedor_repartidor'] = None
            logger.info(f"ℹ️ Pedido {pedido.pk} es DIRECTO, no se crea chat con proveedor")

        return chats_creados

    @classmethod
    def crear_chat_soporte(cls, proveedor, admin_user=None):
        """
        Crea un chat de soporte para un proveedor

        Args:
            proveedor (Proveedor): Proveedor que solicita soporte
            admin_user (User): Admin asignado (opcional)

        Returns:
            Chat: Chat de soporte creado
        """
        # Buscar admin disponible si no se especifica
        if not admin_user:
            admin_user = User.objects.filter(rol='admin', is_active=True).first()
            if not admin_user:
                raise ValidationError('No hay administradores disponibles')

        chat = cls.objects.create(
            tipo=TipoChat.SOPORTE,
            proveedor=proveedor,
            titulo=f"Soporte - {proveedor.nombre}"
        )

        chat.participantes.add(proveedor.user, admin_user)
        chat.enviar_mensaje_sistema(
            f"Chat de soporte iniciado. {admin_user.get_full_name()} te ayudará."
        )

        logger.info(f"✅ Chat de soporte creado para proveedor {proveedor.id}")
        return chat

    @property
    def tiene_mensajes_sin_leer(self):
        """Verifica si hay mensajes sin leer"""
        return self.mensajes.filter(leido=False, eliminado=False).exists()

    @property
    def total_mensajes(self):
        """Total de mensajes en el chat"""
        return self.mensajes.filter(eliminado=False).count()

    @property
    def otros_participantes(self):
        """Lista de participantes (para mostrar en UI)"""
        return self.participantes.all()


# ============================================
# 💬 MODELO: MENSAJE
# ============================================

class Mensaje(models.Model):
    """
    Mensaje individual dentro de un chat

    ✅ SOPORTA:
    - Texto
    - Imágenes (fotos, comprobantes)
    - Audios (notas de voz tipo WhatsApp)
    - Mensajes del sistema
    """

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    chat = models.ForeignKey(
        Chat,
        on_delete=models.CASCADE,
        related_name='mensajes',
        verbose_name='Chat'
    )

    remitente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='mensajes_enviados',
        verbose_name='Remitente',
        help_text='Null para mensajes del sistema'
    )

    tipo = models.CharField(
        max_length=20,
        choices=TipoMensaje.choices,
        default=TipoMensaje.TEXTO,
        verbose_name='Tipo de Mensaje',
        db_index=True
    )

    # ============================================
    # CONTENIDO
    # ============================================

    contenido = models.TextField(
        blank=True,
        verbose_name='Contenido del Mensaje',
        help_text='Texto del mensaje'
    )

    # Archivo adjunto (imagen o audio)
    archivo = models.FileField(
        upload_to='chat/archivos/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Archivo Adjunto',
        validators=[
            FileExtensionValidator(['jpg', 'jpeg', 'png', 'webp', 'mp3', 'ogg', 'm4a', 'wav']),
            validar_tamano_archivo
        ],
        help_text='Imagen o audio (máx 10MB)'
    )

    # Metadata del archivo
    nombre_archivo = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Nombre Original del Archivo'
    )

    tamano_archivo = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Tamaño del Archivo (bytes)'
    )

    duracion_audio = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Duración del Audio (segundos)',
        help_text='Solo para mensajes de audio'
    )

    # ============================================
    # ESTADO
    # ============================================

    leido = models.BooleanField(
        default=False,
        verbose_name='Mensaje Leído',
        db_index=True
    )

    leido_en = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Fecha de Lectura'
    )

    eliminado = models.BooleanField(
        default=False,
        verbose_name='Mensaje Eliminado',
        help_text='Soft delete',
        db_index=True
    )

    # ============================================
    # AUDITORÍA
    # ============================================

    creado_en = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Envío',
        db_index=True
    )

    actualizado_en = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Modificación'
    )

    class Meta:
        db_table = 'mensajes'
        verbose_name = 'Mensaje'
        verbose_name_plural = 'Mensajes'
        ordering = ['creado_en']
        indexes = [
            models.Index(fields=['chat', 'creado_en']),
            models.Index(fields=['chat', 'leido', 'eliminado']),
            models.Index(fields=['remitente']),
            models.Index(fields=['tipo']),
            models.Index(fields=['-creado_en']),
        ]

    def __str__(self):
        if self.tipo == TipoMensaje.SISTEMA:
            return f"[SISTEMA] {self.contenido[:50]}"

        remitente_email = self.remitente.email if self.remitente else 'Sistema'

        if self.tipo == TipoMensaje.TEXTO:
            preview = self.contenido[:50] if self.contenido else ''
            return f"{remitente_email}: {preview}"
        elif self.tipo == TipoMensaje.IMAGEN:
            return f"{remitente_email}: [Imagen]"
        elif self.tipo == TipoMensaje.AUDIO:
            duracion = f"{self.duracion_audio}s" if self.duracion_audio else ''
            return f"{remitente_email}: [Audio {duracion}]"

        return f"Mensaje {self.id}"

    # ============================================
    # ✅ VALIDACIONES
    # ============================================

    def clean(self):
        """Validaciones personalizadas"""
        super().clean()

        errors = {}

        # Mensaje de texto debe tener contenido
        if self.tipo == TipoMensaje.TEXTO:
            if not self.contenido or not self.contenido.strip():
                errors['contenido'] = 'El mensaje de texto no puede estar vacío'

        # Mensaje de imagen debe tener archivo
        if self.tipo == TipoMensaje.IMAGEN:
            if not self.archivo:
                errors['archivo'] = 'Debes adjuntar una imagen'
            elif self.archivo:
                ext = self.archivo.name.split('.')[-1].lower()
                if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                    errors['archivo'] = f'Formato de imagen no válido: {ext}'

        # Mensaje de audio debe tener archivo
        if self.tipo == TipoMensaje.AUDIO:
            if not self.archivo:
                errors['archivo'] = 'Debes adjuntar un audio'
            elif self.archivo:
                ext = self.archivo.name.split('.')[-1].lower()
                if ext not in ['mp3', 'ogg', 'm4a', 'wav']:
                    errors['archivo'] = f'Formato de audio no válido: {ext}'

        # Mensaje del sistema no necesita remitente
        if self.tipo == TipoMensaje.SISTEMA and self.remitente:
            errors['remitente'] = 'Los mensajes del sistema no deben tener remitente'

        # Mensajes normales SÍ necesitan remitente
        if self.tipo != TipoMensaje.SISTEMA and not self.remitente:
            errors['remitente'] = 'El mensaje debe tener un remitente'

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        """Override save para extraer metadata del archivo"""
        self.full_clean()

        # Extraer nombre y tamaño del archivo
        if self.archivo:
            self.nombre_archivo = self.archivo.name.split('/')[-1]
            self.tamano_archivo = self.archivo.size

        super().save(*args, **kwargs)

    # ============================================
    # ✅ MÉTODOS DE NEGOCIO
    # ============================================

    def marcar_como_leido(self):
        """Marca el mensaje como leído"""
        if not self.leido:
            self.leido = True
            self.leido_en = timezone.now()
            self.save(update_fields=['leido', 'leido_en', 'actualizado_en'])
            logger.debug(f"✅ Mensaje {self.id} marcado como leído")

    def eliminar_mensaje(self):
        """Soft delete del mensaje"""
        self.eliminado = True
        self.save(update_fields=['eliminado', 'actualizado_en'])
        logger.info(f"🗑️ Mensaje {self.id} eliminado (soft delete)")

    def restaurar_mensaje(self):
        """Restaura un mensaje eliminado"""
        self.eliminado = False
        self.save(update_fields=['eliminado', 'actualizado_en'])
        logger.info(f"♻️ Mensaje {self.id} restaurado")

    @property
    def es_imagen(self):
        """Verifica si es un mensaje de imagen"""
        return self.tipo == TipoMensaje.IMAGEN

    @property
    def es_audio(self):
        """Verifica si es un mensaje de audio"""
        return self.tipo == TipoMensaje.AUDIO

    @property
    def es_sistema(self):
        """Verifica si es un mensaje del sistema"""
        return self.tipo == TipoMensaje.SISTEMA

    @property
    def url_archivo(self):
        """Retorna la URL del archivo si existe"""
        if self.archivo:
            return self.archivo.url
        return None

    @property
    def tamano_archivo_mb(self):
        """Retorna el tamaño del archivo en MB"""
        if self.tamano_archivo:
            return round(self.tamano_archivo / (1024 * 1024), 2)
        return 0
