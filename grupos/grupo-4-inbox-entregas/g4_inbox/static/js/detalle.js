// =====================================================
// PANTALLA DE DETALLE / ENTREGA / REVISIÓN
// Conectada al backend real — igual que inbox.js, pero para una sola
// asignación, cuyo id viene en la URL: detalle.html?id=123
// =====================================================

const API_BASE = "/api/v1";

const idAsignacion = new URLSearchParams(location.search).get("id");

const NOMBRE_ESTADO = {
  assigned: "Asignada", in_progress: "En progreso", submitted: "Entregada",
  under_review: "En revisión", returned: "Devuelta", approved: "Aprobada",
  closed: "Cerrada", cancelled: "Cancelada",
};

function claseBadge(estado) {
  return "badge-" + String(estado || "").replace(/_/g, "-");
}

async function apiFetch(ruta, opciones = {}) {
  const respuesta = await fetch(`${API_BASE}${ruta}`, {
    ...opciones,
    headers: { "Content-Type": "application/json", ...(opciones.headers || {}) },
  });
  const tipo = respuesta.headers.get("content-type") || "";
  const datos = tipo.includes("application/json") ? await respuesta.json() : await respuesta.text();
  if (!respuesta.ok) {
    const detalle = datos && datos.detail ? datos.detail : `Error HTTP ${respuesta.status}`;
    throw new Error(Array.isArray(detalle) ? detalle.map((x) => x.msg || JSON.stringify(x)).join(", ") : detalle);
  }
  return datos;
}

function mostrarError(mensaje, id = "avisoError") {
  const el = document.getElementById(id);
  el.textContent = mensaje;
  el.style.display = "flex";
}

function ocultarAvisos() {
  ["avisoError", "avisoEntregaError", "avisoEntregaOk"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.style.display = "none";
  });
}

function adaptarTarea(api) {
  return {
    id: api.id,
    titulo: api.title || api.task_type || `Tarea ${api.id}`,
    tipo: api.task_type || "",
    estado: api.status,
    instrucciones: api.instructions || "",
    comentario: (api.comments || []).length ? api.comments[api.comments.length - 1].text : "",
    borrador: api.draft_comment || "",
    archivo: (api.files || []).length ? api.files[api.files.length - 1].name : null,
    // Por defecto true: si el backend no manda este campo (no debería
    // pasar), es más seguro seguir pidiendo evidencia que dejar de pedirla.
    requiereArchivo: api.requiere_archivo !== false,
  };
}

let tareaActual = null;

function agregarBoton(contenedor, texto, clase, accion) {
  const btn = document.createElement("button");
  btn.className = `btn-udv ${clase}`;
  btn.textContent = texto;
  btn.onclick = accion;
  contenedor.appendChild(btn);
}

function mostrarFormularioEntrega(tarea) {
  document.getElementById("formEntrega").style.display = "block";
  document.getElementById("entregaComentario").value = tarea.borrador || "";
  document.getElementById("entregaArchivo").value = "";

  // Este tipo de tarea no pide evidencia — se oculta el campo de archivo
  // en vez de mostrarlo y luego dejar entregar sin usarlo.
  const campoArchivo = document.getElementById("entregaArchivo");
  const etiquetaArchivo = document.querySelector('label[for="entregaArchivo"]');
  campoArchivo.style.display = tarea.requiereArchivo ? "block" : "none";
  if (etiquetaArchivo) etiquetaArchivo.style.display = tarea.requiereArchivo ? "block" : "none";

  document.getElementById("archivoInfo").textContent = !tarea.requiereArchivo
    ? "Esta tarea no requiere evidencia adjunta."
    : tarea.archivo
      ? `📎 Archivo registrado: ${tarea.archivo}`
      : "Selecciona la evidencia que vas a registrar.";
  const botones = document.getElementById("entregaBotones");
  botones.innerHTML = "";
  agregarBoton(botones, "Guardar borrador", "btn-udv-outline", () => guardarBorrador(tarea));
  agregarBoton(botones, tarea.estado === "returned" ? "Reenviar" : "Entregar", "btn-udv-primary", () => confirmarEntrega(tarea));
}

// GET /api/v1/assignments/{id} — carga y pinta la pantalla completa
async function cargarDetalle() {
  ocultarAvisos();
  try {
    const api = await apiFetch(`/assignments/${idAsignacion}`);
    tareaActual = adaptarTarea(api);

    document.getElementById("cargando").style.display = "none";
    document.getElementById("detalle").style.display = "block";
    document.getElementById("detTipo").textContent = tareaActual.tipo;
    document.getElementById("detTitulo").textContent = tareaActual.titulo;
    document.getElementById("detInstrucciones").textContent = tareaActual.instrucciones;

    const badge = document.getElementById("detEstadoBadge");
    badge.textContent = NOMBRE_ESTADO[tareaActual.estado] || tareaActual.estado;
    badge.className = `udv-badge ${claseBadge(tareaActual.estado)}`;

    document.getElementById("obsGroup").style.display = "none";
    document.getElementById("obs").value = "";
    document.getElementById("formEntrega").style.display = "none";

    const contComentario = document.getElementById("detComentario");
    contComentario.innerHTML = "";
    if (tareaActual.comentario) {
      const aviso = document.createElement("div");
      aviso.className = "udv-alert udv-alert-danger";
      aviso.textContent = `Observación del revisor: ${tareaActual.comentario}`;
      contComentario.appendChild(aviso);
    }

    // Las acciones visibles salen de lo que el estado permite — nunca
    // se inventa un botón que la tabla de transiciones no autorice.
    const botones = document.getElementById("detBotones");
    botones.innerHTML = "";
    if (tareaActual.estado === "assigned") {
      agregarBoton(botones, "Iniciar tarea", "btn-udv-primary", () => transicion(tareaActual, "start"));
    } else if (tareaActual.estado === "in_progress" || tareaActual.estado === "returned") {
      mostrarFormularioEntrega(tareaActual);
    } else if (tareaActual.estado === "submitted") {
      agregarBoton(botones, "Tomar para revisar", "btn-udv-primary", () => transicion(tareaActual, "review"));
    } else if (tareaActual.estado === "under_review") {
      agregarBoton(botones, "Aprobar", "btn-udv-primary", () => transicion(tareaActual, "approve"));
      agregarBoton(botones, "Devolver", "btn-udv-gold", () => devolver(tareaActual));
      document.getElementById("obsGroup").style.display = "block";
    } else {
      botones.textContent = "Sin acciones disponibles en este estado.";
    }
  } catch (error) {
    document.getElementById("cargando").style.display = "none";
    mostrarError(`No se pudo cargar la asignación: ${error.message}`);
  }
}

async function guardarBorrador(tarea) {
  try {
    const comment = document.getElementById("entregaComentario").value.trim();
    await apiFetch(`/assignments/${tarea.id}/submission-draft`, {
      method: "PUT",
      body: JSON.stringify({ comment }),
    });
    tarea.borrador = comment;
    const ok = document.getElementById("avisoEntregaOk");
    ok.textContent = "Borrador guardado en el backend. Puedes seguir editándolo antes de entregar.";
    ok.style.display = "flex";
    document.getElementById("avisoEntregaError").style.display = "none";
  } catch (error) {
    mostrarError(error.message, "avisoEntregaError");
  }
}

// Registra el archivo en el endpoint de vinculación y luego hace submit/resubmit.
// El backend solo guarda el nombre/id del archivo, no recibe los bytes.
async function confirmarEntrega(tarea) {
  const comentario = document.getElementById("entregaComentario").value.trim();
  const archivoInput = document.getElementById("entregaArchivo");
  const archivoNuevo = archivoInput.files[0];
  document.getElementById("avisoEntregaError").style.display = "none";
  document.getElementById("avisoEntregaOk").style.display = "none";

  if (tarea.requiereArchivo && !tarea.archivo && !archivoNuevo) {
    mostrarError("Debes seleccionar la evidencia antes de entregar.", "avisoEntregaError");
    return;
  }
  try {
    await apiFetch(`/assignments/${tarea.id}/submission-draft`, {
      method: "PUT",
      body: JSON.stringify({ comment: comentario }),
    });
    if (archivoNuevo) {
      await apiFetch(`/assignments/${tarea.id}/files`, {
        method: "POST",
        body: JSON.stringify({ file_id: `demo-${tarea.id}-${Date.now()}`, name: archivoNuevo.name }),
      });
    }
    const accion = tarea.estado === "returned" ? "resubmit" : "submit";
    await apiFetch(`/assignments/${tarea.id}/${accion}`, {
      method: "POST",
      headers: { "X-Role": "docente" },
    });
    await cargarDetalle();
    const ok = document.getElementById("avisoEntregaOk");
    ok.textContent = accion === "resubmit" ? "Reenvío registrado correctamente." : "Entrega registrada correctamente.";
    ok.style.display = "flex";
  } catch (error) {
    mostrarError(error.message, "avisoEntregaError");
  }
}

async function transicion(tarea, accion) {
  try {
    await apiFetch(`/assignments/${tarea.id}/${accion}`, {
      method: "POST",
      headers: { "X-Role": accion === "start" ? "docente" : "revisor" },
    });
    await cargarDetalle();
  } catch (error) {
    mostrarError(error.message);
  }
}

async function devolver(tarea) {
  const comment = document.getElementById("obs").value.trim();
  if (!comment) {
    mostrarError("La observación es obligatoria para devolver.");
    return;
  }
  try {
    await apiFetch(`/assignments/${tarea.id}/return`, {
      method: "POST",
      headers: { "X-Role": "revisor" },
      body: JSON.stringify({ comment }),
    });
    await cargarDetalle();
  } catch (error) {
    mostrarError(error.message);
  }
}

if (!idAsignacion) {
  document.getElementById("cargando").style.display = "none";
  mostrarError("No se indicó qué asignación mostrar. Vuelve al inbox y elige una tarjeta.");
} else {
  cargarDetalle();
}
