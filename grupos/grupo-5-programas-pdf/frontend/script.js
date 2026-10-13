
document.addEventListener("DOMContentLoaded", async () => {
  const API = "http://127.0.0.1:8000";
  const programaId = 1;

  const $ = (selector) => document.querySelector(selector);

  const rol = $("#rol");
  const estadoPrograma = $("#estado-programa");
  const numeroVersion = $("#numero-version");
  const estadoGuardado = $("#estado-guardado");

  const docente = $("#docente");
  const nombreDecanatura = $("#nombre-decanatura");
  const nombreCoordinador = $("#nombre-coordinador");

  const guardar = $("#guardar-seccion");
  const crearVersion = $("#crear-version");
  const enviarRevision = $("#enviar-revision");
  const devolver = $("#devolver");
  const aprobar = $("#aprobar");
  const autorizar = $("#autorizar");
  const vistaPreviaPdf = $("#vista-previa-pdf");
  const imprimirPdf = $("#imprimir-pdf");
  const cerrarVistaPrevia = $("#cerrar-vista-previa");
  const documentoPdf = $("#documento-pdf");
  const cancelar = $("#cancelar-cambios");

  const enlacesSecciones = document.querySelectorAll(".nav-secciones a");
  const secciones = document.querySelectorAll(".seccion");
  const camposPrograma = document.querySelectorAll(
    ".seccion input, .seccion textarea, .seccion select",
  );

  let programa = null;
  let versionActual = null;
  let versionId = null;
  let estado = "borrador";
  let version = 1;
  let guardando = false;

  const nombresRol = {
    docente: "Docente",
    "coordinador-academico": "Coordinador académico",
    decanatura: "Decanatura",
  };

  const nombresEstado = {
    borrador: "BORRADOR",
    en_revision: "EN REVISIÓN",
    devuelto: "DEVUELTO",
    aprobado: "APROBADO",
    vigente: "VIGENTE",
    reemplazado: "REEMPLAZADO",
  };

  function usuarioActual() {
    if (rol.value === "docente") {
      return docente.value.trim();
    }

    if (rol.value === "coordinador-academico") {
      return nombreCoordinador.value.trim();
    }

    return nombreDecanatura.value.trim();
  }

  function mostrarMensaje(mensaje) {
    estadoGuardado.textContent = mensaje;
  }

  async function solicitar(ruta, opciones = {}) {
    const respuesta = await fetch(`${API}${ruta}`, {
      ...opciones,
      headers: {
        "Content-Type": "application/json",
        ...opciones.headers,
      },
    });

    const texto = await respuesta.text();
    let resultado = {};

    if (texto) {
      try {
        resultado = JSON.parse(texto);
      } catch {
        resultado = { mensaje: texto };
      }
    }

    if (!respuesta.ok) {
      throw new Error(
        resultado.error ||
          resultado.mensaje ||
          `Error del servidor: ${respuesta.status}`,
      );
    }

    return resultado;
  }

  function enviarJSON(ruta, metodo, datos) {
    return solicitar(ruta, {
      method: metodo,
      body: JSON.stringify(datos),
    });
  }

  function valor(id) {
    return document.getElementById(id)?.value ?? "";
  }

  function asignar(id, dato) {
    const elemento = document.getElementById(id);

    if (!elemento || dato === undefined || dato === null) return;

    if (elemento.tagName === "SELECT") {
      const opcion = [...elemento.options].find(
        (item) => item.value === String(dato) ||
          item.textContent.trim() === String(dato),
      );

      if (opcion) elemento.value = opcion.value;
      return;
    }

    elemento.value = dato;
  }

  function contenidoDe(versionDatos, nombre) {
    return versionDatos?.secciones?.[nombre]?.contenido || {};
  }

  function capturarGeneral() {
    return {
      codigo: valor("codigo"),
      asignatura: valor("asignatura"),
      programa: valor("programa"),
      departamento: valor("departamento"),
      facultad: valor("facultad"),
      area_formacion: valor("area-formacion"),
      pensum: valor("pensum"),
      ciclo: valor("ciclo"),
      anio: valor("anio"),
      nivel: valor("nivel"),
      modalidad: valor("modalidad"),
      creditos: valor("creditos"),
      horas: valor("horas"),
      sede: valor("sede"),
    };
  }

  function capturarPrerrequisitos() {
    const filas = [...document.querySelectorAll("#prerrequisitos tbody tr")];

    return {
      asignaturas: filas.map((fila) => {
        const controles = fila.querySelectorAll("input");

        return {
          asignatura: controles[0]?.value || "",
          codigo: controles[1]?.value || "",
          orden: controles[2]?.value || "",
        };
      }),
    };
  }

  function capturarSecciones() {
    return {
      responsables: {
        docente: docente.value,
        decanatura: nombreDecanatura.value,
        coordinador: nombreCoordinador.value,
      },

      general: capturarGeneral(),

      prerrequisitos: capturarPrerrequisitos(),

      descripcion: {
        texto: valor("descripcion-texto"),
      },

      competencias: {
        general: valor("competencia-general"),
        especificas: valor("competencias-especificas"),
      },

      perfil: {
        codigo: valor("perfil-codigo"),
        contribucion: valor("perfil-contribucion"),
      },

      metodologia: {
        texto: valor("metodologia-texto"),
      },

      contenidos: {
        texto: valor("contenidos-texto"),
      },

      bibliografia: {
        texto: valor("bibliografia-texto"),
      },

      evaluacion: {
        parcial: valor("evaluacion-parcial"),
        final: valor("evaluacion-final"),
        proyecto: valor("evaluacion-proyecto"),
      },
    };
  }

  function cargarSecciones(datosVersion) {
    const general = contenidoDe(datosVersion, "general");
    const responsables = contenidoDe(datosVersion, "responsables");
    const prerrequisitos = contenidoDe(datosVersion, "prerrequisitos");
    const descripcion = contenidoDe(datosVersion, "descripcion");
    const competencias = contenidoDe(datosVersion, "competencias");
    const perfil = contenidoDe(datosVersion, "perfil");
    const metodologia = contenidoDe(datosVersion, "metodologia");
    const contenidos = contenidoDe(datosVersion, "contenidos");
    const bibliografia = contenidoDe(datosVersion, "bibliografia");
    const evaluacion = contenidoDe(datosVersion, "evaluacion");

    // Los datos del programa sirven como valores iniciales.
    asignar("codigo", programa?.codigo || "PW-001");
    asignar("asignatura", programa?.asignatura || "Programación Web");
    asignar(
      "programa",
      programa?.programa_academico || "Ingeniería en Sistemas",
    );
    asignar("departamento", programa?.departamento || "Tecnología");
    asignar("facultad", programa?.facultad || "Ingeniería");
    asignar("area-formacion", programa?.area_formacion || "");
    asignar("pensum", programa?.pensum || "");
    asignar("ciclo", programa?.ciclo_academico || "Segundo ciclo");
    asignar("anio", programa?.anio || 2026);
    asignar("nivel", programa?.nivel_academico || "Licenciatura");
    asignar("modalidad", programa?.modalidad || "Presencial");
    asignar("creditos", programa?.creditos ?? 4);
    asignar("horas", programa?.horas_semanales ?? 64);
    asignar("sede", programa?.sede || "Campus Central");

    // Los valores guardados en la sección tienen prioridad.
    Object.entries(general).forEach(([campo, dato]) => {
      const equivalencias = {
        programa: "programa",
        ciclo: "ciclo",
        anio: "anio",
        nivel: "nivel",
        horas: "horas",
      };

      asignar(equivalencias[campo] || campo, dato);
    });

    asignar(
      "docente",
      responsables.docente || programa?.profesor || "",
    );
    asignar("nombre-decanatura", responsables.decanatura ?? "");
    asignar("nombre-coordinador", responsables.coordinador ?? "");

    asignar("descripcion-texto", descripcion.texto ?? "");
    asignar("competencia-general", competencias.general ?? "");
    asignar("competencias-especificas", competencias.especificas ?? "");
    asignar("perfil-codigo", perfil.codigo ?? "");
    asignar("perfil-contribucion", perfil.contribucion ?? "");
    asignar("metodologia-texto", metodologia.texto ?? "");
    asignar("contenidos-texto", contenidos.texto ?? "");
    asignar("bibliografia-texto", bibliografia.texto ?? "");
    asignar("evaluacion-parcial", evaluacion.parcial ?? "");
    asignar("evaluacion-final", evaluacion.final ?? "");
    asignar("evaluacion-proyecto", evaluacion.proyecto ?? "");

    if (Array.isArray(prerrequisitos.asignaturas)) {
      cargarFilasPrerrequisitos(prerrequisitos.asignaturas);
    }
  }

  function cargarFilasPrerrequisitos(filas) {
    const cuerpo = $("#prerrequisitos tbody");
    cuerpo.replaceChildren();

    filas.forEach((dato) => {
      const fila = document.createElement("tr");

      [
        ["text", dato.asignatura],
        ["text", dato.codigo],
        ["number", dato.orden],
      ].forEach(([tipo, contenido]) => {
        const celda = document.createElement("td");
        const input = document.createElement("input");

        input.type = tipo;
        input.value = contenido ?? "";
        celda.append(input);
        fila.append(celda);
      });

      cuerpo.append(fila);
    });
  }

  async function cargarPrograma(id) {
    const resultado = await solicitar(`/course-programs/${id}`);

    programa = resultado.programa || resultado;
    const versiones = resultado.versiones || [];

    if (!programa) {
      throw new Error("No se encontró el programa solicitado.");
    }

    // Priorizar un borrador o una versión devuelta para continuar editando.
    const editables = versiones.filter((item) =>
      ["borrador", "devuelto"].includes(item.estado),
    );

    const seleccionada =
      editables.sort(
        (a, b) =>
          (b.numero_version || 0) - (a.numero_version || 0),
      )[0] ||
      versiones.find(
        (item) =>
          item.numero_version === programa.version_actual &&
          item.estado === "vigente",
      ) ||
      versiones.sort(
        (a, b) =>
          (b.numero_version || 0) - (a.numero_version || 0),
      )[0];

    if (seleccionada) {
      await cargarVersion(seleccionada.id);
    } else {
      throw new Error("El programa todavía no tiene versiones.");
    }
  }

  async function cargarVersion(id) {
    const datos = await solicitar(`/program-versions/${id}`);

    versionActual = datos;
    versionId = datos.id ?? id;
    version = datos.numero_version ?? 1;
    estado = datos.estado || "borrador";

    cargarSecciones(datos);
    actualizarEstado();
  }

  async function guardarEnServidor() {
    if (!versionId) {
      throw new Error("No hay una versión seleccionada para guardar.");
    }

    const seccionesCapturadas = capturarSecciones();

    for (const [nombre, contenido] of Object.entries(seccionesCapturadas)) {
      await enviarJSON(
        `/program-versions/${versionId}/sections/${nombre}`,
        "PUT",
        {
          usuario: usuarioActual(),
          rol: rol.value,
          contenido,
        },
      );
    }

    versionActual = await solicitar(`/program-versions/${versionId}`);
    estado = versionActual.estado || estado;

    actualizarEstado();
    mostrarMensaje("Borrador guardado en el servidor.");
  }

  async function ejecutarAccion(accion, mensaje, datos = {}) {
    if (!versionId) {
      throw new Error("No hay una versión seleccionada.");
    }

    await enviarJSON(`/program-versions/${versionId}/${accion}`, "POST", {
      usuario: usuarioActual(),
      rol: rol.value,
      ...datos,
    });

    await cargarVersion(versionId);
    mostrarMensaje(mensaje);
  }

  // Navegación entre secciones.
  enlacesSecciones.forEach((enlace) => {
    enlace.addEventListener("click", (evento) => {
      evento.preventDefault();

      const id = enlace.getAttribute("href").substring(1);

      enlacesSecciones.forEach((item) => item.classList.remove("activa"));
      secciones.forEach((item) => item.classList.remove("activa"));

      enlace.classList.add("activa");
      document.getElementById(id)?.classList.add("activa");
    });
  });

  rol.addEventListener("change", () => {
    actualizarEstado();
    mostrarMensaje("Rol seleccionado: " + nombresRol[rol.value]);
  });

  // Guardar todas las secciones de la versión.
  guardar.addEventListener("click", async () => {
    if (rol.value !== "docente") {
      alert("Solo el docente puede guardar el borrador.");
      return;
    }

    if (!["borrador", "devuelto"].includes(estado)) {
      alert("El programa no se puede modificar en este estado.");
      return;
    }

    await conCarga(async () => {
      await guardarEnServidor();
    });
  });

  enviarRevision.addEventListener("click", async () => {
    if (rol.value !== "docente") {
      alert("Solo el docente puede enviar el programa a revisión.");
      return;
    }

    if (!docente.value.trim()) {
      alert("Escribe el nombre del docente antes de enviar a revisión.");
      return;
    }

    if (!["borrador", "devuelto"].includes(estado)) {
      alert("Solo puedes enviar un borrador o un programa devuelto.");
      return;
    }

    await conCarga(async () => {
      await guardarEnServidor();

      await ejecutarAccion("submit", "Programa enviado a revisión.");
    });
  });

  devolver.addEventListener("click", async () => {
    if (rol.value !== "coordinador-academico") {
      alert("Solo Coordinación académica puede devolver el programa.");
      return;
    }

    if (estado !== "en_revision") {
      alert("El programa debe estar en revisión.");
      return;
    }

    if (!nombreCoordinador.value.trim()) {
      alert("Escribe el nombre del coordinador académico.");
      return;
    }

    const observacion = prompt("Indica por qué se devuelve el programa.");
    if (observacion === null) return;
    if (!observacion.trim()) {
      alert("Debes indicar una observación para devolver el programa.");
      return;
    }

    await conCarga(() =>
      ejecutarAccion("return", "Programa devuelto al docente.", {
        observacion: observacion.trim(),
      }),
    );
  });

  aprobar.addEventListener("click", async () => {
    if (rol.value !== "coordinador-academico") {
      alert("Solo Coordinación académica puede aprobar el programa.");
      return;
    }

    if (estado !== "en_revision") {
      alert("El programa debe estar en revisión.");
      return;
    }

    if (!nombreCoordinador.value.trim()) {
      alert("Escribe el nombre del coordinador académico.");
      return;
    }

    await conCarga(() =>
      ejecutarAccion("approve", "Programa aprobado."),
    );
  });

  autorizar.addEventListener("click", async () => {
    if (rol.value !== "decanatura") {
      alert("Solo Decanatura puede autorizar una versión.");
      return;
    }

    if (estado !== "aprobado") {
      alert("El programa debe estar aprobado antes de autorizarlo.");
      return;
    }

    if (!nombreDecanatura.value.trim()) {
      alert("Escribe el nombre de la Decanatura.");
      return;
    }

    await conCarga(() =>
      ejecutarAccion("authorize", "Versión autorizada."),
    );
  });

  crearVersion.addEventListener("click", async () => {
    if (rol.value !== "coordinador-academico") {
      alert("Solo Coordinación académica puede crear una versión.");
      return;
    }

    if (estado !== "vigente") {
      alert("Debes partir de una versión autorizada.");
      return;
    }

    if (!nombreCoordinador.value.trim()) {
      alert("Escribe el nombre del coordinador académico.");
      return;
    }

    await conCarga(async () => {
      const nueva = await enviarJSON(
        `/course-programs/${programaId}/versions`,
        "POST",
        {
          usuario: usuarioActual(),
          rol: rol.value,
          clonar: true,
        },
      );

      if (!nueva.id) {
        throw new Error("El servidor no devolvió el ID de la nueva versión.");
      }

      await cargarVersion(nueva.id);
      mostrarMensaje(`Se creó la versión ${version} como borrador.`);
    });
  });

  // Cancelar: volver a cargar la versión desde el servidor.
  cancelar.addEventListener("click", async () => {
    if (!confirm("¿Deseas descartar los cambios que no has guardado?")) return;

    await conCarga(async () => {
      await cargarVersion(versionId);
      mostrarMensaje("Se cargaron nuevamente los últimos datos guardados.");
    });
  });

  async function conCarga(funcion) {
    if (guardando) return;

    guardando = true;
    actualizarInterfaz();
    mostrarMensaje("Procesando...");

    try {
      await funcion();
    } catch (error) {
      console.error(error);
      mostrarMensaje("Error: " + error.message);
      alert("No se pudo completar la acción.\n\n" + error.message);
    } finally {
      guardando = false;
      actualizarEstado();
    }
  }

  function actualizarEstado() {
    estadoPrograma.className = "udv-badge";
    estadoPrograma.textContent = nombresEstado[estado] || estado.toUpperCase();

    const clases = {
      borrador: "badge-draft",
      en_revision: "badge-under-review",
      devuelto: "badge-returned",
      aprobado: "badge-approved",
      vigente: "badge-authorized",
      reemplazado: "badge-superseded",
    };

    estadoPrograma.classList.add(clases[estado] || "badge-draft");
    numeroVersion.textContent = "Versión " + version;

    actualizarInterfaz();
    actualizarEdicionResponsables();
  }

  function actualizarEdicionResponsables() {
    const puedeEditar =
      rol.value === "docente" &&
      ["borrador", "devuelto"].includes(estado);

    camposPrograma.forEach((control) => {
      if (control instanceof HTMLSelectElement) {
        control.disabled = !puedeEditar;
      } else if (
        control instanceof HTMLInputElement ||
        control instanceof HTMLTextAreaElement
      ) {
        control.readOnly = !puedeEditar;
      }
    });

    docente.readOnly = !puedeEditar;

    nombreDecanatura.readOnly = !(
      rol.value === "decanatura" && estado === "aprobado"
    );

    nombreCoordinador.readOnly = !(
      rol.value === "coordinador-academico" &&
      ["en_revision", "vigente"].includes(estado)
    );
  }

  function actualizarInterfaz() {
    const botones = [
      guardar,
      crearVersion,
      enviarRevision,
      devolver,
      aprobar,
      autorizar,
      cancelar,
    ];

    botones.forEach((boton) => {
      boton.style.display = "none";
      boton.disabled = guardando;
    });
    vistaPreviaPdf.style.display = "inline-block";
    imprimirPdf.style.display = "none";
    cerrarVistaPrevia.style.display = "none";
    imprimirPdf.hidden = true;
    cerrarVistaPrevia.hidden = true;

    if (document.body.classList.contains("vista-previa-pdf")) {
      vistaPreviaPdf.style.display = "none";
      imprimirPdf.style.display = "inline-block";
      cerrarVistaPrevia.style.display = "inline-block";
      imprimirPdf.hidden = false;
      cerrarVistaPrevia.hidden = false;
      return;
    }

    if (rol.value === "docente" && ["borrador", "devuelto"].includes(estado)) {
      guardar.style.display = "inline-block";
      enviarRevision.style.display = "inline-block";
      cancelar.style.display = "inline-block";
    }

    if (rol.value === "decanatura" && estado === "aprobado") {
      autorizar.style.display = "inline-block";
    }

    if (rol.value === "coordinador-academico") {
      if (estado === "en_revision") {
        devolver.style.display = "inline-block";
        aprobar.style.display = "inline-block";
      }

      if (estado === "vigente") {
        crearVersion.style.display = "inline-block";
      }
    }

    [vistaPreviaPdf, imprimirPdf, cerrarVistaPrevia].forEach((boton) => {
      boton.disabled = guardando;
    });
  }

  // Vista previa de impresión: no sustituye todavía un PDF generado por el backend.
  function crearElemento(etiqueta, clase, texto) {
    const elemento = document.createElement(etiqueta);
    if (clase) elemento.className = clase;
    if (texto !== undefined) elemento.textContent = texto;
    return elemento;
  }

  function construirDocumentoPdf() {
    documentoPdf.replaceChildren();

    const encabezado = crearElemento("header", "pdf-encabezado");
    const institucion = crearElemento("div", "pdf-institucion");
    institucion.append(
      crearElemento("h2", "", "UNIVERSIDAD DA VINCI DE GUATEMALA"),
      crearElemento("p", "", valor("facultad") || "Facultad académica"),
    );

    const metadatos = crearElemento("div", "pdf-metadatos");
    metadatos.append(
      crearElemento("p", "", `Versión: ${version}`),
      crearElemento("p", "", `Fecha: ${new Date().toLocaleDateString("es-GT")}`),
      crearElemento("p", "", `Estado: ${estadoPrograma.textContent.trim()}`),
    );

    encabezado.append(institucion, metadatos);

    documentoPdf.append(
      encabezado,
      crearElemento("h1", "pdf-titulo", "PROGRAMA DE CURSO"),
      crearElemento("p", "pdf-asignatura", valor("asignatura")),
      crearElemento(
        "p",
        "pdf-leyenda",
        estado === "vigente"
          ? "Documento autorizado"
          : "Documento de prueba - sin autorización vigente",
      ),
    );

    secciones.forEach((seccion) => {
      const copia = seccion.cloneNode(true);
      copia.classList.remove("activa");
      copia.classList.add("pdf-seccion");
      copia.removeAttribute("id");

      copia.querySelectorAll("[id]").forEach((elemento) =>
        elemento.removeAttribute("id"),
      );

      copia.querySelectorAll("label[for]").forEach((etiqueta) =>
        etiqueta.removeAttribute("for"),
      );

      copia.querySelectorAll("input, textarea, select").forEach((control) => {
        const dato =
          control instanceof HTMLSelectElement
            ? control.selectedOptions[0]?.textContent.trim() || ""
            : control.value;

        control.replaceWith(crearElemento("span", "pdf-valor", dato));
      });

      documentoPdf.append(copia);
    });

    const autorizacion = crearElemento("section", "pdf-seccion");
    autorizacion.append(crearElemento("h3", "", "Autorización"));

    const tabla = crearElemento("table", "pdf-tabla-autorizacion");
    const cuerpo = crearElemento("tbody");

    [
      ["Elaborado por", docente.value.trim()],
      ["Facultad", valor("facultad")],
      ["Decanatura", nombreDecanatura.value.trim()],
      ["Coordinador académico", nombreCoordinador.value.trim()],
      ["Fecha", new Date().toLocaleDateString("es-GT")],
    ].forEach(([campo, dato]) => {
      const fila = crearElemento("tr");
      fila.append(
        crearElemento("th", "", campo),
        crearElemento("td", "", dato),
      );
      cuerpo.append(fila);
    });

    tabla.append(cuerpo);
    autorizacion.append(tabla);
    documentoPdf.append(autorizacion);

    const firmas = crearElemento("footer", "pdf-firmas");

    ["Elaborado por", "Decanatura", "Coordinador académico"].forEach((cargo) => {
      const firma = crearElemento("div", "pdf-firma");
      firma.append(
        crearElemento("div", "pdf-linea-firma"),
        crearElemento("span", "", cargo),
      );
      firmas.append(firma);
    });

    documentoPdf.append(firmas);
  }

  vistaPreviaPdf.addEventListener("click", () => {
    construirDocumentoPdf();
    documentoPdf.hidden = false;
    document.body.classList.add("vista-previa-pdf");
    actualizarInterfaz();
    mostrarMensaje("Vista previa lista para imprimir.");
  });

  imprimirPdf.addEventListener("click", () =>
    conCarga(async () => {
      const respuesta = await fetch(
        `${API}/program-versions/${versionId}/pdf`,
      );

      if (!respuesta.ok) {
        const resultado = await respuesta.json().catch(() => ({}));
        throw new Error(
          resultado.error || `No se pudo generar el PDF (${respuesta.status}).`,
        );
      }

      const archivo = await respuesta.blob();
      if (archivo.type !== "application/pdf") {
        throw new Error("El servidor no devolvió un documento PDF.");
      }

      const url = URL.createObjectURL(archivo);
      const enlace = document.createElement("a");
      enlace.href = url;
      enlace.download = `programa-${programaId}-version-${version}.pdf`;
      document.body.append(enlace);
      enlace.click();
      enlace.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      mostrarMensaje("PDF descargado.");
    }),
  );

  cerrarVistaPrevia.addEventListener("click", () => {
    document.body.classList.remove("vista-previa-pdf");
    documentoPdf.hidden = true;
    actualizarInterfaz();
    mostrarMensaje("Vista previa cerrada.");
  });

  try {
    mostrarMensaje("Conectando con la API...");
    await cargarPrograma(programaId);
    mostrarMensaje("Programa cargado desde el servidor.");
  } catch (error) {
    console.error(error);
    mostrarMensaje("No se pudo cargar el programa: " + error.message);
    alert(
      "No se pudo cargar el programa desde la API.\n\n" +
        error.message +
        "\n\nVerifica que el servidor esté activo en 127.0.0.1:8000.",
    );
  }
});
