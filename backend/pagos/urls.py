# pagos/urls.py
"""
Configuración de URLs para el módulo de Pagos.

✅ CARACTERÍSTICAS:
- Rutas REST con Django REST Framework Router
- Endpoints de ViewSets
- Webhooks de pasarelas
- Documentación automática de API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MetodoPagoViewSet,
    PagoViewSet,
    TransaccionViewSet,
    EstadisticasPagoViewSet,
    # ✅ CORREGIDO: Importar funciones en lugar de clase
    stripe_webhook,
    kushki_webhook,
    paymentez_webhook,
)

# ==========================================================
# 🔗 ROUTER DE DRF
# ==========================================================

router = DefaultRouter()

# Registrar ViewSets
router.register(r'metodos', MetodoPagoViewSet, basename='metodo-pago')
router.register(r'pagos', PagoViewSet, basename='pago')
router.register(r'transacciones', TransaccionViewSet, basename='transaccion')
router.register(r'estadisticas-diarias', EstadisticasPagoViewSet, basename='estadistica-pago')

# ==========================================================
# 📍 URLS PRINCIPALES
# ==========================================================

app_name = 'pagos'

urlpatterns = [
    # ==========================================================
    # API REST - ViewSets
    # ==========================================================
    # Incluye todas las rutas del router
    # GET    /api/pagos/metodos/
    # GET    /api/pagos/metodos/{id}/
    # GET    /api/pagos/metodos/disponibles/
    #
    # GET    /api/pagos/pagos/
    # POST   /api/pagos/pagos/
    # GET    /api/pagos/pagos/{id}/
    # PATCH  /api/pagos/pagos/{id}/actualizar_estado/
    # POST   /api/pagos/pagos/{id}/reembolsar/
    # POST   /api/pagos/pagos/{id}/verificar/
    # GET    /api/pagos/pagos/{id}/transacciones/
    # GET    /api/pagos/pagos/{id}/resumen/
    # GET    /api/pagos/pagos/mis_pagos/
    # GET    /api/pagos/pagos/pendientes_verificacion/
    # GET    /api/pagos/pagos/estadisticas/
    # GET    /api/pagos/pagos/del_dia/
    #
    # GET    /api/pagos/transacciones/
    # GET    /api/pagos/transacciones/{id}/
    #
    # GET    /api/pagos/estadisticas-diarias/
    # POST   /api/pagos/estadisticas-diarias/recalcular/
    path('', include(router.urls)),

    # ==========================================================
    # 🔗 WEBHOOKS - Pasarelas de Pago
    # ==========================================================
    # ✅ CORREGIDO: Usar funciones directamente
    path(
        'webhook/stripe/',
        stripe_webhook,
        name='webhook-stripe'
    ),
    path(
        'webhook/kushki/',
        kushki_webhook,
        name='webhook-kushki'
    ),
    path(
        'webhook/paymentez/',
        paymentez_webhook,
        name='webhook-paymentez'
    ),
]

# ==========================================================
# 📚 DOCUMENTACIÓN DE ENDPOINTS
# ==========================================================
"""
ENDPOINTS DISPONIBLES:

╔══════════════════════════════════════════════════════════════════════╗
║                      MÉTODOS DE PAGO                               ║
╚══════════════════════════════════════════════════════════════════════╝

GET     /api/pagos/metodos/
        Lista todos los métodos de pago activos
        Permisos: IsAuthenticated

GET     /api/pagos/metodos/{id}/
        Detalle de un método de pago
        Permisos: IsAuthenticated

GET     /api/pagos/metodos/disponibles/
        Lista solo métodos disponibles actualmente
        Permisos: IsAuthenticated


╔══════════════════════════════════════════════════════════════════════╗
║                           PAGOS                                    ║
╚══════════════════════════════════════════════════════════════════════╝

GET     /api/pagos/pagos/
        Lista pagos del usuario (admin ve todos)
        Permisos: IsOwnerOrAdmin
        Filtros: estado, metodo_pago__tipo, creado_en
        Búsqueda: referencia, pedido__id, notas
        Ordenamiento: creado_en, monto, estado

POST    /api/pagos/pagos/
        Crea un nuevo pago para un pedido
        Permisos: IsAuthenticated
        Body: {
            "pedido_id": 1,
            "metodo_pago_id": 1,
            "monto": 50.00,
            "tarjeta_token": "tok_xxx",  // Para tarjetas
            "transferencia_banco": "Pichincha",  // Para transferencias
            "transferencia_numero_operacion": "12345",
            "transferencia_comprobante_file": <file>,
            "metadata": {},
            "notas": ""
        }

GET     /api/pagos/pagos/{id}/
        Detalle completo de un pago
        Permisos: IsOwnerOrAdmin

PATCH   /api/pagos/pagos/{id}/actualizar_estado/
        Actualiza el estado del pago
        Permisos: CanVerifyPayments (Admin)
        Body: {
            "estado": "completado",
            "motivo": "Verificado manualmente",
            "pasarela_respuesta": {}
        }

POST    /api/pagos/pagos/{id}/reembolsar/
        Procesa un reembolso total o parcial
        Permisos: CanVerifyPayments (Admin)
        Body: {
            "monto": 25.00,  // null = reembolso total
            "motivo": "Cliente insatisfecho"
        }

POST    /api/pagos/pagos/{id}/verificar/
        Verifica y completa una transferencia bancaria
        Permisos: CanVerifyPayments (Admin)
        Body: {
            "notas": "Comprobante verificado"
        }

GET     /api/pagos/pagos/{id}/transacciones/
        Historial de transacciones del pago
        Permisos: IsOwnerOrAdmin

GET     /api/pagos/pagos/{id}/resumen/
        Resumen rápido del pago
        Permisos: IsOwnerOrAdmin

GET     /api/pagos/pagos/mis_pagos/
        Lista todos los pagos del usuario actual
        Permisos: IsAuthenticated

GET     /api/pagos/pagos/pendientes_verificacion/
        Lista pagos pendientes de verificación manual
        Permisos: IsAdminUser

GET     /api/pagos/pagos/estadisticas/
        Estadísticas generales de pagos
        Permisos: IsAdminUser
        Query Params:
            - fecha_inicio: YYYY-MM-DD
            - fecha_fin: YYYY-MM-DD

GET     /api/pagos/pagos/del_dia/
        Pagos y estadísticas del día actual
        Permisos: IsAdminUser


╔══════════════════════════════════════════════════════════════════════╗
║                       TRANSACCIONES                                ║
╚══════════════════════════════════════════════════════════════════════╝

GET     /api/pagos/transacciones/
        Lista transacciones (usuario ve solo sus transacciones)
        Permisos: IsAuthenticated
        Filtros: tipo, exitosa, creado_en
        Ordenamiento: creado_en, monto

GET     /api/pagos/transacciones/{id}/
        Detalle de una transacción
        Permisos: IsAuthenticated


╔══════════════════════════════════════════════════════════════════════╗
║                   ESTADÍSTICAS DIARIAS                             ║
╚══════════════════════════════════════════════════════════════════════╝

GET     /api/pagos/estadisticas-diarias/
        Lista estadísticas diarias
        Permisos: IsAdminUser

GET     /api/pagos/estadisticas-diarias/{id}/
        Detalle de estadísticas de un día
        Permisos: IsAdminUser

POST    /api/pagos/estadisticas-diarias/recalcular/
        Recalcula estadísticas de un día
        Permisos: IsAdminUser
        Body: {
            "fecha": "2025-01-15"  // Opcional, default: hoy
        }


╔══════════════════════════════════════════════════════════════════════╗
║                    WEBHOOKS EXTERNOS                               ║
╚══════════════════════════════════════════════════════════════════════╝

POST    /api/pagos/webhook/stripe/
        Webhook para notificaciones de Stripe
        Permisos: None (público, validado por firma)

POST    /api/pagos/webhook/kushki/
        Webhook para notificaciones de Kushki
        Permisos: None (público, validado por firma)

POST    /api/pagos/webhook/paymentez/
        Webhook para notificaciones de Paymentez
        Permisos: None (público, validado por firma)


╔══════════════════════════════════════════════════════════════════════╗
║                     EJEMPLOS DE USO                                ║
╚══════════════════════════════════════════════════════════════════════╝

1. CREAR PAGO CON EFECTIVO:
   POST /api/pagos/pagos/
   {
       "pedido_id": 1,
       "metodo_pago_id": 1,
       "monto": 50.00
   }

2. CREAR PAGO CON TRANSFERENCIA:
   POST /api/pagos/pagos/
   Content-Type: multipart/form-data
   {
       "pedido_id": 1,
       "metodo_pago_id": 2,
       "monto": 50.00,
       "transferencia_banco": "Banco Pichincha",
       "transferencia_numero_operacion": "123456789",
       "transferencia_comprobante_file": <archivo>
   }

3. CREAR PAGO CON TARJETA:
   POST /api/pagos/pagos/
   {
       "pedido_id": 1,
       "metodo_pago_id": 3,
       "monto": 50.00,
       "tarjeta_token": "tok_1234567890",
       "tarjeta_ultimos_digitos": "4242",
       "tarjeta_marca": "Visa"
   }

4. VERIFICAR TRANSFERENCIA:
   POST /api/pagos/pagos/5/verificar/
   {
       "notas": "Comprobante verificado correctamente"
   }

5. PROCESAR REEMBOLSO TOTAL:
   POST /api/pagos/pagos/5/reembolsar/
   {
       "motivo": "Pedido cancelado por el cliente"
   }

6. PROCESAR REEMBOLSO PARCIAL:
   POST /api/pagos/pagos/5/reembolsar/
   {
       "monto": 25.00,
       "motivo": "Devolución parcial por producto faltante"
   }

7. OBTENER MIS PAGOS:
   GET /api/pagos/pagos/mis_pagos/

8. OBTENER ESTADÍSTICAS DEL MES:
   GET /api/pagos/pagos/estadisticas/?fecha_inicio=2025-01-01&fecha_fin=2025-01-31

9. VER PAGOS PENDIENTES DE VERIFICACIÓN:
   GET /api/pagos/pagos/pendientes_verificacion/

10. RECALCULAR ESTADÍSTICAS:
    POST /api/pagos/estadisticas-diarias/recalcular/
    {
        "fecha": "2025-01-15"
    }


╔══════════════════════════════════════════════════════════════════════╗
║                    CÓDIGOS DE RESPUESTA                            ║
╚══════════════════════════════════════════════════════════════════════╝

200 OK                  - Operación exitosa
201 Created             - Recurso creado
400 Bad Request         - Datos inválidos
401 Unauthorized        - No autenticado
403 Forbidden           - Sin permisos
404 Not Found           - Recurso no encontrado
500 Internal Server     - Error del servidor


╔══════════════════════════════════════════════════════════════════════╗
║                        FILTROS                                     ║
╚══════════════════════════════════════════════════════════════════════╝

Pagos:
    ?estado=completado
    ?metodo_pago__tipo=efectivo
    ?creado_en__date=2025-01-15
    ?creado_en__gte=2025-01-01
    ?creado_en__lte=2025-01-31
    ?search=ABC123
    ?ordering=-creado_en
    ?ordering=monto

Transacciones:
    ?tipo=pago
    ?exitosa=true
    ?creado_en__date=2025-01-15
    ?ordering=-creado_en
"""
