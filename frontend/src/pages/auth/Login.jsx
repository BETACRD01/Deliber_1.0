import React, { useState, useContext, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { AuthContext } from "../../context/AuthContext";
import { useBackendConnection } from "../../hooks/useBackendConnection";
import {
  Lock,
  Mail,
  Eye,
  EyeOff,
  Zap,
  RefreshCw,
  Shield,
} from "lucide-react";

export function Login() {
  const navigate = useNavigate();
  const { login, isAuthenticated, loading: authLoading } =
    useContext(AuthContext);

  const {
    connected,
    checking,
    error: connectionError,
    verificarConexion,
  } = useBackendConnection();

  const [email, setEmail] = useState("admin@deliber.com");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  // Redirección si ya está autenticado
  useEffect(() => {
    if (isAuthenticated && !authLoading) {
      navigate("/dashboard");
    }
  }, [isAuthenticated, authLoading, navigate]);

  // Login
  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await login(email, password);
      if (result.success) {
        navigate("/dashboard");
      } else {
        setError(result.error || "Error en el inicio de sesión");
      }
    } catch (err) {
      setError("Error inesperado. Intenta nuevamente.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-950 px-4">
      <div className="w-full max-w-md">

        {/* HEADER */}
        <div className="text-center mb-10">
          <div className="w-16 h-16 mx-auto flex items-center justify-center rounded-2xl 
              bg-gradient-to-tr from-blue-600 to-purple-600 shadow-lg shadow-blue-500/20">
            <Zap className="w-8 h-8 text-white" />
          </div>

          <h1 className="text-4xl font-bold text-white mt-4">Deliber Admin</h1>

          <p className="text-slate-400 text-sm mt-2">
            Inicia sesión para acceder al panel de administración
          </p>
        </div>

        {/* CARD */}
        <div className="bg-slate-900/70 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl p-8 space-y-6">

          {/* ESTADO DEL BACKEND */}
          <div
            className={`flex items-center justify-between text-xs px-4 py-3 rounded-xl border transition-all ${
              checking
                ? "bg-yellow-500/10 border-yellow-500/40 text-yellow-300"
                : connected
                ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-300"
                : "bg-red-500/10 border-red-500/40 text-red-300"
            }`}
          >
            <span className="flex-1">
              {checking
                ? "Verificando conexión..."
                : connected
                ? "Backend conectado ✓"
                : "Backend desconectado. Haz clic para reintentar"}
            </span>

            <button
              type="button"
              onClick={verificarConexion}
              disabled={checking}
              className="p-2 bg-slate-800 hover:bg-slate-700 rounded-lg text-slate-300 disabled:opacity-50 transition-colors"
              title="Verificar conexión"
            >
              <RefreshCw className={`w-4 h-4 ${checking ? "animate-spin" : ""}`} />
            </button>
          </div>

          {/* MENSAJE DE ERROR DEL BACKEND */}
          {connectionError && (
            <div className="bg-red-500/10 border border-red-500/40 text-red-300 text-xs px-4 py-3 rounded-xl">
              {connectionError}
            </div>
          )}

          {/* FORM */}
          <form onSubmit={handleSubmit} className="space-y-5">

            {/* EMAIL */}
            <div>
              <label className="text-sm text-slate-300 font-medium">
                Correo electrónico
              </label>
              <div className="relative mt-1">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700 
                    rounded-xl text-white text-sm px-12 py-3
                    focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                    outline-none transition"
                  required
                />
              </div>
            </div>

            {/* PASSWORD */}
            <div>
              <label className="text-sm text-slate-300 font-medium">
                Contraseña
              </label>

              <div className="relative mt-1">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />

                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-slate-900/80 border border-slate-700 rounded-xl 
                    text-white text-sm px-12 py-3
                    focus:ring-2 focus:ring-blue-500 focus:border-blue-500 
                    outline-none transition"
                  required
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-4 top-1/2 -translate-y-1/2 
                    text-slate-500 hover:text-white transition"
                >
                  {showPassword ? (
                    <EyeOff className="w-5 h-5" />
                  ) : (
                    <Eye className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            {/* ERROR DE LOGIN */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/40 text-red-300 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            {/* BOTÓN LOGIN */}
            <button
              type="submit"
              disabled={!connected || loading}
              className="w-full py-3 bg-gradient-to-r from-blue-600 to-purple-600
                hover:from-blue-500 hover:to-purple-500
                text-white font-semibold text-sm rounded-xl shadow-md
                hover:shadow-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? "Iniciando sesión..."
                : !connected
                ? "Conecta el backend primero"
                : "Iniciar sesión"}
            </button>
          </form>

          {/* INFO */}
          <div className="flex items-center gap-2 text-slate-500 text-xs pt-2">
            <Shield className="w-4 h-4" />
            Acceso solo para administradores autorizados.
          </div>
        </div>

        {/* FOOTER */}
        <p className="text-center text-xs text-slate-500 mt-4">
          ¿Problemas para acceder?{" "}
          <button className="text-blue-400 hover:underline">
            Contactar soporte
          </button>
        </p>
      </div>
    </div>
  );
}
