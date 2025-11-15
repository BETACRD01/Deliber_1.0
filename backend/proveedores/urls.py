from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProveedorViewSet

router = DefaultRouter()
router.register(r'proveedores', ProveedorViewSet, basename='proveedor')

app_name = 'proveedores'

urlpatterns = [
    path('', include(router.urls)),
]