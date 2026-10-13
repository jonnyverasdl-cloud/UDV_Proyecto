// =====================================================
// PANTALLA DEL INBOX
// Solo dibuja lo que responde Api.obtenerInbox / Api.obtenerResumen.
// Las reglas de negocio (vencimiento, filtros, orden, paginación) viven
// en la API, no aquí.
// =====================================================

// La API habla en inglés; la pantalla, en español.
const nombresEstado = {
  assigned: "Asignada",
  in_progress: "En progreso",
  submitted: "Entregada",
  under_review: "En revisión",
  returned: "Devuelta",
  approved: "Aprobada",
  closed: "Cerrada",
  cancelled: "Cancelada"
};
const nombresPrioridad = { urgent: "Urgente", high: "Alta", medium: "Media", low: "Baja" };

const el = (id) => document.getElementById(id);

// Todo dato que se meta en innerHTML debe pasar por aquí.
function escapar(valor) {
  return String(valor ?? "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

const textoDias = (n) => (n === 1 ? "1 día" : `${n} días`);
const traducir = (diccionario, clave) => diccionario[clave] ?? clave ?? "—";

// "in_progress" -> "badge-in-progress" (clase de udv.css)
const claseBadge = (estado) => "badge-" + String(estado).replace(/_/g, "-");

// Estado actual de la consulta: se conserva aunque falle una carga
const consulta = { q: "", status: "", page: 1, per_page: 5 };

// ---------- Tarjeta ----------

// El vencimiento se comunica con texto e ícono, no solo con color.
function textoVencimiento(a) {
  const dias = Api.diasRestantes(a.due_at);
  if (dias === null) return `<span class="vence">Sin fecha límite</span>`;
  if (a.due_state === "vencida") {
    return `<span class="vence vence--vencida"><strong>⚠ Vencida</strong> hace ${textoDias(-dias)}</span>`;
  }
  if (a.due_state === "por-vencer") {
    const cuando = dias === 0 ? "hoy" : `en ${textoDias(dias)}`;
    return `<span class="vence vence--por-vencer"><strong>⏰ Por vencer</strong> vence ${cuando}</span>`;
  }
  return `<span class="vence">Vence: ${escapar(a.due_at)}</span>`;
}

function crearTarjeta(a) {
  return `
    <article class="udv-card inbox-tarjeta ${escapar(a.due_state)}">
      <p class="udv-card__category">${escapar(a.task_type)}</p>
      <h3 class="udv-card__title">${escapar(a.title)}</h3>
      <div class="inbox-tarjeta__detalles">
        <span class="udv-badge ${claseBadge(a.status)}">${escapar(traducir(nombresEstado, a.status))}</span>
        <span>Prioridad: ${escapar(traducir(nombresPrioridad, a.priority))}</span>
        ${textoVencimiento(a)}
      </div>
    </article>`;
}

// ---------- Pantalla ----------

function mostrarAviso(html, tipo) {
  el("aviso").innerHTML = html ? `<div class="udv-alert udv-alert-${tipo}" role="${tipo === "danger" ? "alert" : "status"}">${html}</div>` : "";
}

function mostrarContadores(resumen) {
  el("total-pendientes").textContent = resumen.pending;
  el("total-vencidas").textContent = resumen.overdue;
  el("total-por-vencer").textContent = resumen.due_soon;
}

function mostrarPaginacion(r) {
  const paginas = Math.max(1, Math.ceil(r.total / r.per_page));
  el("pagina-actual").textContent = `Página ${r.page} de ${paginas}`;
  el("pagina-anterior").disabled = r.page <= 1;
  el("pagina-siguiente").disabled = r.page >= paginas;
  el("paginacion").hidden = r.total === 0;
}

function mostrarLista(r) {
  el("resultado").textContent = `${r.total} ${r.total === 1 ? "asignación" : "asignaciones"}`;
  mostrarPaginacion(r);
  if (r.total === 0) {
    el("lista").innerHTML = "";
    mostrarAviso("No hay asignaciones que coincidan con la búsqueda.", "info");
    return;
  }
  mostrarAviso("", "info");
  el("lista").innerHTML = r.data.map(crearTarjeta).join("");
}

// Si la carga falla, se avisa y NO se borra lo que ya estaba en pantalla
// ni lo que el usuario escribió en los filtros.
async function cargar() {
  try {
    const [resumen, r] = await Promise.all([Api.obtenerResumen(), Api.obtenerInbox(consulta)]);
    mostrarContadores(resumen);
    mostrarLista(r);
  } catch (error) {
    mostrarAviso(`<span>No se pudo cargar el inbox. Tus filtros se conservaron.</span>
      <button type="button" class="btn-udv btn-udv-primary btn-udv-sm" id="reintentar">Reintentar</button>`, "danger");
  }
}

// ---------- Eventos ----------

let temporizador;
el("buscar").addEventListener("input", (e) => {
  clearTimeout(temporizador);
  temporizador = setTimeout(() => { consulta.q = e.target.value; consulta.page = 1; cargar(); }, 150);
});
el("filtro-estado").addEventListener("change", (e) => { consulta.status = e.target.value; consulta.page = 1; cargar(); });
el("por-pagina").addEventListener("change", (e) => { consulta.per_page = Number(e.target.value); consulta.page = 1; cargar(); });
el("pagina-anterior").addEventListener("click", () => { consulta.page -= 1; cargar(); });
el("pagina-siguiente").addEventListener("click", () => { consulta.page += 1; cargar(); });
// El botón "Reintentar" se crea dentro del aviso, por eso se escucha en el contenedor.
el("aviso").addEventListener("click", (e) => { if (e.target.id === "reintentar") cargar(); });

cargar();
