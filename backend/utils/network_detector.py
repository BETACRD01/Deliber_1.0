"""
==========================================
ARCHIVO: backend/utils/network_detector.py
==========================================
Detector automático de red para Django Backend
Lee configuración desde .env y detecta la red actual automáticamente
"""

import socket
import logging
import os
from typing import Optional, List

logger = logging.getLogger(__name__)


class NetworkDetector:
    """Detector inteligente de configuración de red"""
    
    RED_POR_DEFECTO = 'CASA'
    
    @classmethod
    def _cargar_config_desde_env(cls) -> dict:
        """
        Carga la configuración de redes desde el archivo .env
        """
        return {
            'CASA': {
                'prefijo': os.getenv('RED_CASA_PREFIX', '192.168.1'),
                'ip_servidor': os.getenv('RED_CASA_IP', '192.168.1.5'),  # ✅ CORREGIDO: .4 → .5
                'descripcion': 'Red domestica WiFi'
            },
            'INSTITUCIONAL': {
                'prefijo': os.getenv('RED_INSTITUCIONAL_PREFIX', '172.16'),
                'ip_servidor': os.getenv('RED_INSTITUCIONAL_IP', '172.16.60.5'),  # ⚠️ Verificar cuando estés en esa red
                'descripcion': 'Red institucional'
            },
            'HOTSPOT': {
                'prefijo': os.getenv('RED_HOTSPOT_PREFIX', '192.168.137'),
                'ip_servidor': os.getenv('RED_HOTSPOT_IP', '192.168.137.1'),
                'descripcion': 'Hotspot movil'
            },
            'DOCKER': {
                'prefijo': '172.17',
                'ip_servidor': '0.0.0.0',
                'descripcion': 'Red Docker'
            }
        }
    
    @classmethod
    def obtener_ip_local(cls) -> Optional[str]:
        """
        Obtiene la IP local del servidor
        Usa multiples metodos para mayor confiabilidad
        """
        # Verificar si esta en modo manual
        connection_mode = os.getenv('CONNECTION_MODE', 'AUTO').upper()
        if connection_mode == 'MANUAL':
            manual_ip = os.getenv('MANUAL_SERVER_IP')
            if manual_ip:
                logger.info(f"Modo MANUAL: Usando IP configurada: {manual_ip}")
                return manual_ip
        
        # Metodo 1: Conectar a servidor externo (sin enviar datos)
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            if ip and not ip.startswith('127.'):
                logger.info(f"IP detectada (metodo socket): {ip}")
                return ip
        except Exception as e:
            logger.debug(f"Metodo socket fallo: {e}")
        
        # Metodo 2: Usar hostname
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            if ip and not ip.startswith('127.'):
                logger.info(f"IP detectada (metodo hostname): {ip}")
                return ip
        except Exception as e:
            logger.debug(f"Metodo hostname fallo: {e}")
        
        # Metodo 3: Verificar variable de entorno (para Docker)
        try:
            host_ip = socket.gethostbyname(socket.gethostname())
            if host_ip and not host_ip.startswith('127.'):
                logger.info(f"IP detectada (metodo gethostbyname): {host_ip}")
                return host_ip
        except Exception as e:
            logger.debug(f"Metodo gethostbyname fallo: {e}")
        
        logger.warning("No se pudo detectar IP local")
        return None
    
    @classmethod
    def detectar_red(cls) -> dict:
        """
        Detecta automaticamente la red actual
        Retorna diccionario con configuracion detectada
        """
        # Verificar si la deteccion automatica esta habilitada
        enable_detection = os.getenv('ENABLE_NETWORK_DETECTION', 'True').lower() == 'true'
        
        if not enable_detection:
            logger.info("Deteccion automatica deshabilitada en .env")
            redes = cls._cargar_config_desde_env()
            red_default = redes[cls.RED_POR_DEFECTO]
            return {
                'nombre': cls.RED_POR_DEFECTO,
                'ip_local': red_default['ip_servidor'],
                'ip_servidor': red_default['ip_servidor'],
                'prefijo': red_default['prefijo'],
                'valida': False,
                'descripcion': f"{red_default['descripcion']} (modo estatico)",
                'modo': 'STATIC'
            }
        
        # Verificar modo de conexion
        connection_mode = os.getenv('CONNECTION_MODE', 'AUTO').upper()
        
        if connection_mode == 'DOCKER':
            logger.info("Modo DOCKER detectado")
            return {
                'nombre': 'DOCKER',
                'ip_local': '0.0.0.0',
                'ip_servidor': '0.0.0.0',
                'prefijo': '172.17',
                'valida': True,
                'descripcion': 'Red Docker',
                'modo': 'DOCKER'
            }
        
        # Obtener IP local
        ip_local = cls.obtener_ip_local()
        redes = cls._cargar_config_desde_env()
        
        if not ip_local:
            logger.warning("Usando configuracion por defecto")
            red_default = redes[cls.RED_POR_DEFECTO]
            return {
                'nombre': cls.RED_POR_DEFECTO,
                'ip_local': '127.0.0.1',
                'ip_servidor': red_default['ip_servidor'],
                'prefijo': red_default['prefijo'],
                'valida': False,
                'descripcion': red_default['descripcion'],
                'modo': 'FALLBACK'
            }
        
        # Buscar coincidencia con redes conocidas
        for nombre_red, config in redes.items():
            prefijo = config['prefijo']
            if ip_local.startswith(prefijo):
                logger.info(f"Red detectada: {nombre_red} - {config['descripcion']}")
                return {
                    'nombre': nombre_red,
                    'ip_local': ip_local,
                    'ip_servidor': config['ip_servidor'],
                    'prefijo': prefijo,
                    'valida': True,
                    'descripcion': config['descripcion'],
                    'modo': 'AUTO'
                }
        
        # Red desconocida - usar IP detectada
        logger.warning(f"Red desconocida: {ip_local}")
        prefijo = '.'.join(ip_local.split('.')[:3])
        return {
            'nombre': 'DESCONOCIDA',
            'ip_local': ip_local,
            'ip_servidor': ip_local,
            'prefijo': prefijo,
            'valida': True,
            'descripcion': 'Red no identificada',
            'modo': 'AUTO'
        }
    
    @classmethod
    def obtener_allowed_hosts(cls, config_red: dict) -> List[str]:
        """
        Genera lista de ALLOWED_HOSTS segun la red detectada
        """
        hosts = [
            'localhost',
            '127.0.0.1',
            '0.0.0.0',
            'backend',
            config_red['ip_local'],
            config_red['ip_servidor'],
            '*.local',
        ]
        
        # Agregar todas las IPs de redes conocidas desde .env
        redes = cls._cargar_config_desde_env()
        for config in redes.values():
            hosts.append(config['ip_servidor'])
        
        # Agregar hosts adicionales desde ALLOWED_HOSTS en .env
        env_hosts = os.getenv('ALLOWED_HOSTS', '')
        if env_hosts:
            hosts.extend(env_hosts.split(','))
        
        # Eliminar duplicados, None y vacios
        return list(set(filter(lambda x: x and x.strip(), hosts)))
    
    @classmethod
    def obtener_cors_origins(cls, config_red: dict, puerto: int = 8000) -> List[str]:
        """
        Genera lista de CORS_TRUSTED_ORIGINS segun la red
        """
        origins = [
            f'http://localhost:{puerto}',
            f'http://127.0.0.1:{puerto}',
        ]
        
        # Agregar IP del servidor detectado
        if config_red['ip_servidor'] not in ['0.0.0.0', 'backend']:
            origins.append(f"http://{config_red['ip_servidor']}:{puerto}")
        
        # Agregar todas las IPs de redes conocidas
        redes = cls._cargar_config_desde_env()
        for config in redes.values():
            if config['ip_servidor'] not in ['0.0.0.0', 'backend']:
                origins.append(f"http://{config['ip_servidor']}:{puerto}")
        
        # Agregar origenes extra desde .env
        extra_origins = os.getenv('CSRF_TRUSTED_ORIGINS_EXTRA', '')
        if extra_origins:
            origins.extend(extra_origins.split(','))
        
        # Eliminar duplicados
        return list(set(filter(lambda x: x and x.strip(), origins)))
    
    @classmethod
    def obtener_frontend_url(cls, config_red: dict, puerto: int = 8000) -> str:
        """
        Obtiene la URL del frontend segun la red detectada
        """
        # Si hay FRONTEND_URL en .env, usarla
        frontend_url = os.getenv('FRONTEND_URL')
        if frontend_url:
            return frontend_url
        
        # Generar automaticamente
        if config_red['ip_servidor'] == '0.0.0.0':
            return f"http://localhost:{puerto}"
        
        return f"http://{config_red['ip_servidor']}:{puerto}"
    
    @classmethod
    def imprimir_info(cls, config_red: dict):
        """
        Muestra informacion de la red detectada en consola
        """
        print("\n" + "="*70)
        print("DELIBER - DETECCION AUTOMATICA DE RED")
        print("="*70)
        print(f"Red detectada: {config_red['nombre']}")
        print(f"Descripcion: {config_red['descripcion']}")
        print(f"Modo de deteccion: {config_red.get('modo', 'AUTO')}")
        print(f"IP local del servidor: {config_red['ip_local']}")
        print(f"IP de escucha: {config_red['ip_servidor']}")
        print(f"Prefijo de red: {config_red['prefijo']}.*")
        
        if not config_red['valida']:
            print("\nADVERTENCIA: Red no detectada, usando configuracion fallback")
        
        # Mostrar configuracion de .env relevante
        print("\n" + "-"*70)
        print("Configuracion desde .env:")
        print(f"  ENABLE_NETWORK_DETECTION: {os.getenv('ENABLE_NETWORK_DETECTION', 'True')}")
        print(f"  CONNECTION_MODE: {os.getenv('CONNECTION_MODE', 'AUTO')}")
        print(f"  BACKEND_PORT: {os.getenv('BACKEND_PORT', '8000')}")
        
        print("="*70 + "\n")


# ==========================================
# INSTANCIA GLOBAL (SINGLETON)
# ==========================================
_config_red_global: Optional[dict] = None


def obtener_config_red() -> dict:
    """
    Obtiene la configuracion de red (se ejecuta solo una vez)
    """
    global _config_red_global
    if _config_red_global is None:
        _config_red_global = NetworkDetector.detectar_red()
        NetworkDetector.imprimir_info(_config_red_global)
    return _config_red_global


def refrescar_config_red() -> dict:
    """
    Fuerza una nueva deteccion de red
    """
    global _config_red_global
    logger.info("Re-detectando red...")
    _config_red_global = NetworkDetector.detectar_red()
    NetworkDetector.imprimir_info(_config_red_global)
    return _config_red_global