# administradores/management/commands/crear_superadmin.py
"""
Management command para crear un superadministrador completo

Uso:
    python manage.py crear_superadmin

Crea automáticamente:
- User con rol ADMINISTRADOR + is_superuser=True
- Perfil de Administrador con TODOS los permisos
- Acceso al Django Admin (/admin/)
- Acceso al Panel de Administración personalizado
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from django.core.exceptions import ValidationError
from authentication.models import User
from administradores.models import Administrador
from usuarios.models import Perfil
import logging
import getpass

logger = logging.getLogger("administradores")


class Command(BaseCommand):
    help = "Crea un superadministrador con acceso completo al sistema"

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS("╔═══════════════════════════════════════╗")
        )
        self.stdout.write(
            self.style.SUCCESS("║   CREAR SUPERADMINISTRADOR            ║")
        )
        self.stdout.write(
            self.style.SUCCESS("╚═══════════════════════════════════════╝\n")
        )

        try:
            # 1. Pedir datos básicos
            email = self._pedir_email()
            password = self._pedir_password()
            nombre = self._pedir_texto("Nombre", requerido=True)
            apellido = self._pedir_texto("Apellido", requerido=True)
            celular = self._pedir_celular()
            cargo = self._pedir_texto(
                "Cargo", requerido=False, default="Administrador General"
            )
            departamento = self._pedir_texto(
                "Departamento", requerido=False, default="Operaciones"
            )

            # 2. Generar username automáticamente
            username = email.split("@")[0]
            if User.objects.filter(username=username).exists():
                username = f"{username}_{User.objects.count() + 1}"

            # 3. Mostrar resumen
            self._mostrar_resumen(
                email, username, nombre, apellido, celular, cargo, departamento
            )

            # 4. Confirmar creación
            if not self._confirmar():
                self.stdout.write(self.style.ERROR("\n❌ Operación cancelada"))
                return

            # 5. Crear administrador
            with transaction.atomic():
                admin_creado = self._crear_superadmin(
                    email=email,
                    username=username,
                    password=password,
                    nombre=nombre,
                    apellido=apellido,
                    celular=celular,
                    cargo=cargo,
                    departamento=departamento,
                )

            # 6. Mostrar resultado
            self._mostrar_exito(admin_creado)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.ERROR("\n\n❌ Operación cancelada por el usuario")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n❌ Error: {str(e)}"))
            logger.error(f"Error creando superadmin: {e}", exc_info=True)

    # ==========================================
    # MÉTODOS AUXILIARES
    # ==========================================

    def _pedir_email(self):
        """Pide y valida el email"""
        while True:
            email = input("📧 Email (para login): ").strip().lower()

            if not email:
                self.stdout.write(self.style.ERROR("❌ El email es obligatorio"))
                continue

            if "@" not in email or "." not in email:
                self.stdout.write(self.style.ERROR("❌ Email inválido"))
                continue

            if User.objects.filter(email=email).exists():
                self.stdout.write(
                    self.style.ERROR(f"❌ El email {email} ya está registrado")
                )
                continue

            return email

    def _pedir_password(self):
        """Pide y valida la contraseña"""
        while True:
            password = getpass.getpass("🔒 Contraseña (mínimo 8 caracteres): ")

            if len(password) < 8:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ La contraseña debe tener al menos 8 caracteres"
                    )
                )
                continue

            password_confirm = getpass.getpass("🔒 Confirmar contraseña: ")

            if password != password_confirm:
                self.stdout.write(self.style.ERROR("❌ Las contraseñas no coinciden"))
                continue

            return password

    def _pedir_texto(self, campo, requerido=True, default=None):
        """Pide un texto genérico"""
        while True:
            valor = input(
                f'📝 {campo}{f" (opcional, default: {default})" if default else ""}: '
            ).strip()

            if not valor and default:
                return default

            if not valor and requerido:
                self.stdout.write(self.style.ERROR(f"❌ {campo} es obligatorio"))
                continue

            return valor or ""

    def _pedir_celular(self):
        """Pide y valida el celular"""
        while True:
            celular = input("📱 Celular (formato: 09XXXXXXXX): ").strip()

            if not celular.startswith("09") or len(celular) != 10:
                self.stdout.write(
                    self.style.ERROR(
                        "❌ Celular debe comenzar con 09 y tener 10 dígitos"
                    )
                )
                continue

            if not celular.isdigit():
                self.stdout.write(
                    self.style.ERROR("❌ Celular solo debe contener números")
                )
                continue

            if User.objects.filter(celular=celular).exists():
                self.stdout.write(
                    self.style.ERROR(f"❌ El celular {celular} ya está registrado")
                )
                continue

            return celular

    def _mostrar_resumen(
        self, email, username, nombre, apellido, celular, cargo, departamento
    ):
        """Muestra el resumen de datos antes de crear"""
        self.stdout.write(
            self.style.WARNING("\n╔═══════════════════════════════════════╗")
        )
        self.stdout.write(
            self.style.WARNING("║   RESUMEN DEL SUPERADMINISTRADOR     ║")
        )
        self.stdout.write(
            self.style.WARNING("╚═══════════════════════════════════════╝")
        )
        self.stdout.write(f"📧 Email:        {email}")
        self.stdout.write(f"👤 Username:     {username}")
        self.stdout.write(f"🙋 Nombre:       {nombre} {apellido}")
        self.stdout.write(f"📱 Celular:      {celular}")
        self.stdout.write(f"💼 Cargo:        {cargo}")
        self.stdout.write(f"🏢 Departamento: {departamento}")
        self.stdout.write(self.style.SUCCESS("\n✅ PERMISOS: ACCESO TOTAL AL SISTEMA"))

    def _confirmar(self):
        """Pide confirmación"""
        respuesta = input("\n¿Crear este superadministrador? (s/n): ").lower()
        return respuesta == "s"

    def _crear_superadmin(
        self, email, username, password, nombre, apellido, celular, cargo, departamento
    ):
        """Crea el superadministrador completo"""

        # 1. Crear User
        user = User.objects.create_user(
            email=email,
            username=username,
            password=password,
            first_name=nombre,
            last_name=apellido,
            celular=celular,
            rol=User.RolChoices.ADMINISTRADOR,
            rol_activo=User.RolChoices.ADMINISTRADOR,
            is_staff=True,  # ✅ Acceso al Django Admin
            is_superuser=True,  # ✅ Permisos totales
            is_active=True,
            verificado=True,
            terminos_aceptados=True,
        )

        logger.info(f"✅ User creado: {user.email} (ID: {user.id})")

        # 2. Crear perfil Administrador
        admin = Administrador.objects.create(
            user=user,
            cargo=cargo,
            departamento=departamento,
            puede_gestionar_usuarios=True,
            puede_gestionar_pedidos=True,
            puede_gestionar_proveedores=True,
            puede_gestionar_repartidores=True,
            puede_gestionar_rifas=True,
            puede_ver_reportes=True,
            puede_configurar_sistema=True,  # ✅ Super Admin
            puede_gestionar_solicitudes=True,
            activo=True,
        )

        logger.info(f"✅ Administrador creado: {admin.id}")

        # 3. Verificar que existe Perfil (debería crearse automáticamente por señal)
        try:
            perfil = user.perfil_usuario
            logger.info(f"✅ Perfil usuario ya existe: {perfil.id}")
        except Perfil.DoesNotExist:
            # Crear manualmente si no existe
            perfil = Perfil.objects.create(user=user)
            logger.warning(f"⚠️ Perfil creado manualmente: {perfil.id}")

        return {
            "user": user,
            "admin": admin,
            "perfil": perfil,
        }

    def _mostrar_exito(self, admin_creado):
        """Muestra mensaje de éxito"""
        user = admin_creado["user"]
        admin = admin_creado["admin"]

        self.stdout.write(
            self.style.SUCCESS("\n╔═══════════════════════════════════════╗")
        )
        self.stdout.write(
            self.style.SUCCESS("║   ✅ SUPERADMINISTRADOR CREADO       ║")
        )
        self.stdout.write(
            self.style.SUCCESS("╚═══════════════════════════════════════╝")
        )
        self.stdout.write(f"\n👤 Usuario ID:       {user.id}")
        self.stdout.write(f"🔑 Administrador ID: {admin.id}")
        self.stdout.write(f"📧 Email:            {user.email}")
        self.stdout.write(f"💼 Cargo:            {admin.cargo}")

        self.stdout.write(self.style.SUCCESS("\n✅ ACCESOS HABILITADOS:"))
        self.stdout.write("   • Django Admin:  /admin/")
        self.stdout.write("   • Panel Admin:   (tu frontend React)")
        self.stdout.write("   • API completa")

        self.stdout.write(self.style.WARNING("\n⚠️  IMPORTANTE:"))
        self.stdout.write("   • Guarda estas credenciales en un lugar seguro")
        self.stdout.write("   • Cambia la contraseña después del primer login")

        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 ¡Listo! Ya puedes iniciar sesión con {user.email}\n"
            )
        )
