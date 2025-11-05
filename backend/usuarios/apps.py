# usuarios/apps.py

from django.apps import AppConfig


class UsuariosConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'usuarios'
    verbose_name = 'Gestión de Usuarios'
    
    def ready(self):
        """
        Importa las señales cuando la app está lista
        """
        import usuarios.models  # Esto carga las señales definidas en models.py