import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://172.16.60.5:8000/api';

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor para agregar token JWT
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Interceptor para manejar respuestas
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Si el token expiró, intentar refrescarlo
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${API_BASE_URL}/auth/token/refresh/`,
            { refresh: refreshToken }
          );
          
          const { access } = response.data;
          localStorage.setItem('access_token', access);
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// ============================================
// ENDPOINTS - AUTENTICACIÓN
// ============================================

export const authAPI = {
  // Login y registro
  login: (email, password) => 
    api.post('/auth/login/', { identificador: email, password }),
  
  registro: (data) =>
    api.post('/auth/registro/', data),
  
  googleLogin: (data) =>
    api.post('/auth/google-login/', data),
  
  logout: () => 
    api.post('/auth/logout/'),
  
  perfil: () => 
    api.get('/auth/perfil/'),
  
  refreshToken: (refresh) =>
    api.post('/auth/token/refresh/', { refresh }),
  
  // Recuperación de contraseña
  solicitarCodigoRecuperacion: (email) =>
    api.post('/auth/solicitar-codigo-recuperacion/', { email }),
  
  verificarCodigo: (email, codigo) =>
    api.post('/auth/verificar-codigo/', { email, codigo }),
  
  resetPasswordConCodigo: (data) =>
    api.post('/auth/reset-password-con-codigo/', data),
};

// ============================================
// ENDPOINTS - DASHBOARD ADMINISTRATIVO
// ============================================

export const dashboardAPI = {
  estadisticas: () => 
    api.get('/admin/dashboard/'),
  
  resumenDia: () => 
    api.get('/admin/dashboard/resumen_dia/'),
  
  alertas: () => 
    api.get('/admin/dashboard/alertas/'),
};

// ============================================
// ENDPOINTS - USUARIOS
// ============================================

export const usuariosAPI = {
  // Gestión de usuarios (Admin)
  listar: (page = 1, search = '', filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    if (search) params.append('search', search);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/admin/usuarios/?${params}`);
  },
  
  detalle: (id) => 
    api.get(`/admin/usuarios/${id}/`),
  
  actualizar: (id, data) => 
    api.patch(`/admin/usuarios/${id}/`, data),
  
  cambiarRol: (id, data) => 
    api.post(`/admin/usuarios/${id}/cambiar_rol/`, data),
  
  desactivar: (id, data) => 
    api.post(`/admin/usuarios/${id}/desactivar/`, data),
  
  activar: (id) => 
    api.post(`/admin/usuarios/${id}/activar/`),
  
  resetearPassword: (id, data) => 
    api.post(`/admin/usuarios/${id}/resetear_password/`, data),
  
  estadisticas: () => 
    api.get('/admin/usuarios/estadisticas/'),

  // Perfil personal
  miPerfil: () =>
    api.get('/usuarios/perfil/'),
  
  perfilPublico: (userId) =>
    api.get(`/usuarios/perfil/publico/${userId}/`),
  
  actualizarPerfil: (data) =>
    api.patch('/usuarios/perfil/actualizar/', data),
  
  estadisticasPerfil: () =>
    api.get('/usuarios/perfil/estadisticas/'),
  
  actualizarFotoPerfil: (formData) =>
    api.post('/usuarios/perfil/foto/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    }),

  // Direcciones
  direcciones: () =>
    api.get('/usuarios/direcciones/'),
  
  crearDireccion: (data) =>
    api.post('/usuarios/direcciones/', data),
  
  actualizarDireccion: (id, data) =>
    api.patch(`/usuarios/direcciones/${id}/`, data),
  
  eliminarDireccion: (id) =>
    api.delete(`/usuarios/direcciones/${id}/`),

  // Métodos de pago
  metodosPago: () =>
    api.get('/usuarios/metodos-pago/'),
  
  crearMetodoPago: (data) =>
    api.post('/usuarios/metodos-pago/', data),
  
  eliminarMetodoPago: (id) =>
    api.delete(`/usuarios/metodos-pago/${id}/`),

  // FCM Token (Notificaciones push)
  actualizarFCMToken: (token) =>
    api.post('/usuarios/fcm-token/', { token }),

  // Cambio de rol activo
  cambiarRolActivo: (rol) =>
    api.post('/usuarios/cambiar-rol-activo/', { rol_activo: rol }),
  
  misRoles: () =>
    api.get('/usuarios/mis-roles/'),
};

// ============================================
// ENDPOINTS - PROVEEDORES
// ============================================

export const proveedoresAPI = {
  // Listado y gestión (Admin)
  listar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/admin/proveedores/?${params}`);
  },
  
  detalle: (id) => 
    api.get(`/admin/proveedores/${id}/`),
  
  verificar: (id, data) => 
    api.post(`/admin/proveedores/${id}/verificar/`, data),
  
  desactivar: (id) => 
    api.post(`/admin/proveedores/${id}/desactivar/`),
  
  activar: (id) => 
    api.post(`/admin/proveedores/${id}/activar/`),
  
  pendientes: () => 
    api.get('/admin/proveedores/pendientes/'),

  // Listado público
  listarPublico: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/proveedores/?${params}`);
  },

  detallePublico: (id) =>
    api.get(`/proveedores/${id}/`),
  
  activos: () =>
    api.get('/proveedores/activos/'),
  
  abiertos: () =>
    api.get('/proveedores/abiertos/'),
  
  porTipo: (tipo) =>
    api.get(`/proveedores/por_tipo/?tipo=${tipo}`),

  // Mi proveedor (para usuarios con rol proveedor)
  miProveedor: () =>
    api.get('/proveedores/mi_proveedor/'),
  
  actualizarMiProveedor: (data) =>
    api.patch('/proveedores/mi_proveedor/', data),
};

// ============================================
// ENDPOINTS - REPARTIDORES
// ============================================

export const repartidoresAPI = {
  // Gestión (Admin)
  listar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/admin/repartidores/?${params}`);
  },
  
  detalle: (id) => 
    api.get(`/admin/repartidores/${id}/`),
  
  verificar: (id, data) => 
    api.post(`/admin/repartidores/${id}/verificar/`, data),
  
  desactivar: (id) => 
    api.post(`/admin/repartidores/${id}/desactivar/`),
  
  activar: (id) => 
    api.post(`/admin/repartidores/${id}/activar/`),
  
  pendientes: () => 
    api.get('/admin/repartidores/pendientes/'),

  // Perfil y gestión personal
  miPerfil: () =>
    api.get('/repartidores/perfil/'),
  
  actualizarPerfil: (data) =>
    api.patch('/repartidores/perfil/', data),
  
  estadisticas: () =>
    api.get('/repartidores/perfil/estadisticas/'),

  // Estado y ubicación
  actualizarEstado: (disponible) =>
    api.post('/repartidores/estado/', { disponible }),
  
  actualizarUbicacion: (data) =>
    api.post('/repartidores/ubicacion/', data),

  // Vehículos
  vehiculos: () =>
    api.get('/repartidores/vehiculos/'),
  
  crearVehiculo: (data) =>
    api.post('/repartidores/vehiculos/', data),
  
  actualizarVehiculo: (id, data) =>
    api.patch(`/repartidores/vehiculos/${id}/`, data),
  
  eliminarVehiculo: (id) =>
    api.delete(`/repartidores/vehiculos/${id}/`),

  // Pedidos
  pedidosDisponibles: () =>
    api.get('/repartidores/pedidos-disponibles/'),
  
  aceptarPedido: (pedidoId) =>
    api.post(`/repartidores/pedidos/${pedidoId}/aceptar/`),
};

// ============================================
// ENDPOINTS - PRODUCTOS Y CATEGORÍAS
// ============================================

export const categoriasAPI = {
  listar: () =>
    api.get('/categorias/'),
  
  detalle: (id) =>
    api.get(`/categorias/${id}/`),
  
  crear: (data) =>
    api.post('/categorias/', data),
  
  actualizar: (id, data) =>
    api.patch(`/categorias/${id}/`, data),
  
  eliminar: (id) =>
    api.delete(`/categorias/${id}/`),
};

export const productosAPI = {
  listar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/productos/?${params}`);
  },
  
  detalle: (id) =>
    api.get(`/productos/${id}/`),
  
  crear: (data) =>
    api.post('/productos/', data),
  
  actualizar: (id, data) =>
    api.patch(`/productos/${id}/`, data),
  
  eliminar: (id) =>
    api.delete(`/productos/${id}/`),
  
  destacados: () =>
    api.get('/productos/destacados/'),
  
  ofertas: () =>
    api.get('/productos/ofertas/'),
  
  buscar: (query) =>
    api.get(`/productos/buscar/?q=${query}`),
};

export const variantesAPI = {
  listar: (productoId) =>
    api.get(`/variantes/?producto=${productoId}`),
  
  crear: (data) =>
    api.post('/variantes/', data),
  
  actualizar: (id, data) =>
    api.patch(`/variantes/${id}/`, data),
  
  eliminar: (id) =>
    api.delete(`/variantes/${id}/`),
};

// ============================================
// ENDPOINTS - PEDIDOS
// ============================================

export const pedidosAPI = {
  listar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/pedidos/?${params}`);
  },
  
  detalle: (id) =>
    api.get(`/pedidos/${id}/`),
  
  crear: (data) =>
    api.post('/pedidos/', data),
  
  aceptarRepartidor: (id, data) =>
    api.post(`/pedidos/${id}/aceptar-repartidor/`, data),
  
  confirmarProveedor: (id, data) =>
    api.post(`/pedidos/${id}/confirmar-proveedor/`, data),
  
  cambiarEstado: (id, data) =>
    api.post(`/pedidos/${id}/estado/`, data),
  
  cancelar: (id, data) =>
    api.post(`/pedidos/${id}/cancelar/`, data),
  
  ganancias: (id) =>
    api.get(`/pedidos/${id}/ganancias/`),

  // Mis pedidos según rol
  misPedidos: () =>
    api.get('/pedidos/mis-pedidos/'),
};

// ============================================
// ENDPOINTS - PAGOS
// ============================================

export const pagosAPI = {
  metodos: () =>
    api.get('/pagos/metodos/'),
  
  crear: (data) =>
    api.post('/pagos/pagos/', data),
  
  detalle: (id) =>
    api.get(`/pagos/pagos/${id}/`),
  
  misPagos: () =>
    api.get('/pagos/pagos/mis_pagos/'),
  
  pendientesVerificacion: () =>
    api.get('/pagos/pagos/pendientes_verificacion/'),
  
  verificarPago: (id, data) =>
    api.post(`/pagos/pagos/${id}/verificar/`, data),
};

// ============================================
// ENDPOINTS - RIFAS
// ============================================

export const rifasAPI = {
  listar: (page = 1) =>
    api.get(`/rifas/rifas/?page=${page}`),
  
  detalle: (id) =>
    api.get(`/rifas/rifas/${id}/`),
  
  crear: (data) =>
    api.post('/rifas/rifas/', data),
  
  actualizar: (id, data) =>
    api.patch(`/rifas/rifas/${id}/`, data),
  
  activa: () =>
    api.get('/rifas/rifas/activa/'),
  
  elegibilidad: (id) =>
    api.get(`/rifas/rifas/${id}/elegibilidad/`),
  
  participar: (id) =>
    api.post(`/rifas/rifas/${id}/participar/`),
  
  misParticipaciones: () =>
    api.get('/rifas/participaciones/mis-participaciones/'),
  
  realizarSorteo: (id) =>
    api.post(`/rifas/rifas/${id}/sortear/`),
};

// ============================================
// ENDPOINTS - NOTIFICACIONES
// ============================================

export const notificacionesAPI = {
  listar: (page = 1) =>
    api.get(`/notificaciones/?page=${page}`),
  
  detalle: (id) =>
    api.get(`/notificaciones/${id}/`),
  
  noLeidas: () =>
    api.get('/notificaciones/no_leidas/'),
  
  marcarLeida: (id) =>
    api.post(`/notificaciones/${id}/marcar_leida/`),
  
  marcarTodasLeidas: () =>
    api.post('/notificaciones/marcar_todas_leidas/'),
  
  estadisticas: () =>
    api.get('/notificaciones/estadisticas/'),
  
  eliminar: (id) =>
    api.delete(`/notificaciones/${id}/`),
};

// ============================================
// ENDPOINTS - CHAT
// ============================================

export const chatAPI = {
  listarChats: (page = 1) =>
    api.get(`/chat/chats/?page=${page}`),
  
  detalleChat: (id) =>
    api.get(`/chat/chats/${id}/`),
  
  crearSoporte: (data) =>
    api.post('/chat/chats/soporte/', data),
  
  mensajes: (chatId, page = 1) =>
    api.get(`/chat/chats/${chatId}/mensajes/?page=${page}`),
  
  enviarMensaje: (chatId, data) =>
    api.post(`/chat/chats/${chatId}/mensajes/`, data),
  
  marcarLeido: (chatId) =>
    api.post(`/chat/chats/${chatId}/marcar_leido/`),
  
  cerrarChat: (chatId) =>
    api.post(`/chat/chats/${chatId}/cerrar/`),
};

// ============================================
// ENDPOINTS - REPORTES
// ============================================

export const reportesAPI = {
  // Reportes Admin
  admin: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/admin/?${params}`);
  },
  
  adminEstadisticas: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/admin/estadisticas/?${params}`);
  },
  
  adminExportar: (formato = 'excel', filters = {}) => {
    const params = new URLSearchParams({ ...filters, formato });
    return api.get(`/reportes/admin/exportar/?${params}`, {
      responseType: 'blob'
    });
  },

  // Reportes Proveedor
  proveedor: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/proveedor/?${params}`);
  },
  
  proveedorEstadisticas: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/proveedor/estadisticas/?${params}`);
  },

  // Reportes Repartidor
  repartidor: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/repartidor/?${params}`);
  },
  
  repartidorEstadisticas: (filters = {}) => {
    const params = new URLSearchParams(filters);
    return api.get(`/reportes/repartidor/estadisticas/?${params}`);
  },
};

// ============================================
// ✅ ENDPOINTS - SOLICITUDES DE CAMBIO DE ROL
// ============================================

export const solicitudesRolAPI = {
  // Usuario normal
  crear: (data) =>
    api.post('/usuarios/solicitudes-cambio-rol/', data),

  misSolicitudes: () =>
    api.get('/usuarios/solicitudes-cambio-rol/'),

  detalle: (uuid) =>
    api.get(`/usuarios/solicitudes-cambio-rol/${uuid}/`),
  
   revertir: (uuid, data = {}) =>
    api.post(`/admin/solicitudes-cambio-rol/${uuid}/revertir/`, data),

  // Administrador
  adminListar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach((key) => {
      params.append(key, filters[key]);
    });
    return api.get(`/admin/solicitudes-cambio-rol/?${params}`);
  },

  adminDetalle: (uuid) =>
    api.get(`/admin/solicitudes-cambio-rol/${uuid}/`),

  pendientes: () =>
    api.get('/admin/solicitudes-cambio-rol/pendientes/'),

  estadisticas: () =>
    api.get('/admin/solicitudes-cambio-rol/estadisticas/'),

  aceptar: (uuid, data = {}) =>
    api.post(`/admin/solicitudes-cambio-rol/${uuid}/aceptar/`, data),

  rechazar: (uuid, data = {}) =>
    api.post(`/admin/solicitudes-cambio-rol/${uuid}/rechazar/`, data),

  // ✅ AQUÍ ESTÁ EL MÉTODO ELIMINAR EN EL LUGAR CORRECTO
  eliminar: (uuid) =>
    api.delete(`/admin/solicitudes-cambio-rol/${uuid}/eliminar/`),
};

// ============================================
// ENDPOINTS - CONFIGURACIÓN
// ============================================

export const configAPI = {
  obtener: () => 
    api.get('/admin/configuracion/'),
  
  actualizar: (data) => 
    api.put('/admin/configuracion/', data),

  parametros: () =>
    api.get('/admin/configuracion/parametros/'),
  
  actualizarParametro: (key, value) =>
    api.patch('/admin/configuracion/parametros/', { key, value }),
};

// ============================================
// ENDPOINTS - ACCIONES (LOGS)
// ============================================

export const accionesAPI = {
  listar: (page = 1, filters = {}) => {
    const params = new URLSearchParams();
    params.append('page', page);
    Object.keys(filters).forEach(key => {
      params.append(key, filters[key]);
    });
    return api.get(`/admin/acciones/?${params}`);
  },
  
  detalle: (id) =>
    api.get(`/admin/acciones/${id}/`),
  
  misAcciones: () => 
    api.get('/admin/acciones/mis_acciones/'),

  porUsuario: (usuarioId) =>
    api.get(`/admin/acciones/por_usuario/${usuarioId}/`),

  
};

// ============================================
// UTILIDADES
// ============================================

export const healthAPI = {
  check: () =>
    api.get('/health/'),
};

export default api;