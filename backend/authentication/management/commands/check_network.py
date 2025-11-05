"""
==========================================
ARCHIVO: backend/authentication/management/commands/check_network.py
==========================================
Comando Django para verificar la configuración de red actual
Uso: python manage.py check_network
"""

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Verifica y muestra la configuración de red detectada'

    def handle(self, *args, **options):
        self.stdout.write("\n" + "="*70)
        self.stdout.write(self.style.SUCCESS("🌐 VERIFICACIÓN DE RED - DELIBER BACKEND"))
        self.stdout.write("="*70 + "\n")
        
        try:
            from utils.network_detector import obtener_config_red, NetworkDetector
            
            config_red = obtener_config_red()
            
            self.stdout.write(self.style.SUCCESS(f"✅ Red detectada: {config_red['nombre']}"))
            self.stdout.write(f"📝 Descripción: {config_red['descripcion']}")
            self.stdout.write(f"📍 IP Local: {config_red['ip_local']}")
            self.stdout.write(f"🔗 IP Servidor: {config_red['ip_servidor']}")
            self.stdout.write(f"🌐 Prefijo: {config_red['prefijo']}.*")
            
            if not config_red['valida']:
                self.stdout.write(self.style.WARNING(
                    "\n⚠️  Red no válida, usando configuración fallback"
                ))
            
            # Mostrar ALLOWED_HOSTS
            self.stdout.write("\n" + "-"*70)
            self.stdout.write(self.style.SUCCESS("📋 ALLOWED_HOSTS configurados:"))
            allowed_hosts = NetworkDetector.obtener_allowed_hosts(config_red)
            for host in allowed_hosts:
                self.stdout.write(f"  • {host}")
            
            # Mostrar CORS_ORIGINS
            self.stdout.write("\n" + "-"*70)
            self.stdout.write(self.style.SUCCESS("🔐 CORS_TRUSTED_ORIGINS:"))
            cors_origins = NetworkDetector.obtener_cors_origins(config_red, puerto=8000)
            for origin in cors_origins:
                self.stdout.write(f"  • {origin}")
            
            # Verificar configuración actual de Django
            self.stdout.write("\n" + "-"*70)
            self.stdout.write(self.style.SUCCESS("⚙️  Configuración Django actual:"))
            self.stdout.write(f"  DEBUG: {settings.DEBUG}")
            self.stdout.write(f"  ALLOWED_HOSTS: {len(settings.ALLOWED_HOSTS)} hosts")
            self.stdout.write(f"  CSRF_TRUSTED_ORIGINS: {len(settings.CSRF_TRUSTED_ORIGINS)} orígenes")
            
            if hasattr(settings, 'CORS_ALLOWED_ORIGINS'):
                self.stdout.write(f"  CORS_ALLOWED_ORIGINS: {len(settings.CORS_ALLOWED_ORIGINS)} orígenes")
            elif settings.CORS_ALLOW_ALL_ORIGINS:
                self.stdout.write(f"  CORS_ALLOW_ALL_ORIGINS: True (modo desarrollo)")
            
            # Información de base de datos
            db_config = settings.DATABASES['default']
            self.stdout.write(f"\n  Database: {db_config['NAME']}")
            self.stdout.write(f"  DB Host: {db_config['HOST']}")
            
            # Redis
            if hasattr(settings, 'REDIS_URL'):
                self.stdout.write(f"  Redis: {settings.REDIS_URL}")
            
            self.stdout.write("\n" + "="*70)
            self.stdout.write(self.style.SUCCESS("✅ Verificación completada"))
            self.stdout.write("="*70 + "\n")
            
        except ImportError:
            self.stdout.write(self.style.ERROR(
                "❌ Error: network_detector.py no encontrado en utils/"
            ))
            self.stdout.write(self.style.WARNING(
                "   Crea el archivo: backend/utils/network_detector.py"
            ))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))