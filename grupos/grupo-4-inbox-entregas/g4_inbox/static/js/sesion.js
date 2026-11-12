// Sesión y errores, compartidos por inbox.html y detalle.html.
// Misma convención que el panel de G6 (pantallas/comun.js): el login es de G2
// (POST /api/v1/auth/login), el token se guarda en esta pestaña con la clave
// "udv_token" y se manda como "Authorization: Bearer <token>".
"use strict";

const Sesion = (function () {
  const CLAVE_TOKEN = "udv_token";

  function leerToken() {
    try { return sessionStorage.getItem(CLAVE_TOKEN) || localStorage.getItem(CLAVE_TOKEN); }
    catch { return null; }
  }

  // Encabezados de autenticación para un fetch (vacío si no hay sesión).
  function encabezados() {
    const token = leerToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // El cuerpo de error de G2 es {"error": {"code", "message"}}; los errores
  // propios de FastAPI antes de pasar por G2 traen "detail". Se acepta ambos.
  function mensajeDeError(cuerpo, estadoHttp) {
    if (estadoHttp === 401) return "Tu sesión no está iniciada o venció. Inicia sesión de nuevo.";
    const error = cuerpo && cuerpo.error;
    if (error && error.message) return error.message;
    const detalle = cuerpo && cuerpo.detail;
    if (typeof detalle === "string") return detalle;
    if (Array.isArray(detalle)) return detalle.map((d) => d.msg || JSON.stringify(d)).join(", ");
    return `Error HTTP ${estadoHttp}`;
  }

  return { leerToken, encabezados, mensajeDeError };
})();

if (typeof module !== "undefined") module.exports = Sesion;  // para probarlo con node
