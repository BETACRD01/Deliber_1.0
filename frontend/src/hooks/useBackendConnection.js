import { useState, useEffect } from "react";
import api from "../services/api";

export function useBackendConnection() {
  const [connected, setConnected] = useState(false);
  const [checking, setChecking] = useState(false);
  const [error, setError] = useState("");

  // URL base del backend
  const API_URL =
    import.meta.env.VITE_API_URL?.trim() || "http://172.16.60.5:8000/api";

  // Verificar conexión al cargar el componente
  useEffect(() => {
    verificarConexion();
  }, [API_URL]);

  const verificarConexion = async () => {
    try {
      setChecking(true);
      setError("");

      // Timeout de 5 segundos
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error("Timeout")), 5000)
      );

      // 🔥 PETICIÓN A UNA RUTA LIBRE (NO REQUIERE TOKEN)
      const apiPromise = api.get("/health/");

      // Competencia entre petición y timeout
      await Promise.race([apiPromise, timeoutPromise]);

      setConnected(true);
    } catch (err) {
      setConnected(false);

      if (err.message === "Timeout") {
        setError(
          `⏳ El backend no responde (timeout 5s). Revisa si está activo: ${API_URL}`
        );
      } else {
        setError(`❌ No se puede conectar al backend: ${API_URL}`);
      }
    } finally {
      setChecking(false);
    }
  };

  return { connected, checking, error, verificarConexion };
}
