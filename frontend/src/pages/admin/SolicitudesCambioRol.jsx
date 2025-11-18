import React, { useEffect, useState } from "react";
import { solicitudesRolAPI } from "../../services/api";
import { Check, X, Loader2, UserCog, Trash2, AlertTriangle, RotateCcw } from "lucide-react";

export function SolicitudesCambioRol() {
  const [solicitudes, setSolicitudes] = useState([]);
  const [detalle, setDetalle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [procesando, setProcesando] = useState(false);
  const [error, setError] = useState("");

  // Estados para modales
  const [modalAbierto, setModalAbierto] = useState(false);
  const [tipoAccion, setTipoAccion] = useState(null); // 'aceptar', 'rechazar', 'revertir'
  const [motivo, setMotivo] = useState("");
  const [modalEliminar, setModalEliminar] = useState(false);
  const [confirmacionEliminar, setConfirmacionEliminar] = useState("");

  useEffect(() => {
    cargarSolicitudes();
  }, []);

  const cargarSolicitudes = async () => {
    try {
      setLoading(true);
      const res = await solicitudesRolAPI.adminListar();
      setSolicitudes(res.data.results || res.data);
      setError("");
    } catch (err) {
      console.error(err);
      setError("Error obteniendo solicitudes");
    } finally {
      setLoading(false);
    }
  };

  const verDetalle = async (sol) => {
    try {
      setDetalle(null);
      setError("");
      
      const res = await solicitudesRolAPI.adminDetalle(sol.id || sol.uuid || sol.pk);
      setDetalle(res.data);
    } catch (err) {
      console.error("Error cargando detalle:", err);
      
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      "No se pudo cargar el detalle";
      
      setError(errorMsg);
    }
  };

  // ========================================
  // MODALES ACEPTAR/RECHAZAR/REVERTIR
  // ========================================
  const abrirModalAceptar = () => {
    setTipoAccion("aceptar");
    setMotivo("");
    setError("");
    setModalAbierto(true);
  };

  const abrirModalRechazar = () => {
    setTipoAccion("rechazar");
    setMotivo("");
    setError("");
    setModalAbierto(true);
  };

  const abrirModalRevertir = () => {
    setTipoAccion("revertir");
    setMotivo("");
    setError("");
    setModalAbierto(true);
  };

  const cerrarModal = () => {
    setModalAbierto(false);
    setTipoAccion(null);
    setMotivo("");
    setError("");
  };

  const confirmarAceptar = async () => {
    try {
      setProcesando(true);
      setError("");

      const data = {};
      if (motivo.trim()) {
        data.motivo_respuesta = motivo.trim();
      }
      
      await solicitudesRolAPI.aceptar(detalle.id, data);
      
      await cargarSolicitudes();
      setDetalle(null);
      cerrarModal();
    } catch (err) {
      console.error("Error aceptando solicitud:", err);
      
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      "No se pudo aceptar la solicitud";
      
      setError(errorMsg);
    } finally {
      setProcesando(false);
    }
  };

  const confirmarRechazar = async () => {
    try {
      setProcesando(true);
      setError("");

      const data = {};
      if (motivo.trim()) {
        data.motivo_respuesta = motivo.trim();
      }
      
      await solicitudesRolAPI.rechazar(detalle.id, data);
      
      await cargarSolicitudes();
      setDetalle(null);
      cerrarModal();
    } catch (err) {
      console.error("Error rechazando solicitud:", err);
      
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      "No se pudo rechazar la solicitud";
      
      setError(errorMsg);
    } finally {
      setProcesando(false);
    }
  };

  const confirmarRevertir = async () => {
    if (!motivo.trim() || motivo.trim().length < 10) {
      setError("El motivo debe tener al menos 10 caracteres");
      return;
    }

    try {
      setProcesando(true);
      setError("");

      const data = {
        motivo_reversion: motivo.trim()
      };
      
      await solicitudesRolAPI.revertir(detalle.id, data);
      
      await cargarSolicitudes();
      setDetalle(null);
      cerrarModal();
    } catch (err) {
      console.error("Error revirtiendo solicitud:", err);
      
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      "No se pudo revertir la solicitud";
      
      setError(errorMsg);
    } finally {
      setProcesando(false);
    }
  };

  // ========================================
  // MODAL ELIMINAR
  // ========================================
  const abrirModalEliminar = () => {
    setConfirmacionEliminar("");
    setError("");
    setModalEliminar(true);
  };

  const cerrarModalEliminar = () => {
    setModalEliminar(false);
    setConfirmacionEliminar("");
    setError("");
  };

  const confirmarEliminar = async () => {
    if (confirmacionEliminar !== "ELIMINAR") {
      setError("Debes escribir ELIMINAR para confirmar");
      return;
    }

    try {
      setProcesando(true);
      setError("");

      await solicitudesRolAPI.eliminar(detalle.id);
      
      await cargarSolicitudes();
      setDetalle(null);
      cerrarModalEliminar();
    } catch (err) {
      console.error("Error eliminando solicitud:", err);
      
      const errorMsg = err.response?.data?.error || 
                      err.response?.data?.detail || 
                      "No se pudo eliminar la solicitud";
      
      setError(errorMsg);
    } finally {
      setProcesando(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-12 h-12 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="bg-slate-950 min-h-screen py-10 px-4">
      <div className="max-w-6xl mx-auto">

        {/* TÍTULO */}
        <div className="flex items-center gap-3 mb-10">
          <div className="p-3 bg-blue-600/20 rounded-xl">
            <UserCog className="text-blue-400" size={30} />
          </div>
          <h1 className="text-3xl text-white font-bold">
            Solicitudes de Cambio de Rol
          </h1>
        </div>

        {/* ERROR GLOBAL */}
        {error && !modalAbierto && !modalEliminar && (
          <div className="bg-red-500/10 text-red-300 border border-red-500/40 px-4 py-3 rounded-xl mb-6">
            ⚠️ {error}
          </div>
        )}

        {/* LISTADO PRINCIPAL */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* LISTA IZQUIERDA */}
          <div className="space-y-4">
            {solicitudes.length === 0 && (
              <p className="text-slate-400">No hay solicitudes.</p>
            )}

            {solicitudes.map((s) => (
              <div
                key={s.id}
                className="bg-slate-900/70 border border-slate-800 p-5 rounded-xl hover:border-blue-500/40 transition cursor-pointer"
                onClick={() => verDetalle(s)}
              >
                <div className="flex justify-between items-center">
                  <div>
                    <p className="text-lg text-white font-semibold">
                      {s.usuario_nombre || s.nombre || "Usuario"}
                    </p>
                    <p className="text-slate-400 text-sm">{s.usuario_email}</p>

                    <p className="mt-1 text-slate-300">
                      Rol solicitado:{" "}
                      <span className="font-bold text-blue-400">
                        {s.rol_solicitado?.toUpperCase()}
                      </span>
                    </p>

                    <p className="text-xs text-slate-500 mt-1">
                      Estado:{" "}
                      <span
                        className={
                          s.estado === "PENDIENTE"
                            ? "text-yellow-400"
                            : s.estado === "ACEPTADA"
                            ? "text-green-400"
                            : s.estado === "REVERTIDA"
                            ? "text-purple-400"
                            : "text-red-400"
                        }
                      >
                        {s.estado}
                      </span>
                    </p>
                  </div>

                  <span className="text-slate-600">{">"}</span>
                </div>
              </div>
            ))}
          </div>

          {/* PANEL DERECHA (DETALLE) */}
          <div>
            {detalle ? (
              <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl">
                <h2 className="text-2xl font-bold text-white mb-4">
                  Detalles de la Solicitud
                </h2>

                {/* Datos */}
                <div className="space-y-3 text-slate-300">
                  <p>
                    <strong className="text-white">Usuario:</strong>{" "}
                    {detalle.usuario?.nombre_completo ||
                      detalle.usuario?.username ||
                      detalle.usuario?.email}
                  </p>

                  <p>
                    <strong className="text-white">Email:</strong>{" "}
                    {detalle.usuario?.email}
                  </p>

                  <p>
                    <strong className="text-white">Rol solicitado:</strong>{" "}
                    <span className="text-blue-400 font-bold">
                      {detalle.rol_solicitado?.toUpperCase()}
                    </span>
                  </p>

                  {detalle.rol_anterior && (
                    <p>
                      <strong className="text-white">Rol anterior:</strong>{" "}
                      <span className="text-slate-400">
                        {detalle.rol_anterior?.toUpperCase()}
                      </span>
                    </p>
                  )}

                  <p>
                    <strong className="text-white">Motivo del usuario:</strong>
                    <br />
                    <span className="text-slate-400">
                      {detalle.motivo || "No proporcionado"}
                    </span>
                  </p>

                  <p>
                    <strong className="text-white">Fecha de solicitud:</strong>{" "}
                    {new Date(detalle.creado_en).toLocaleString()}
                  </p>

                  <p>
                    <strong className="text-white">Estado:</strong>{" "}
                    <span
                      className={
                        detalle.estado === "PENDIENTE"
                          ? "text-yellow-400"
                          : detalle.estado === "ACEPTADA"
                          ? "text-green-400"
                          : detalle.estado === "REVERTIDA"
                          ? "text-purple-400"
                          : "text-red-400"
                      }
                    >
                      {detalle.estado}
                    </span>
                  </p>

                  {detalle.estado !== "PENDIENTE" && (
                    <>
                      {detalle.admin_email && (
                        <p>
                          <strong className="text-white">Revisado por:</strong>{" "}
                          {detalle.admin_email}
                        </p>
                      )}

                      {detalle.motivo_respuesta && (
                        <p>
                          <strong className="text-white">Respuesta del admin:</strong>
                          <br />
                          <span className="text-slate-400">
                            {detalle.motivo_respuesta}
                          </span>
                        </p>
                      )}

                      {detalle.respondido_en && (
                        <p>
                          <strong className="text-white">Fecha de respuesta:</strong>{" "}
                          {new Date(detalle.respondido_en).toLocaleString()}
                        </p>
                      )}
                    </>
                  )}

                  {detalle.estado === "REVERTIDA" && (
                    <>
                      {detalle.revertido_por_email && (
                        <p>
                          <strong className="text-white">Revertido por:</strong>{" "}
                          {detalle.revertido_por_email}
                        </p>
                      )}

                      {detalle.motivo_reversion && (
                        <p>
                          <strong className="text-white">Motivo de reversión:</strong>
                          <br />
                          <span className="text-purple-400">
                            {detalle.motivo_reversion}
                          </span>
                        </p>
                      )}

                      {detalle.revertido_en && (
                        <p>
                          <strong className="text-white">Fecha de reversión:</strong>{" "}
                          {new Date(detalle.revertido_en).toLocaleString()}
                        </p>
                      )}
                    </>
                  )}
                </div>

                {/* BOTONES DE ACCIÓN */}
                <div className="flex flex-wrap gap-3 mt-6">
                  {/* Aceptar/Rechazar - Solo PENDIENTE */}
                  {detalle.estado === "PENDIENTE" && (
                    <>
                      <button
                        disabled={procesando || modalAbierto || modalEliminar}
                        onClick={abrirModalAceptar}
                        className="flex items-center gap-2 px-4 py-2 bg-green-600/20 border border-green-500/40 text-green-300 rounded-lg hover:bg-green-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <Check size={18} />
                        Aceptar
                      </button>

                      <button
                        disabled={procesando || modalAbierto || modalEliminar}
                        onClick={abrirModalRechazar}
                        className="flex items-center gap-2 px-4 py-2 bg-red-600/20 border border-red-500/40 text-red-300 rounded-lg hover:bg-red-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        <X size={18} />
                        Rechazar
                      </button>
                    </>
                  )}

                  {/* Revertir - Solo ACEPTADA con rol_anterior */}
                  {detalle.estado === "ACEPTADA" && detalle.rol_anterior && (
                    <button
                      disabled={procesando || modalAbierto || modalEliminar}
                      onClick={abrirModalRevertir}
                      className="flex items-center gap-2 px-4 py-2 bg-purple-600/20 border border-purple-500/40 text-purple-300 rounded-lg hover:bg-purple-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <RotateCcw size={18} />
                      Revertir Cambio
                    </button>
                  )}

                  {/* Eliminar - Siempre visible */}
                  <button
                    disabled={procesando || modalAbierto || modalEliminar}
                    onClick={abrirModalEliminar}
                    className="flex items-center gap-2 px-4 py-2 bg-orange-600/20 border border-orange-500/40 text-orange-300 rounded-lg hover:bg-orange-600/30 transition disabled:opacity-50 disabled:cursor-not-allowed ml-auto"
                  >
                    <Trash2 size={18} />
                    Eliminar
                  </button>
                </div>
              </div>
            ) : (
              <div className="bg-slate-900/70 border border-slate-800 p-6 rounded-xl text-center">
                <p className="text-slate-500">
                  Selecciona una solicitud para ver detalles
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ========================================
          MODAL ACEPTAR/RECHAZAR/REVERTIR
          ======================================== */}
      {modalAbierto && detalle && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border border-slate-700 rounded-2xl shadow-2xl max-w-2xl w-full max-h-screen overflow-y-auto">
            
            {/* Header */}
            <div className={`p-6 border-b border-slate-700 ${
              tipoAccion === "aceptar" ? "bg-gradient-to-r from-green-900/30 to-slate-900" :
              tipoAccion === "rechazar" ? "bg-gradient-to-r from-red-900/30 to-slate-900" :
              "bg-gradient-to-r from-purple-900/30 to-slate-900"
            }`}>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-2xl font-bold text-white">
                    {tipoAccion === "aceptar" && "✅ Aceptar Solicitud"}
                    {tipoAccion === "rechazar" && "❌ Rechazar Solicitud"}
                    {tipoAccion === "revertir" && "🔄 Revertir Cambio de Rol"}
                  </h3>
                  <p className="text-slate-400 text-sm mt-1">
                    {tipoAccion === "aceptar" && "Proporciona un motivo de aceptación (opcional)"}
                    {tipoAccion === "rechazar" && "Proporciona una razón del rechazo (opcional)"}
                    {tipoAccion === "revertir" && "⚠️ Debes proporcionar un motivo (OBLIGATORIO, mín. 10 caracteres)"}
                  </p>
                </div>
                <button
                  onClick={cerrarModal}
                  className="text-slate-400 hover:text-white transition"
                >
                  <X size={24} />
                </button>
              </div>
            </div>

            {/* Body */}
            <div className="p-6 space-y-6">
              
              {/* Info solicitud */}
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-2">
                <p className="text-slate-300">
                  <strong className="text-white">Usuario:</strong> {detalle.usuario?.email}
                </p>
                <p className="text-slate-300">
                  <strong className="text-white">Rol solicitado:</strong>{" "}
                  <span className="text-blue-400 font-bold">{detalle.rol_solicitado?.toUpperCase()}</span>
                </p>
                
                {tipoAccion === "revertir" && detalle.rol_anterior && (
                  <p className="text-slate-300">
                    <strong className="text-white">Volverá a:</strong>{" "}
                    <span className="text-purple-400 font-bold">{detalle.rol_anterior?.toUpperCase()}</span>
                  </p>
                )}
              </div>

              {tipoAccion === "revertir" && (
                <div className="bg-purple-500/10 border border-purple-500/40 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="text-purple-400 flex-shrink-0 mt-1" size={20} />
                    <div className="space-y-1">
                      <p className="text-purple-300 font-bold text-sm">
                        ⚠️ ADVERTENCIA
                      </p>
                      <p className="text-purple-300 text-sm">
                        El usuario <strong>{detalle.usuario?.email}</strong> volverá de{" "}
                        <strong>{detalle.rol_solicitado}</strong> a{" "}
                        <strong>{detalle.rol_anterior}</strong>
                      </p>
                      <p className="text-purple-300 text-xs mt-2">
                        Esta acción se registrará en auditoría y el usuario recibirá una notificación.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Textarea */}
              <div className="space-y-2">
                <label className="text-slate-300 font-medium block">
                  {tipoAccion === "aceptar" && "Motivo de Aceptación"}
                  {tipoAccion === "rechazar" && "Razón del Rechazo"}
                  {tipoAccion === "revertir" && "Motivo de Reversión *"}
                </label>
                <textarea
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value)}
                  placeholder={
                    tipoAccion === "aceptar"
                      ? "Ejemplo: Documentación verificada correctamente..."
                      : tipoAccion === "rechazar"
                      ? "Ejemplo: Documentación incompleta..."
                      : "Ejemplo: El usuario no cumplió con los estándares requeridos..."
                  }
                  className="w-full bg-slate-800 border border-slate-700 rounded-lg text-white p-4 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 outline-none transition resize-none"
                  rows="5"
                />
                <p className="text-slate-400 text-xs">
                  {motivo.length}/500 caracteres
                  {tipoAccion === "revertir" && (
                    motivo.length >= 10 ? (
                      <span className="ml-2 text-green-400">✓ Válido</span>
                    ) : (
                      <span className="ml-2 text-red-400">✗ Mínimo 10 caracteres</span>
                    )
                  )}
                </p>
              </div>

              {tipoAccion !== "revertir" && (
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                  <p className="text-blue-300 text-sm">
                    <strong>💡 Nota:</strong> El motivo es opcional. Si lo dejas vacío, se usará un mensaje automático.
                  </p>
                </div>
              )}

              {/* Error en modal */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-slate-800/50 border-t border-slate-700 p-6 flex gap-3">
              <button
                onClick={cerrarModal}
                disabled={procesando}
                className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50 font-medium"
              >
                Cancelar
              </button>
              
              <button
                onClick={
                  tipoAccion === "aceptar" ? confirmarAceptar :
                  tipoAccion === "rechazar" ? confirmarRechazar :
                  confirmarRevertir
                }
                disabled={procesando || (tipoAccion === "revertir" && motivo.trim().length < 10)}
                className={`flex-1 px-4 py-3 rounded-lg transition font-medium flex items-center justify-center gap-2 ${
                  tipoAccion === "aceptar"
                    ? "bg-green-600 hover:bg-green-500 text-white disabled:opacity-50"
                    : tipoAccion === "rechazar"
                    ? "bg-red-600 hover:bg-red-500 text-white disabled:opacity-50"
                    : "bg-purple-600 hover:bg-purple-500 text-white disabled:opacity-50 disabled:cursor-not-allowed"
                }`}
              >
                {procesando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Procesando...
                  </>
                ) : (
                  <>
                    {tipoAccion === "aceptar" && <Check size={18} />}
                    {tipoAccion === "rechazar" && <X size={18} />}
                    {tipoAccion === "revertir" && <RotateCcw size={18} />}
                    
                    {tipoAccion === "aceptar" && "Confirmar Aceptación"}
                    {tipoAccion === "rechazar" && "Confirmar Rechazo"}
                    {tipoAccion === "revertir" && "Confirmar Reversión"}
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ========================================
          MODAL ELIMINAR
          ======================================== */}
      {modalEliminar && detalle && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-slate-900 border-2 border-orange-500/50 rounded-2xl shadow-2xl max-w-xl w-full">
            
            <div className="bg-gradient-to-r from-orange-900/50 to-red-900/50 p-6 border-b-2 border-orange-500/50">
              <div className="flex items-center gap-3">
                <AlertTriangle className="text-orange-400" size={32} />
                <div>
                  <h3 className="text-2xl font-bold text-white">
                    ⚠️ Eliminar Solicitud
                  </h3>
                  <p className="text-orange-300 text-sm mt-1">
                    Esta acción NO se puede deshacer
                  </p>
                </div>
              </div>
            </div>

            <div className="p-6 space-y-6">
              
              <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 space-y-2">
                <p className="text-slate-300">
                  <strong className="text-white">Usuario:</strong> {detalle.usuario?.email}
                </p>
                <p className="text-slate-300">
                  <strong className="text-white">Rol:</strong>{" "}
                  <span className="text-blue-400 font-bold">{detalle.rol_solicitado?.toUpperCase()}</span>
                </p>
                <p className="text-slate-300">
                  <strong className="text-white">Estado actual:</strong>{" "}
                  <span
                    className={
                      detalle.estado === "PENDIENTE"
                        ? "text-yellow-400"
                        : detalle.estado === "ACEPTADA"
                        ? "text-green-400"
                        : detalle.estado === "REVERTIDA"
                        ? "text-purple-400"
                        : "text-red-400"
                    }
                  >
                    {detalle.estado}
                  </span>
                </p>
              </div>
              
              {detalle.estado === "ACEPTADA" && (
                <div className="bg-red-500/20 border-2 border-red-500/50 rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="text-red-400 flex-shrink-0 mt-1" size={24} />
                    <div className="space-y-2">
                      <p className="text-red-300 font-bold">
                        ⚠️ ADVERTENCIA CRÍTICA
                      </p>
                      <p className="text-red-300 text-sm">
                        Esta solicitud fue <strong>ACEPTADA</strong>. Si la eliminas:
                      </p>
                      <ul className="text-red-300 text-sm list-disc list-inside space-y-1">
                        <li>Se borrará el registro de la solicitud</li>
                        <li><strong>El usuario MANTIENE el rol {detalle.rol_solicitado}</strong></li>
                        <li>Solo se elimina el historial, no el rol activo</li>
                      </ul>
                      <p className="text-yellow-300 text-xs mt-2 font-bold">
                        💡 Tip: Si quieres quitar el rol, usa "Revertir Cambio" en lugar de eliminar.
                      </p>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                <p className="text-slate-300 font-medium">
                  Para confirmar, escribe <span className="text-orange-400 font-bold">ELIMINAR</span>:
                </p>
                <input
                  type="text"
                  value={confirmacionEliminar}
                  onChange={(e) => setConfirmacionEliminar(e.target.value.toUpperCase())}
                  placeholder="Escribe ELIMINAR"className="w-full bg-slate-800 border-2 border-slate-700 rounded-lg text-white px-4 py-3 focus:border-orange-500 focus:ring-2 focus:ring-orange-500/20 outline-none transition font-mono"
                  autoFocus
                />
                {confirmacionEliminar && confirmacionEliminar !== "ELIMINAR" && (
                  <p className="text-red-400 text-sm">
                    ❌ Debes escribir exactamente "ELIMINAR"
                  </p>
                )}
              </div>

              {/* Error */}
              {error && (
                <div className="bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-lg text-sm">
                  {error}
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-slate-800/50 border-t border-slate-700 p-6 flex gap-3">
              <button
                onClick={cerrarModalEliminar}
                disabled={procesando}
                className="flex-1 px-4 py-3 bg-slate-700 hover:bg-slate-600 text-white rounded-lg transition disabled:opacity-50 font-medium"
              >
                Cancelar
              </button>
              
              <button
                onClick={confirmarEliminar}
                disabled={procesando || confirmacionEliminar !== "ELIMINAR"}
                className="flex-1 px-4 py-3 bg-red-600 hover:bg-red-500 text-white rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed font-medium flex items-center justify-center gap-2"
              >
                {procesando ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Eliminando...
                  </>
                ) : (
                  <>
                    <Trash2 size={18} />
                    Eliminar Permanentemente
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}