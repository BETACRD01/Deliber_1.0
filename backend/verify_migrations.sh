#!/bin/bash

# 🔍 SCRIPT COMPLETO DE VERIFICACIÓN DE MIGRACIONES

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           VERIFICACIÓN COMPLETA DE MIGRACIONES                ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# ============================================================
# 1. MOSTRAR ESTADO DE MIGRACIONES
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1️⃣  ESTADO DE MIGRACIONES POR APP"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec backend python manage.py showmigrations

# ============================================================
# 2. VERIFICAR TABLA solicitudes_cambio_rol EN BD
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2️⃣  VERIFICAR TABLA EN POSTGRESQL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📊 Columnas de solicitudes_cambio_rol:"
docker compose exec -T db psql -U postgres -d deliber -c "
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'solicitudes_cambio_rol'
ORDER BY ordinal_position;
"

# ============================================================
# 3. VERIFICAR TABLA usuarios_perfil EN BD
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3️⃣  VERIFICAR TABLA usuarios_perfil"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "
SELECT 
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'usuarios_perfil'
ORDER BY ordinal_position
LIMIT 10;
"

# ============================================================
# 4. VERIFICAR CONSTRAINTS Y ÍNDICES
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4️⃣  CONSTRAINTS E ÍNDICES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "
-- Constraints
SELECT constraint_name, constraint_type, table_name
FROM information_schema.table_constraints
WHERE table_name = 'solicitudes_cambio_rol';

-- Índices
SELECT indexname FROM pg_indexes WHERE tablename = 'solicitudes_cambio_rol';
"

# ============================================================
# 5. VERIFICAR RELACIONES FOREIGNKEY
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5️⃣  RELACIONES FOREIGNKEY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'solicitudes_cambio_rol' AND tc.constraint_type = 'FOREIGN KEY';
"

# ============================================================
# 6. VERIFICAR DATOS EN TABLA
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6️⃣  DATOS ACTUALES EN TABLA"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "
SELECT COUNT(*) as total_solicitudes FROM solicitudes_cambio_rol;
SELECT estado, COUNT(*) FROM solicitudes_cambio_rol GROUP BY estado;
"

# ============================================================
# 7. VERIFICAR CONTENIDO DE django_migrations
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "7️⃣  MIGRACIONES APLICADAS (django_migrations)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "
SELECT app, name, applied
FROM django_migrations
WHERE app = 'usuarios'
ORDER BY applied DESC;
"

# ============================================================
# 8. VERIFICAR POSIBLES CAMBIOS PENDIENTES
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "8️⃣  DETECTAR CAMBIOS PENDIENTES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec backend python manage.py makemigrations --dry-run usuarios

# ============================================================
# 9. VERIFICAR INTEGRIDAD DE BD
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "9️⃣  VERIFICAR INTEGRIDAD DE BD (Django Check)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec backend python manage.py check

# ============================================================
# 10. LISTAR TODAS LAS TABLAS
# ============================================================
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔟  TODAS LAS TABLAS EN LA BD"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T db psql -U postgres -d deliber -c "\dt" | grep -E "usuarios|solicitud|perfil"

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                  VERIFICACIÓN COMPLETADA                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"