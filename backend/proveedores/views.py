from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import transaction
from .models import Proveedor
from authentication.models import User  # ✅ Correcto
from .serializers import (
    ProveedorSerializer,
    ProveedorListSerializer,
    ProveedorUpdateSerializer,
    ProveedorAdminSerializer
)
from authentication.permissions import EsProveedor, EsAdministrador
import logging

logger = logging.getLogger('proveedores')


class ProveedorViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar proveedores con validación de propiedad

    ✅ MEJORAS IMPLEMENTADAS:
    - Validación de propiedad (usuario solo edita su proveedor)
    - Sincronización automática con User
    - Serializers diferenciados por acción
    - Endpoint personalizado mi_proveedor
    - Permisos granulares
    - Logging detallado

    Endpoints disponibles:
    - GET    /api/proveedores/              - Listar todos (filtrado por rol)
    - POST   /api/proveedores/              - Crear nuevo (admin only)
    - GET    /api/proveedores/{id}/         - Detalle de proveedor
    - PUT    /api/proveedores/{id}/         - Actualizar (owner o admin)
    - PATCH  /api/proveedores/{id}/         - Actualizar parcial (owner o admin)
    - DELETE /api/proveedores/{id}/         - Eliminar (admin only)

    Endpoints custom:
    - GET    /api/proveedores/mi_proveedor/      - Mi proveedor (proveedor only)
    - GET    /api/proveedores/activos/           - Solo activos
    - GET    /api/proveedores/abiertos/          - Abiertos ahora
    - GET    /api/proveedores/por_tipo/?tipo=    - Filtrar por tipo
    - POST   /api/proveedores/{id}/activar/      - Activar (admin only)
    - POST   /api/proveedores/{id}/desactivar/   - Desactivar (admin only)
    - POST   /api/proveedores/{id}/verificar/    - Verificar (admin only)
    """

    queryset = Proveedor.objects.select_related('user').all()
    serializer_class = ProveedorSerializer

    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]

    filterset_fields = ['tipo_proveedor', 'ciudad', 'activo', 'verificado']
    search_fields = ['nombre', 'ruc', 'direccion', 'ciudad', 'user__email']
    ordering_fields = ['nombre', 'created_at', 'comision_porcentaje']
    ordering = ['-created_at']

    # ============================================
    # ✅ PERMISOS DIFERENCIADOS POR ACCIÓN
    # ============================================
    def get_permissions(self):
        """
        Permisos granulares según la acción
        """
        if self.action in ['create', 'destroy']:
            # Solo admins pueden crear/eliminar proveedores
            return [IsAdminUser()]

        elif self.action in ['update', 'partial_update']:
            # Proveedor puede editar el suyo, admin puede editar todos
            return [IsAuthenticated()]

        elif self.action in ['activar', 'desactivar', 'verificar']:
            # Solo admins
            return [IsAdminUser()]

        elif self.action == 'mi_proveedor':
            # Solo proveedores autenticados
            return [IsAuthenticated(), EsProveedor()]

        else:
            # Listar, detalle: cualquier usuario autenticado
            return [IsAuthenticated()]

    # ============================================
    # ✅ SERIALIZER DIFERENCIADO POR ACCIÓN
    # ============================================
    def get_serializer_class(self):
        """
        Retorna el serializer apropiado según la acción
        """
        if self.action == 'list':
            return ProveedorListSerializer

        elif self.action in ['update', 'partial_update']:
            # Si es admin, puede usar el serializer completo
            if self.request.user.es_administrador():
                return ProveedorAdminSerializer
            return ProveedorUpdateSerializer

        elif self.request.user.es_administrador():
            return ProveedorAdminSerializer

        return ProveedorSerializer

    # ============================================
    # ✅ QUERYSET FILTRADO POR ROL
    # ============================================
    def get_queryset(self):
        """
        Filtra proveedores según el rol del usuario
        - Proveedor: solo ve el suyo
        - Admin: ve todos
        - Usuario/Repartidor: ve solo activos y verificados
        """
        queryset = super().get_queryset()
        user = self.request.user

        # Si es proveedor (no admin), solo ve el suyo
        if user.es_proveedor() and not user.es_administrador():
            queryset = queryset.filter(user=user)

        # Si es usuario regular o repartidor, solo ver activos y verificados
        elif user.es_usuario() or user.es_repartidor():
            queryset = queryset.filter(activo=True, verificado=True)

        # Filtrar por parámetros de query
        activos = self.request.query_params.get('activos', None)
        if activos == 'true':
            queryset = queryset.filter(activo=True)

        verificados = self.request.query_params.get('verificados', None)
        if verificados == 'true':
            queryset = queryset.filter(verificado=True)

        # Búsqueda general
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(nombre__icontains=search) |
                Q(ruc__icontains=search) |
                Q(ciudad__icontains=search) |
                Q(descripcion__icontains=search) |
                Q(user__email__icontains=search)
            )

        return queryset

    # ============================================
    # ✅ VALIDACIÓN DE PROPIEDAD EN UPDATE
    # ============================================
    def update(self, request, *args, **kwargs):
        """
        Actualiza proveedor con validación de propiedad y sincronización
        """
        proveedor = self.get_object()
        user = request.user

        # ✅ Verificar permisos de propiedad
        if not user.es_administrador():
            if not hasattr(user, 'proveedor') or user.proveedor != proveedor:
                logger.warning(
                    f"❌ Usuario {user.email} intentó editar proveedor {proveedor.id} sin permiso"
                )
                return Response(
                    {'error': 'No tienes permiso para editar este proveedor'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # ✅ Sincronizar campos críticos con User (solo admin puede cambiar email/celular)
        with transaction.atomic():
            # Si es admin y quiere cambiar email/teléfono, sincronizar con User
            if user.es_administrador() and proveedor.user:
                if 'email' in request.data:
                    proveedor.user.email = request.data['email']
                    proveedor.user.save(update_fields=['email'])
                    logger.info(f"✅ Email sincronizado: {request.data['email']}")

                if 'telefono' in request.data:
                    proveedor.user.celular = request.data['telefono']
                    proveedor.user.save(update_fields=['celular'])
                    logger.info(f"✅ Celular sincronizado: {request.data['telefono']}")

            # Actualizar proveedor
            response = super().update(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            logger.info(
                f"✅ Proveedor {proveedor.nombre} actualizado por {user.email}"
            )

        return response

    def partial_update(self, request, *args, **kwargs):
        """
        Actualización parcial con las mismas validaciones
        """
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    # ============================================
    # ✅ ENDPOINT: MI PROVEEDOR
    # ============================================
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mi_proveedor(self, request):
        """
        GET /api/proveedores/mi_proveedor/

        Obtiene el proveedor del usuario autenticado
        Solo accesible para usuarios con rol PROVEEDOR

        Response 200:
        {
            "id": 5,
            "nombre": "Mi Restaurante",
            "verificado": true,
            ...
        }

        Response 403: Usuario no es proveedor
        Response 404: Proveedor no encontrado
        """
        user = request.user

        # Verificar que es proveedor
        if not user.es_proveedor():
            return Response(
                {
                    'error': 'No eres un proveedor',
                    'rol_actual': user.rol
                },
                status=status.HTTP_403_FORBIDDEN
            )

        # Obtener proveedor vinculado
        try:
            proveedor = user.proveedor
            serializer = self.get_serializer(proveedor)

            logger.info(f"✅ Proveedor {user.email} consultó su perfil")

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Proveedor.DoesNotExist:
            logger.error(
                f"❌ Usuario {user.email} (rol PROVEEDOR) no tiene proveedor vinculado"
            )
            return Response(
                {
                    'error': 'No tienes un proveedor vinculado',
                    'detalle': 'Contacta con soporte para resolver este problema'
                },
                status=status.HTTP_404_NOT_FOUND
            )

    # ============================================
    # ✅ ENDPOINT: ACTIVOS
    # ============================================
    @action(detail=False, methods=['get'])
    def activos(self, request):
        """
        GET /api/proveedores/activos/

        Retorna solo proveedores activos
        Usuarios regulares: también deben estar verificados
        """
        queryset = self.get_queryset().filter(activo=True)

        # Si no es admin, también filtrar por verificados
        if not request.user.es_administrador():
            queryset = queryset.filter(verificado=True)

        # Paginación
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = ProveedorListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = ProveedorListSerializer(queryset, many=True, context={'request': request})

        logger.info(
            f"✅ Usuario {request.user.email} consultó proveedores activos ({queryset.count()})"
        )

        return Response({
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ ENDPOINT: ABIERTOS AHORA
    # ============================================
    @action(detail=False, methods=['get'])
    def abiertos(self, request):
        """
        GET /api/proveedores/abiertos/

        Retorna proveedores que están abiertos en este momento
        """
        queryset = self.get_queryset().filter(activo=True)

        if not request.user.es_administrador():
            queryset = queryset.filter(verificado=True)

        # Filtrar solo los que están abiertos
        abiertos = [p for p in queryset if p.esta_abierto()]

        serializer = ProveedorListSerializer(
            abiertos,
            many=True,
            context={'request': request}
        )

        logger.info(
            f"✅ Usuario {request.user.email} consultó proveedores abiertos ({len(abiertos)})"
        )

        return Response({
            'count': len(abiertos),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ ENDPOINT: POR TIPO
    # ============================================
    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """
        GET /api/proveedores/por_tipo/?tipo=restaurante

        Filtra proveedores por tipo
        Tipos válidos: restaurante, farmacia, supermercado, tienda, otro
        """
        tipo = request.query_params.get('tipo', None)

        if not tipo:
            return Response(
                {
                    'error': 'Debes especificar el parámetro "tipo"',
                    'tipos_validos': ['restaurante', 'farmacia', 'supermercado', 'tienda', 'otro']
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = self.get_queryset().filter(
            tipo_proveedor=tipo,
            activo=True
        )

        if not request.user.es_administrador():
            queryset = queryset.filter(verificado=True)

        serializer = ProveedorListSerializer(
            queryset,
            many=True,
            context={'request': request}
        )

        return Response({
            'tipo': tipo,
            'count': queryset.count(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ ENDPOINT: ACTIVAR (ADMIN ONLY)
    # ============================================
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def activar(self, request, pk=None):
        """
        POST /api/proveedores/{id}/activar/

        Activa un proveedor (solo administradores)
        """
        proveedor = self.get_object()
        proveedor.activo = True
        proveedor.save(update_fields=['activo'])

        logger.info(
            f"✅ Admin {request.user.email} activó proveedor {proveedor.nombre} (ID: {proveedor.id})"
        )

        return Response({
            'mensaje': f'Proveedor {proveedor.nombre} activado correctamente',
            'proveedor': ProveedorSerializer(proveedor, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ ENDPOINT: DESACTIVAR (ADMIN ONLY)
    # ============================================
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def desactivar(self, request, pk=None):
        """
        POST /api/proveedores/{id}/desactivar/

        Desactiva un proveedor (solo administradores)
        """
        proveedor = self.get_object()
        proveedor.activo = False
        proveedor.save(update_fields=['activo'])

        logger.info(
            f"⚠️ Admin {request.user.email} desactivó proveedor {proveedor.nombre} (ID: {proveedor.id})"
        )

        return Response({
            'mensaje': f'Proveedor {proveedor.nombre} desactivado correctamente',
            'proveedor': ProveedorSerializer(proveedor, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ ENDPOINT: VERIFICAR (ADMIN ONLY)
    # ============================================
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def verificar(self, request, pk=None):
        """
        POST /api/proveedores/{id}/verificar/

        Verifica un proveedor y su usuario vinculado (solo administradores)
        Sincroniza el estado de verificación en User y Proveedor
        """
        proveedor = self.get_object()

        with transaction.atomic():
            # Verificar proveedor
            proveedor.verificado = True
            proveedor.save(update_fields=['verificado'])

            # ✅ Sincronizar con User
            if proveedor.user:
                proveedor.user.verificado = True
                proveedor.user.save(update_fields=['verificado'])

        logger.info(
            f"✅ Admin {request.user.email} verificó proveedor {proveedor.nombre} "
            f"y usuario {proveedor.user.email if proveedor.user else 'N/A'}"
        )

        return Response({
            'mensaje': f'Proveedor {proveedor.nombre} verificado correctamente',
            'proveedor': ProveedorSerializer(proveedor, context={'request': request}).data
        }, status=status.HTTP_200_OK)

    # ============================================
    # ✅ OVERRIDE: CREATE (ADMIN ONLY)
    # ============================================
    def create(self, request, *args, **kwargs):
        """
        Crea un proveedor (solo admin)
        Logging detallado
        """
        response = super().create(request, *args, **kwargs)

        if response.status_code == status.HTTP_201_CREATED:
            logger.info(
                f"✅ Admin {request.user.email} creó proveedor: "
                f"{response.data.get('nombre')} (ID: {response.data.get('id')})"
            )

        return response

    # ============================================
    # ✅ OVERRIDE: DESTROY (ADMIN ONLY)
    # ============================================
    def destroy(self, request, *args, **kwargs):
        """
        Elimina un proveedor (solo admin)
        Logging de advertencia
        """
        proveedor = self.get_object()
        nombre = proveedor.nombre
        proveedor_id = proveedor.id
        user_email = proveedor.user.email if proveedor.user else 'N/A'

        response = super().destroy(request, *args, **kwargs)

        if response.status_code == status.HTTP_204_NO_CONTENT:
            logger.warning(
                f"⚠️ Admin {request.user.email} eliminó proveedor: "
                f"{nombre} (ID: {proveedor_id}, Usuario: {user_email})"
            )

        return response

    # ============================================
    # ✅ OVERRIDE: RETRIEVE (CON LOGGING)
    # ============================================
    def retrieve(self, request, *args, **kwargs):
        """
        Obtiene detalle de un proveedor
        """
        response = super().retrieve(request, *args, **kwargs)

        if response.status_code == status.HTTP_200_OK:
            proveedor_id = kwargs.get('pk')
            logger.debug(
                f"👁️ Usuario {request.user.email} consultó proveedor ID {proveedor_id}"
            )

        return response

# ============================================
# ✅ ENDPOINTS DE SINCRONIZACIÓN (ADMIN ONLY)
# ============================================

@action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
def sincronizar_todos(self, request):
    """
    POST /api/proveedores/sincronizar_todos/

    Sincroniza TODOS los proveedores con sus usuarios vinculados
    Solo administradores pueden ejecutar esta acción

    Response:
    {
        "total_proveedores": 50,
        "sincronizados": 35,
        "sin_usuario": 10,
        "sin_cambios": 5,
        "errores": 0,
        "detalles": [...]
    }
    """
    from django.db import transaction

    proveedores = self.get_queryset().filter(user__isnull=False)

    resultado = {
        'total_proveedores': proveedores.count(),
        'sincronizados': 0,
        'sin_usuario': Proveedor.objects.filter(user__isnull=True).count(),
        'sin_cambios': 0,
        'errores': 0,
        'detalles': []
    }

    with transaction.atomic():
        for proveedor in proveedores:
            try:
                # Intentar sincronizar
                cambios = proveedor.sincronizar_con_user()

                if cambios:
                    resultado['sincronizados'] += 1
                    resultado['detalles'].append({
                        'id': proveedor.id,
                        'nombre': proveedor.nombre,
                        'estado': 'sincronizado',
                        'cambios': True
                    })
                else:
                    resultado['sin_cambios'] += 1
                    resultado['detalles'].append({
                        'id': proveedor.id,
                        'nombre': proveedor.nombre,
                        'estado': 'sin_cambios',
                        'cambios': False
                    })

            except Exception as e:
                resultado['errores'] += 1
                resultado['detalles'].append({
                    'id': proveedor.id,
                    'nombre': proveedor.nombre,
                    'estado': 'error',
                    'error': str(e)
                })
                logger.error(
                    f"❌ Error sincronizando proveedor {proveedor.id}: {e}"
                )

    logger.info(
        f"✅ Admin {request.user.email} sincronizó proveedores: "
        f"{resultado['sincronizados']} exitosos, {resultado['errores']} errores"
    )

    return Response(resultado, status=status.HTTP_200_OK)


@action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
def sincronizar(self, request, pk=None):
    """
    POST /api/proveedores/{id}/sincronizar/

    Sincroniza un proveedor específico con su usuario

    Response:
    {
        "proveedor_id": 5,
        "nombre": "Restaurante El Buen Sabor",
        "sincronizado": true,
        "cambios": {
            "email": {"antes": "viejo@email.com", "despues": "nuevo@email.com"},
            "telefono": {"antes": "0998765432", "despues": "0987654321"}
        }
    }
    """
    proveedor = self.get_object()

    if not proveedor.user:
        return Response({
            'error': 'Este proveedor no tiene usuario vinculado',
            'proveedor_id': proveedor.id,
            'nombre': proveedor.nombre
        }, status=status.HTTP_400_BAD_REQUEST)

    # Guardar valores anteriores
    email_antes = proveedor.email
    telefono_antes = proveedor.telefono

    # Sincronizar
    cambios_realizados = proveedor.sincronizar_con_user()

    # Preparar respuesta con detalles
    resultado = {
        'proveedor_id': proveedor.id,
        'nombre': proveedor.nombre,
        'user_id': proveedor.user.id,
        'sincronizado': True,
        'cambios_realizados': cambios_realizados,
        'cambios': {}
    }

    if cambios_realizados:
        if email_antes != proveedor.email:
            resultado['cambios']['email'] = {
                'antes': email_antes,
                'despues': proveedor.email
            }

        if telefono_antes != proveedor.telefono:
            resultado['cambios']['telefono'] = {
                'antes': telefono_antes,
                'despues': proveedor.telefono
            }

        logger.info(
            f"✅ Admin {request.user.email} sincronizó proveedor {proveedor.id}"
        )
    else:
        resultado['mensaje'] = 'El proveedor ya estaba sincronizado'

    return Response(resultado, status=status.HTTP_200_OK)


@action(detail=False, methods=['get'], permission_classes=[IsAdminUser])
def estado_sincronizacion(self, request):
    """
    GET /api/proveedores/estado_sincronizacion/

    Obtiene un reporte del estado de sincronización de todos los proveedores

    Response:
    {
        "total_proveedores": 50,
        "con_usuario": 45,
        "sin_usuario": 5,
        "sincronizados": 40,
        "desincronizados": 5,
        "desincronizados_detalles": [...]
    }
    """
    from django.db.models import Q, F

    total = Proveedor.objects.count()
    con_usuario = Proveedor.objects.filter(user__isnull=False).count()
    sin_usuario = Proveedor.objects.filter(user__isnull=True).count()

    # Proveedores desincronizados
    desincronizados = Proveedor.objects.filter(
        user__isnull=False
    ).exclude(
        Q(email=F('user__email')) & Q(telefono=F('user__celular'))
    )

    desincronizados_detalles = []
    for proveedor in desincronizados:
        diferencias = []

        if proveedor.email != proveedor.user.email:
            diferencias.append({
                'campo': 'email',
                'proveedor': proveedor.email,
                'usuario': proveedor.user.email
            })

        if proveedor.telefono != proveedor.user.celular:
            diferencias.append({
                'campo': 'telefono',
                'proveedor': proveedor.telefono,
                'usuario': proveedor.user.celular
            })

        desincronizados_detalles.append({
            'id': proveedor.id,
            'nombre': proveedor.nombre,
            'user_id': proveedor.user.id,
            'user_email': proveedor.user.email,
            'diferencias': diferencias
        })

    resultado = {
        'total_proveedores': total,
        'con_usuario': con_usuario,
        'sin_usuario': sin_usuario,
        'sincronizados': con_usuario - desincronizados.count(),
        'desincronizados': desincronizados.count(),
        'desincronizados_detalles': desincronizados_detalles,
        'porcentaje_sincronizado': round(
            ((con_usuario - desincronizados.count()) / total * 100) if total > 0 else 0,
            2
        )
    }

    # Proveedores sin usuario (legacy)
    if sin_usuario > 0:
        proveedores_sin_user = Proveedor.objects.filter(user__isnull=True)[:10]
        resultado['sin_usuario_ejemplos'] = [
            {
                'id': p.id,
                'nombre': p.nombre,
                'ruc': p.ruc,
                'email': p.email,
                'telefono': p.telefono,
                'created_at': p.created_at
            }
            for p in proveedores_sin_user
        ]

    logger.info(
        f"📊 Admin {request.user.email} consultó estado de sincronización"
    )

    return Response(resultado, status=status.HTTP_200_OK)


@action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
def vincular_usuarios_legacy(self, request):
    """
    POST /api/proveedores/vincular_usuarios_legacy/

    Intenta vincular automáticamente proveedores sin usuario
    Busca coincidencias por email o RUC

    Body (opcional):
    {
        "modo": "email" | "ruc" | "ambos",
        "dry_run": true  // Si es true, solo simula sin guardar
    }

    Response:
    {
        "proveedores_sin_usuario": 10,
        "vinculados": 7,
        "no_encontrados": 3,
        "detalles": [...]
    }
    """
    from django.db.models import Q

    modo = request.data.get('modo', 'ambos')
    dry_run = request.data.get('dry_run', False)

    proveedores_sin_user = Proveedor.objects.filter(user__isnull=True)

    resultado = {
        'proveedores_sin_usuario': proveedores_sin_user.count(),
        'vinculados': 0,
        'no_encontrados': 0,
        'errores': 0,
        'dry_run': dry_run,
        'detalles': []
    }

    for proveedor in proveedores_sin_user:
        try:
            user_encontrado = None
            metodo_vinculacion = None

            # Buscar por email
            if modo in ['email', 'ambos'] and proveedor.email:
                try:
                    user_encontrado = User.objects.get(
                        email=proveedor.email,
                        rol='PROVEEDOR',
                        proveedor__isnull=True  # Que no tenga proveedor ya vinculado
                    )
                    metodo_vinculacion = 'email'
                except User.DoesNotExist:
                    pass
                except User.MultipleObjectsReturned:
                    resultado['detalles'].append({
                        'proveedor_id': proveedor.id,
                        'nombre': proveedor.nombre,
                        'estado': 'error',
                        'mensaje': 'Múltiples usuarios con ese email'
                    })
                    resultado['errores'] += 1
                    continue

            # Buscar por RUC si no encontró por email
            if not user_encontrado and modo in ['ruc', 'ambos'] and proveedor.ruc:
                try:
                    user_encontrado = User.objects.get(
                        ruc=proveedor.ruc,
                        rol='PROVEEDOR',
                        proveedor__isnull=True
                    )
                    metodo_vinculacion = 'ruc'
                except User.DoesNotExist:
                    pass
                except User.MultipleObjectsReturned:
                    resultado['detalles'].append({
                        'proveedor_id': proveedor.id,
                        'nombre': proveedor.nombre,
                        'estado': 'error',
                        'mensaje': 'Múltiples usuarios con ese RUC'
                    })
                    resultado['errores'] += 1
                    continue

            # Vincular si encontró
            if user_encontrado:
                if not dry_run:
                    proveedor.user = user_encontrado
                    proveedor.save()

                    # Sincronizar datos
                    proveedor.sincronizar_con_user()

                resultado['vinculados'] += 1
                resultado['detalles'].append({
                    'proveedor_id': proveedor.id,
                    'nombre': proveedor.nombre,
                    'user_id': user_encontrado.id,
                    'user_email': user_encontrado.email,
                    'estado': 'vinculado' if not dry_run else 'simulado',
                    'metodo': metodo_vinculacion
                })

                if not dry_run:
                    logger.info(
                        f"✅ Proveedor {proveedor.id} vinculado con User {user_encontrado.id} "
                        f"(método: {metodo_vinculacion})"
                    )
            else:
                resultado['no_encontrados'] += 1
                resultado['detalles'].append({
                    'proveedor_id': proveedor.id,
                    'nombre': proveedor.nombre,
                    'email': proveedor.email,
                    'ruc': proveedor.ruc,
                    'estado': 'no_encontrado',
                    'mensaje': 'No se encontró usuario coincidente'
                })

        except Exception as e:
            resultado['errores'] += 1
            resultado['detalles'].append({
                'proveedor_id': proveedor.id,
                'nombre': proveedor.nombre,
                'estado': 'error',
                'error': str(e)
            })
            logger.error(f"❌ Error vinculando proveedor {proveedor.id}: {e}")

    mensaje = (
        f"{'[DRY RUN] ' if dry_run else ''}Vinculación completada: "
        f"{resultado['vinculados']} vinculados, "
        f"{resultado['no_encontrados']} no encontrados, "
        f"{resultado['errores']} errores"
    )

    logger.info(f"📊 Admin {request.user.email}: {mensaje}")

    return Response(resultado, status=status.HTTP_200_OK)


@action(detail=False, methods=['post'], permission_classes=[IsAdminUser])
def forzar_sincronizacion(self, request):
    """
    POST /api/proveedores/forzar_sincronizacion/

    Fuerza sincronización bidireccional:
    - Si hay conflicto, prioriza datos de User (source of truth)
    - Actualiza tanto Proveedor como User si es necesario

    Body:
    {
        "direccion": "user_to_proveedor" | "proveedor_to_user" | "auto",
        "campo": "email" | "telefono" | "ambos",
        "proveedores_ids": [5, 12, 18]  // Opcional, si no se envía aplica a todos
    }

    Response:
    {
        "total_procesados": 45,
        "actualizados_proveedor": 30,
        "actualizados_user": 5,
        "sin_cambios": 10,
        "detalles": [...]
    }
    """
    from django.db import transaction

    direccion = request.data.get('direccion', 'user_to_proveedor')
    campo = request.data.get('campo', 'ambos')
    proveedores_ids = request.data.get('proveedores_ids', None)

    # Validar dirección
    if direccion not in ['user_to_proveedor', 'proveedor_to_user', 'auto']:
        return Response({
            'error': 'Dirección inválida',
            'direcciones_validas': ['user_to_proveedor', 'proveedor_to_user', 'auto']
        }, status=status.HTTP_400_BAD_REQUEST)

    # Obtener proveedores a procesar
    if proveedores_ids:
        proveedores = Proveedor.objects.filter(
            id__in=proveedores_ids,
            user__isnull=False
        )
    else:
        proveedores = Proveedor.objects.filter(user__isnull=False)

    resultado = {
        'total_procesados': proveedores.count(),
        'actualizados_proveedor': 0,
        'actualizados_user': 0,
        'sin_cambios': 0,
        'direccion': direccion,
        'campo': campo,
        'detalles': []
    }

    with transaction.atomic():
        for proveedor in proveedores:
            cambios = {
                'proveedor': False,
                'user': False,
                'campos': []
            }

            # Determinar dirección si es 'auto'
            if direccion == 'auto':
                # Priorizar User (más reciente)
                direccion_efectiva = 'user_to_proveedor'
            else:
                direccion_efectiva = direccion

            # Sincronizar según dirección
            if direccion_efectiva == 'user_to_proveedor':
                # User es source of truth
                if campo in ['email', 'ambos']:
                    if proveedor.email != proveedor.user.email:
                        proveedor.email = proveedor.user.email
                        cambios['proveedor'] = True
                        cambios['campos'].append('email')

                if campo in ['telefono', 'ambos']:
                    if proveedor.telefono != proveedor.user.celular:
                        proveedor.telefono = proveedor.user.celular
                        cambios['proveedor'] = True
                        cambios['campos'].append('telefono')

                if cambios['proveedor']:
                    proveedor.save(update_fields=['email', 'telefono'])

            elif direccion_efectiva == 'proveedor_to_user':
                # Proveedor es source of truth
                if campo in ['email', 'ambos']:
                    if proveedor.user.email != proveedor.email:
                        proveedor.user.email = proveedor.email
                        cambios['user'] = True
                        cambios['campos'].append('email')

                if campo in ['telefono', 'ambos']:
                    if proveedor.user.celular != proveedor.telefono:
                        proveedor.user.celular = proveedor.telefono
                        cambios['user'] = True
                        cambios['campos'].append('celular')

                if cambios['user']:
                    proveedor.user.save(update_fields=['email', 'celular'])

            # Contabilizar resultados
            if cambios['proveedor']:
                resultado['actualizados_proveedor'] += 1
            if cambios['user']:
                resultado['actualizados_user'] += 1
            if not cambios['proveedor'] and not cambios['user']:
                resultado['sin_cambios'] += 1

            resultado['detalles'].append({
                'proveedor_id': proveedor.id,
                'nombre': proveedor.nombre,
                'user_id': proveedor.user.id,
                'cambios': cambios
            })

    logger.info(
        f"🔄 Admin {request.user.email} forzó sincronización: "
        f"{resultado['actualizados_proveedor']} proveedores, "
        f"{resultado['actualizados_user']} usuarios actualizados"
    )

    return Response(resultado, status=status.HTTP_200_OK)
