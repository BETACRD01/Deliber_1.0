import React, { useContext } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";

import { AuthProvider, AuthContext } from "./context/AuthContext";
import { Login } from "./pages/auth/Login";
import { Dashboard } from "./pages/admin/Dashboard";
import { SolicitudesCambioRol } from "./pages/admin/SolicitudesCambioRol";

import "./index.css";

// ------------------------------
//   RUTA PROTEGIDA
// ------------------------------
function ProtectedRoute({ children }) {
  const { isAuthenticated, isAdmin, loading } = useContext(AuthContext);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <p className="text-slate-400 text-lg">Cargando...</p>
      </div>
    );
  }

  if (!isAuthenticated) return <Navigate to="/login" replace />;

  if (!isAdmin) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">Acceso denegado</h1>
          <p className="text-slate-400 mt-2">
            Solo administradores pueden acceder a esta sección.
          </p>
        </div>
      </div>
    );
  }

  return children;
}

// ------------------------------
//   CONTENIDO PRINCIPAL DE RUTAS
// ------------------------------
function AppContent() {
  return (
    <Routes>
      {/* Página LOGIN */}
      <Route path="/login" element={<Login />} />

      {/* DASHBOARD ADMIN */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      {/* SOLICITUDES DE CAMBIO DE ROL */}
      <Route
        path="/admin/solicitudes"
        element={
          <ProtectedRoute>
            <SolicitudesCambioRol />
          </ProtectedRoute>
        }
      />

      {/* REDIRECCIONES */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

// ------------------------------
//   APLICACIÓN PRINCIPAL
// ------------------------------
export default function App() {
  return (
    <Router>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </Router>
  );
}
