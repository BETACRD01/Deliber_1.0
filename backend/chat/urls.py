# ============================================
# chat/urls.py
# ============================================

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatViewSet, MensajeViewSet

app_name = 'chat'

# Router para ViewSets
router = DefaultRouter()
router.register(r'chats', ChatViewSet, basename='chat')
router.register(r'mensajes', MensajeViewSet, basename='mensaje')

urlpatterns = [
    path('', include(router.urls)),
]

"""
✅ ENDPOINTS DISPONIBLES:

CHATS:
- GET    /api/chat/chats/                    - Listar chats del usuario
- GET    /api/chat/chats/{id}/               - Detalle de un chat
- POST   /api/chat/chats/soporte/            - Crear chat de soporte
- GET    /api/chat/chats/{id}/mensajes/      - Listar mensajes del chat
- POST   /api/chat/chats/{id}/mensajes/      - Enviar mensaje
- POST   /api/chat/chats/{id}/marcar-leidos/ - Marcar mensajes como leídos
- POST   /api/chat/chats/{id}/escribiendo/   - Indicar que está escribiendo
- POST   /api/chat/chats/{id}/cerrar/        - Cerrar chat (admin)

MENSAJES:
- GET    /api/chat/mensajes/{id}/            - Detalle de un mensaje
- POST   /api/chat/mensajes/{id}/marcar-leido/ - Marcar como leído
- DELETE /api/chat/mensajes/{id}/eliminar/   - Eliminar mensaje
"""
