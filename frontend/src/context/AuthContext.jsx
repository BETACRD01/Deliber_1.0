import React, { createContext, useState, useCallback, useEffect } from 'react';
import { authAPI } from '../services/api';

export const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Cargar usuario al montar
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      verificarToken();
    } else {
      setLoading(false);
    }
  }, []);

  const verificarToken = useCallback(async () => {
    try {
      const response = await authAPI.perfil();

      // Compatibilidad completa (usuario o datos planos)
      const userData = response.data.usuario ?? response.data;

      setUser(userData);
      setError(null);
    } catch (err) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email, password) => {
    try {
      setLoading(true);
      setError(null);

      const response = await authAPI.login(email, password);
      const { tokens } = response.data;

      if (tokens?.access && tokens?.refresh) {
        localStorage.setItem('access_token', tokens.access);
        localStorage.setItem('refresh_token', tokens.refresh);

        await verificarToken();
        return { success: true };
      } else {
        const msg = "No se recibieron tokens desde el backend";
        setError(msg);
        return { success: false, error: msg };
      }
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.response?.data?.error ||
        "Error en el inicio de sesión";

      setError(message);
      return { success: false, error: message };
    } finally {
      setLoading(false);
    }
  }, [verificarToken]);

  const logout = useCallback(async () => {
    try {
      await authAPI.logout();
    } catch (err) {
      console.error("Error en logout:", err);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      setUser(null);
      setError(null);
    }
  }, []);

  // Corrección: roles dinámicos y rol activo
  const isAuthenticated = !!user;

  const isAdmin =
    user?.is_superuser === true ||
    user?.rol_activo === "ADMINISTRADOR" ||
    user?.roles?.includes("ADMINISTRADOR");

  const value = {
    user,
    loading,
    error,
    login,
    logout,
    isAuthenticated,
    isAdmin,
    verificarToken,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}
