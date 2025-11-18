import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { dashboardAPI, proveedoresAPI, usuariosAPI } from '../../services/api';
import { AuthContext } from '../../context/AuthContext';
import { AlertTriangle, CheckCircle2 } from 'lucide-react';

export function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useContext(AuthContext);
  
  const [stats, setStats] = useState(null);
  const [alertas, setAlertas] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [refreshing, setRefreshing] = useState(false);

  // Estados para indicadores personalizados
  const [solicitudesPendientes, setSolicitudesPendientes] = useState(0);
  const [proveedoresPendientes, setProveedoresPendientes] = useState(0);
  const [usuariosNormales, setUsuariosNormales] = useState(0);

  useEffect(() => {
    cargarDatos();
  }, []);

  const cargarDatos = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }
      
      // Cargar estadísticas principales
      try {
        const statsRes = await dashboardAPI.estadisticas();
        setStats(statsRes.data);
      } catch (err) {
        console.error('Error cargando estadísticas:', err);
        setStats({
          usuarios: { total: 0, activos: 0 },
          proveedores: { total: 0, pendientes: 0 },
          repartidores: { total: 0, disponibles: 0 },
          pedidos: { total: 0, hoy: 0 },
          financiero: { ingresos_totales: 0, ganancia_app_total: 0 },
          solicitudes: { pendientes: 0 }
        });
      }
      
      // Cargar alertas del sistema
      try {
        const alertasRes = await dashboardAPI.alertas();
        setAlertas(alertasRes.data.alertas || []);
      } catch (err) {
        console.error('Error cargando alertas:', err);
        setAlertas([]);
      }

      // Cargar solicitudes pendientes
      try {
        const solRes = await dashboardAPI.alertas();
        const solicitudesPend = solRes.data?.solicitudes_pendientes || stats?.solicitudes?.pendientes || 0;
        setSolicitudesPendientes(solicitudesPend);
      } catch (err) {
        console.error('Error cargando solicitudes pendientes:', err);
        setSolicitudesPendientes(0);
      }

      // Cargar proveedores pendientes
      try {
        const provRes = await proveedoresAPI.pendientes();
        const count = Array.isArray(provRes.data) ? provRes.data.length : provRes.data?.count || 0;
        setProveedoresPendientes(count);
      } catch (err) {
        console.error('Error cargando proveedores pendientes:', err);
        setProveedoresPendientes(0);
      }

      // Cargar usuarios normales
      try {
        const usuRes = await usuariosAPI.estadisticas();
        const usuariosNorm = usuRes.data?.usuarios_normales || usuRes.data?.sin_rol || 0;
        setUsuariosNormales(usuariosNorm);
      } catch (err) {
        console.error('Error cargando usuarios normales:', err);
        setUsuariosNormales(0);
      }
      
      setError('');
    } catch (err) {
      setError('Error al cargar datos del dashboard');
      console.error(err);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  // Determinar si hay alertas críticas
  const hayAlertasCriticas = solicitudesPendientes > 0 || proveedoresPendientes > 0 || usuariosNormales > 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-blue-500 border-t-white rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-400 text-lg">Cargando dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950">
      {/* HEADER */}
      <header className="bg-slate-900/70 backdrop-blur-xl border-b border-slate-800 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 flex items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600">
                <span className="text-white font-bold text-lg">📊</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white">Deliber Admin</h1>
                <p className="text-sm text-slate-400">Panel de Administración</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <button
                onClick={() => cargarDatos(true)}
                disabled={refreshing}
                className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 disabled:opacity-50 transition-colors"
                title="Actualizar datos"
              >
                <span className={`text-xl ${refreshing ? 'animate-spin' : ''}`}>🔄</span>
              </button>

              <div className="text-right hidden sm:block">
                <p className="text-sm font-medium text-white">{user?.nombre || 'Administrador'}</p>
                <p className="text-xs text-slate-400">{user?.email}</p>
              </div>

              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 bg-red-600/20 hover:bg-red-600/30 border border-red-500/40 text-red-300 rounded-lg transition-colors"
              >
                <span className="text-lg">🚪</span>
                <span className="hidden sm:inline">Salir</span>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* CONTENIDO PRINCIPAL */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

        {error && (
          <div className="bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-xl mb-6">
            <div className="flex items-center gap-2">
              <span className="text-lg">⚠️</span>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* 🔴 ALERTAS CRÍTICAS - SECCIÓN NUEVA */}
        {hayAlertasCriticas && (
          <div className="mb-8 space-y-3">
            <div className="flex items-center gap-2">
              <AlertTriangle className="text-orange-400" size={24} />
              <h2 className="text-lg font-bold text-white">Alertas Críticas</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Solicitudes Pendientes */}
              {solicitudesPendientes > 0 && (
                <div 
                  onClick={() => navigate("/admin/solicitudes")}
                  className="bg-gradient-to-br from-yellow-600/20 to-orange-600/20 border-2 border-yellow-500/50 rounded-2xl p-4 cursor-pointer hover:border-yellow-400 transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                      <span className="text-xl">📋</span>
                      Solicitudes Pendientes
                    </h3>
                    <span className="text-2xl font-bold text-yellow-400">{solicitudesPendientes}</span>
                  </div>
                  <p className="text-yellow-300/80 text-sm">Haz clic para revisar y gestionar</p>
                </div>
              )}

              {/* Proveedores Pendientes */}
              {proveedoresPendientes > 0 && (
                <div 
                  onClick={() => navigate("/admin/proveedores")}
                  className="bg-gradient-to-br from-cyan-600/20 to-blue-600/20 border-2 border-cyan-500/50 rounded-2xl p-4 cursor-pointer hover:border-cyan-400 transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                      <span className="text-xl">🏪</span>
                      Proveedores Pendientes
                    </h3>
                    <span className="text-2xl font-bold text-cyan-400">{proveedoresPendientes}</span>
                  </div>
                  <p className="text-cyan-300/80 text-sm">Requieren verificación</p>
                </div>
              )}

              {/* Usuarios Normales */}
              {usuariosNormales > 0 && (
                <div 
                  onClick={() => navigate("/admin/usuarios")}
                  className="bg-gradient-to-br from-purple-600/20 to-pink-600/20 border-2 border-purple-500/50 rounded-2xl p-4 cursor-pointer hover:border-purple-400 transition-all group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-white font-semibold flex items-center gap-2">
                      <span className="text-xl">👤</span>
                      Usuarios Normales
                    </h3>
                    <span className="text-2xl font-bold text-purple-400">{usuariosNormales}</span>
                  </div>
                  <p className="text-purple-300/80 text-sm">Sin rol asignado</p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ESTADÍSTICAS PRINCIPALES */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6 mb-8">

          {/* Usuarios */}
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 hover:border-blue-500/40 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-600/20 rounded-xl group-hover:bg-blue-600/30 transition-colors text-2xl">👥</div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">{stats?.usuarios?.total || 0}</p>
                <p className="text-sm text-slate-400">Total</p>
              </div>
            </div>
            <h3 className="text-slate-300 font-medium mb-1">Usuarios</h3>
            <p className="text-xs text-slate-500">Activos: {stats?.usuarios?.activos || 0}</p>
          </div>

          {/* Proveedores */}
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 hover:border-green-500/40 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-600/20 rounded-xl group-hover:bg-green-600/30 transition-colors text-2xl">🏪</div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">{stats?.proveedores?.total || 0}</p>
                <p className="text-sm text-slate-400">Total</p>
              </div>
            </div>
            <h3 className="text-slate-300 font-medium mb-1">Proveedores</h3>
            <p className="text-xs text-slate-500">Pendientes: {stats?.proveedores?.pendientes || 0}</p>
          </div>

          {/* Repartidores */}
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 hover:border-purple-500/40 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-600/20 rounded-xl group-hover:bg-purple-600/30 transition-colors text-2xl">🚚</div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">{stats?.repartidores?.total || 0}</p>
                <p className="text-sm text-slate-400">Total</p>
              </div>
            </div>
            <h3 className="text-slate-300 font-medium mb-1">Repartidores</h3>
            <p className="text-xs text-slate-500">Disponibles: {stats?.repartidores?.disponibles || 0}</p>
          </div>

          {/* Pedidos */}
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 hover:border-orange-500/40 transition-all group">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-orange-600/20 rounded-xl group-hover:bg-orange-600/30 transition-colors text-2xl">🛒</div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">{stats?.pedidos?.total || 0}</p>
                <p className="text-sm text-slate-400">Total</p>
              </div>
            </div>
            <h3 className="text-slate-300 font-medium mb-1">Pedidos</h3>
            <p className="text-xs text-slate-500">Hoy: {stats?.pedidos?.hoy || 0}</p>
          </div>

          {/* Solicitudes de Rol */}
          <div
            className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6 hover:border-pink-500/40 transition-all group cursor-pointer"
            onClick={() => navigate("/admin/solicitudes")}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-pink-600/20 rounded-xl group-hover:bg-pink-600/30 transition-colors text-2xl">
                📋
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold text-white">
                  {stats?.solicitudes?.pendientes || 0}
                </p>
                <p className="text-sm text-slate-400">Pendientes</p>
              </div>
            </div>
            <h3 className="text-slate-300 font-medium mb-1">Solicitudes Rol</h3>
            <p className="text-xs text-slate-500">Ver y gestionar solicitudes</p>
          </div>
        </div>

        {/* FINANCIERO */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-green-600/20 rounded-xl text-3xl">💰</div>
              <div>
                <h3 className="text-slate-400 text-sm font-medium">Ingresos Totales</h3>
                <p className="text-3xl font-bold text-white mt-1">
                  ${stats?.financiero?.ingresos_totales?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-blue-600/20 rounded-xl text-3xl">📈</div>
              <div>
                <h3 className="text-slate-400 text-sm font-medium">Ganancia App</h3>
                <p className="text-3xl font-bold text-white mt-1">
                  ${stats?.financiero?.ganancia_app_total?.toFixed(2) || '0.00'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ALERTAS DEL SISTEMA */}
        {alertas.length > 0 && (
          <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="text-xl">⚠️</span>
              <h2 className="text-lg font-bold text-white">Alertas del Sistema</h2>
            </div>
            
            <div className="space-y-3">
              {alertas.map((alerta, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border-l-4 ${
                    alerta.nivel === 'danger'
                      ? 'bg-red-500/10 border-red-500'
                      : alerta.nivel === 'warning'
                      ? 'bg-yellow-500/10 border-yellow-500'
                      : 'bg-blue-500/10 border-blue-500'
                  }`}
                >
                  <p className={`font-medium ${
                    alerta.nivel === 'danger'
                      ? 'text-red-300'
                      : alerta.nivel === 'warning'
                      ? 'text-yellow-300'
                      : 'text-blue-300'
                  }`}>
                    {alerta.mensaje}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}