
import json
import os
import tempfile
import threading
from datetime import datetime
from functools import wraps
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_ROOT = PROJECT_ROOT / "frontend"
DATA_FILE = PROJECT_ROOT / "programas.json"
MAX_REQUEST_SIZE = 1_000_000

DATA_LOCK = threading.RLock()
ROLES = {"docente", "coordinador-academico", "decanatura"}


def fecha_actual():
    return datetime.now().astimezone().isoformat(timespec="seconds")


def leer_datos():
    with DATA_LOCK:
        with DATA_FILE.open(encoding="utf-8") as archivo:
            data = json.load(archivo)

        for clave in ("programas", "versiones", "historial"):
            if not isinstance(data.get(clave), list):
                raise ValueError(f"Falta la lista '{clave}' en programas.json")

        return data


def guardar_datos(data):
    with DATA_LOCK:
        temporal = None

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=PROJECT_ROOT,
                prefix=".programas-",
                suffix=".tmp",
                delete=False,
            ) as archivo:
                temporal = Path(archivo.name)
                json.dump(data, archivo, ensure_ascii=False, indent=2)
                archivo.write("\n")

            os.replace(temporal, DATA_FILE)

        except OSError:
            if temporal:
                temporal.unlink(missing_ok=True)
            raise


def buscar_programa(data, programa_id):
    return next(
        (p for p in data["programas"] if p["id"] == programa_id),
        None,
    )


def buscar_version(data, version_id):
    return next(
        (v for v in data["versiones"] if v["id"] == version_id),
        None,
    )


def registrar_historial(data, version, accion, usuario, descripcion):
    data["historial"].append({
        "fecha": fecha_actual(),
        "accion": accion,
        "usuario": usuario,
        "descripcion": descripcion,
        "programa_id": version.get("programa_id"),
        "version_id": version.get("id"),
    })


def siguiente_id(items):
    return max((item["id"] for item in items), default=0) + 1


def sincronizado(metodo):
    @wraps(metodo)
    def ejecutar(*args, **kwargs):
        with DATA_LOCK:
            return metodo(*args, **kwargs)

    return ejecutar


def aplanar_datos(valor, prefijo=""):
    if isinstance(valor, dict):
        resultado = {}
        for clave, contenido in valor.items():
            ruta = f"{prefijo}.{clave}" if prefijo else clave
            resultado.update(aplanar_datos(contenido, ruta))
        return resultado

    if isinstance(valor, list):
        resultado = {}
        for indice, contenido in enumerate(valor):
            ruta = f"{prefijo}[{indice}]"
            resultado.update(aplanar_datos(contenido, ruta))
        return resultado

    return {prefijo: valor} if prefijo else {}


def construir_pdf(programa, version):
    buffer = BytesIO()
    documento = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Programa de curso - {programa.get('asignatura', '')}",
        author="Universidad Da Vinci de Guatemala",
    )
    estilos = getSampleStyleSheet()
    estilos.add(ParagraphStyle(
        name="TituloInstitucional",
        parent=estilos["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#001D4A"),
        fontSize=15,
        leading=19,
        spaceAfter=5 * mm,
    ))
    estilos.add(ParagraphStyle(
        name="SeccionPrograma",
        parent=estilos["Heading2"],
        textColor=colors.HexColor("#001D4A"),
        fontSize=11,
        leading=14,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    ))
    estilos.add(ParagraphStyle(
        name="TextoPrograma",
        parent=estilos["BodyText"],
        fontSize=9,
        leading=12,
    ))

    def texto(valor):
        if isinstance(valor, (dict, list)):
            return json.dumps(valor, ensure_ascii=False)
        return escape(str(valor if valor is not None else ""))

    general = (
        version.get("secciones", {})
        .get("general", {})
        .get("contenido", {})
    )
    programa_pdf = dict(programa)
    equivalencias = {
        "programa": "programa_academico",
        "ciclo": "ciclo_academico",
        "anio": "anio",
        "nivel": "nivel_academico",
        "horas": "horas_semanales",
    }
    for campo, valor_general in general.items():
        programa_pdf[equivalencias.get(campo, campo)] = valor_general

    historia = [
        Paragraph("UNIVERSIDAD DA VINCI DE GUATEMALA", estilos["TituloInstitucional"]),
        Paragraph("PROGRAMA DE CURSO", estilos["Heading1"]),
        Spacer(1, 3 * mm),
    ]
    resumen = [
        ["Asignatura", texto(programa_pdf.get("asignatura"))],
        ["Código", texto(programa_pdf.get("codigo"))],
        ["Programa académico", texto(programa_pdf.get("programa_academico"))],
        ["Versión", texto(version.get("numero_version"))],
        ["Estado", texto(version.get("estado", "")).replace("_", " ").upper()],
        ["Departamento", texto(programa_pdf.get("departamento"))],
        ["Facultad", texto(programa_pdf.get("facultad"))],
        ["Ciclo", texto(programa_pdf.get("ciclo_academico"))],
        ["Año", texto(programa_pdf.get("anio"))],
        ["Nivel", texto(programa_pdf.get("nivel_academico"))],
        ["Modalidad", texto(programa_pdf.get("modalidad"))],
        ["Créditos", texto(programa_pdf.get("creditos"))],
        ["Horas", texto(programa_pdf.get("horas_semanales"))],
        ["Sede", texto(programa_pdf.get("sede"))],
    ]
    tabla_resumen = Table(resumen, colWidths=[35 * mm, 130 * mm])
    tabla_resumen.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E7EDF7")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#001D4A")),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    historia.append(tabla_resumen)

    for seccion, datos in version.get("secciones", {}).items():
        contenido = datos.get("contenido", {}) if isinstance(datos, dict) else {}
        if not contenido:
            continue

        historia.extend([
            Paragraph(seccion.replace("_", " ").title(), estilos["SeccionPrograma"]),
        ])
        filas = []
        for clave, valor in aplanar_datos(contenido).items():
            filas.append([
                Paragraph(clave.replace("_", " ").title(), estilos["TextoPrograma"]),
                Paragraph(texto(valor).replace("\n", "<br/>"), estilos["TextoPrograma"]),
            ])
        tabla = Table(filas, colWidths=[45 * mm, 120 * mm], repeatRows=0)
        tabla.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A0A0A0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F4F6F8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        historia.append(tabla)

    documento.build(historia)
    return buffer.getvalue()


def validar_datos_para_revision(version):
    secciones = version.get("secciones", {})
    general_seccion = secciones.get("general", {})
    responsables_seccion = secciones.get("responsables", {})
    general = (
        general_seccion.get("contenido", {})
        if isinstance(general_seccion, dict)
        else {}
    )
    responsables = (
        responsables_seccion.get("contenido", {})
        if isinstance(responsables_seccion, dict)
        else {}
    )
    campos_obligatorios = {
        "codigo": "Código",
        "asignatura": "Asignatura",
        "programa": "Programa académico",
        "facultad": "Facultad",
        "ciclo": "Ciclo",
        "anio": "Año",
    }
    faltantes = [
        etiqueta
        for campo, etiqueta in campos_obligatorios.items()
        if not str(general.get(campo, "")).strip()
    ]
    if not str(responsables.get("docente", "")).strip():
        faltantes.append("Docente")
    return faltantes


class ProgramaHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(FRONTEND_ROOT), **kwargs)

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def leer_body(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))

            if length <= 0 or length > MAX_REQUEST_SIZE:
                raise ValueError

            body = json.loads(self.rfile.read(length).decode("utf-8"))

            if not isinstance(body, dict):
                raise ValueError

            return body

        except (ValueError, json.JSONDecodeError, UnicodeDecodeError):
            raise ValueError("Envía un objeto JSON válido.")

    def error(self, status, mensaje):
        self.send_json(status, {"error": mensaje})

    def usuario(self, body):
        usuario = body.get("usuario")
        return usuario.strip() if isinstance(usuario, str) else ""

    def validar_rol(self, body, rol_esperado):
        rol = body.get("rol")
        usuario = self.usuario(body)
        if rol not in ROLES or rol != rol_esperado:
            self.error(403, "El rol no tiene permiso para realizar esta acción.")
            return False
        if not usuario:
            self.error(400, "Debes indicar el nombre de la persona responsable.")
            return False
        return True

    def do_GET(self):
        path = urlsplit(self.path).path.rstrip("/") or "/"

        try:
            data = leer_datos()

            # Compatibilidad con la API anterior.
            if path == "/api/programas":
                self.send_json(200, data)
                return

            # Listar programas.
            if path == "/course-programs":
                self.send_json(200, data["programas"])
                return

            # Detalle de programa y sus versiones.
            partes = path.strip("/").split("/")

            if (
                len(partes) == 2
                and partes[0] == "course-programs"
                and partes[1].isdigit()
            ):
                programa = buscar_programa(data, int(partes[1]))

                if not programa:
                    self.error(404, "Programa no encontrado.")
                    return

                versiones = [
                    v for v in data["versiones"]
                    if v["programa_id"] == programa["id"]
                ]

                self.send_json(200, {
                    "programa": programa,
                    "versiones": versiones,
                })
                return

            # Consultar una versión.
            if len(partes) == 2 and partes[0] == "program-versions":
                if not partes[1].isdigit():
                    self.error(400, "ID de versión inválido.")
                    return

                version = buscar_version(data, int(partes[1]))

                if not version:
                    self.error(404, "Versión no encontrada.")
                    return

                self.send_json(200, version)
                return

            # Comparar una versión con la anterior.
            if (
                len(partes) == 3
                and partes[0] == "program-versions"
                and partes[1].isdigit()
                and partes[2] == "changes"
            ):
                version = buscar_version(data, int(partes[1]))

                if not version:
                    self.error(404, "Versión no encontrada.")
                    return

                anteriores = [
                    v for v in data["versiones"]
                    if v["programa_id"] == version["programa_id"]
                    and v["numero_version"] < version["numero_version"]
                ]

                anterior = max(
                    anteriores,
                    key=lambda v: v["numero_version"],
                    default=None,
                )

                if anterior is None:
                    self.send_json(200, {
                        "version": version,
                        "version_anterior": None,
                        "cambios": [],
                    })
                    return

                valores_anteriores = aplanar_datos(
                    anterior.get("secciones", {}),
                    "secciones",
                )
                valores_actuales = aplanar_datos(
                    version.get("secciones", {}),
                    "secciones",
                )
                valores_anteriores["estado"] = anterior.get("estado")
                valores_actuales["estado"] = version.get("estado")

                self.send_json(200, {
                    "version": version["id"],
                    "version_anterior": anterior["id"],
                    "cambios": [
                        {
                            "campo": clave,
                            "anterior": valores_anteriores.get(clave),
                            "actual": valores_actuales.get(clave),
                        }
                        for clave in sorted(
                            set(valores_anteriores) | set(valores_actuales)
                        )
                        if valores_anteriores.get(clave) != valores_actuales.get(clave)
                    ],
                })
                return

            # Descargar el documento institucional como PDF.
            if (
                len(partes) == 3
                and partes[0] == "program-versions"
                and partes[1].isdigit()
                and partes[2] == "pdf"
            ):
                version = buscar_version(data, int(partes[1]))
                if not version:
                    self.error(404, "Versión no encontrada.")
                    return
                programa = buscar_programa(data, version["programa_id"])
                if not programa:
                    self.error(404, "Programa no encontrado.")
                    return

                contenido_pdf = construir_pdf(programa, version)
                nombre = f"programa-{programa['id']}-version-{version['numero_version']}.pdf"
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{nombre}"',
                )
                self.send_header("Content-Length", str(len(contenido_pdf)))
                self.end_headers()
                self.wfile.write(contenido_pdf)
                return

            # Servir frontend.
            if path.startswith("/api/") or path.startswith(
                ("/course-programs", "/program-versions")
            ):
                self.error(404, "Ruta de API no encontrada.")
                return

            if path == "/":
                self.path = "/Demo.html"

            super().do_GET()

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.error(500, str(exc))

    @sincronizado
    def do_POST(self):
        path = urlsplit(self.path).path.rstrip("/")

        try:
            body = self.leer_body()
        except ValueError as exc:
            self.error(400, str(exc))
            return

        try:
            data = leer_datos()
            partes = path.strip("/").split("/")

            # Crear programa.
            if path == "/course-programs":
                if not self.validar_rol(body, "docente"):
                    return
                if not body.get("codigo") or not body.get("asignatura"):
                    self.error(400, "El código y la asignatura son obligatorios.")
                    return

                programa = {
                    clave: valor for clave, valor in body.items()
                    if clave not in ("rol", "usuario")
                }
                programa["id"] = siguiente_id(data["programas"])
                programa["version_actual"] = None
                programa["estado"] = "borrador"

                data["programas"].append(programa)

                version = {
                    "id": siguiente_id(data["versiones"]),
                    "programa_id": programa["id"],
                    "numero_version": 1,
                    "estado": "borrador",
                    "secciones": {},
                    "observaciones": [],
                    "creado_en": fecha_actual(),
                    "actualizado_en": fecha_actual(),
                }

                data["versiones"].append(version)

                registrar_historial(
                    data, version, "Creación",
                    self.usuario(body), "Se creó el programa y su versión 1."
                )

                guardar_datos(data)
                self.send_json(201, {
                    "programa": programa,
                    "version": version,
                })
                return

            # Crear o clonar versión.
            if (
                len(partes) == 3
                and partes[0] == "course-programs"
                and partes[1].isdigit()
                and partes[2] == "versions"
            ):
                programa = buscar_programa(data, int(partes[1]))

                if not programa:
                    self.error(404, "Programa no encontrado.")
                    return
                if not self.validar_rol(body, "coordinador-academico"):
                    return

                versiones = [
                    v for v in data["versiones"]
                    if v["programa_id"] == programa["id"]
                ]

                ultima_version = max(
                    versiones,
                    key=lambda v: v["numero_version"],
                    default=None,
                )
                version_vigente = next(
                    (
                        item for item in versiones
                        if item["numero_version"] == programa.get("version_actual")
                        and item.get("estado") == "vigente"
                    ),
                    None,
                )
                if version_vigente is None:
                    self.error(409, "Solo se puede crear una versión desde una versión vigente.")
                    return
                if (
                    ultima_version is not None
                    and ultima_version["id"] != version_vigente["id"]
                ):
                    self.error(
                        409,
                        "La versión más reciente debe estar autorizada antes de crear otra.",
                    )
                    return

                nueva = {
                    "id": siguiente_id(data["versiones"]),
                    "programa_id": programa["id"],
                    "numero_version": (
                        ultima_version["numero_version"] + 1 if ultima_version else 1
                    ),
                    "estado": "borrador",
                    "secciones": (
                        json.loads(json.dumps(version_vigente.get("secciones", {})))
                        if body.get("clonar", True) else {}
                    ),
                    "observaciones": [],
                    "creado_en": fecha_actual(),
                    "actualizado_en": fecha_actual(),
                }
                responsables = nueva.setdefault("secciones", {}).get("responsables")
                if responsables:
                    responsables["contenido"]["coordinador"] = ""
                    responsables["contenido"]["decanatura"] = ""

                data["versiones"].append(nueva)
                programa["estado"] = "borrador"

                registrar_historial(
                    data, nueva, "Creación de versión",
                    self.usuario(body),
                    f"Se creó la versión {nueva['numero_version']}."
                )

                guardar_datos(data)
                self.send_json(201, nueva)
                return

            # Acciones del flujo académico.
            if (
                len(partes) == 3
                and partes[0] == "program-versions"
                and partes[1].isdigit()
                and partes[2] in ("submit", "return", "approve", "authorize")
            ):
                version = buscar_version(data, int(partes[1]))

                if not version:
                    self.error(404, "Versión no encontrada.")
                    return

                accion = partes[2]
                estado = version.get("estado", "borrador")
                versiones_programa = [
                    item for item in data["versiones"]
                    if item["programa_id"] == version["programa_id"]
                ]
                ultima_version = max(
                    versiones_programa,
                    key=lambda item: item["numero_version"],
                    default=None,
                )
                if ultima_version is None or ultima_version["id"] != version["id"]:
                    self.error(
                        409,
                        "Solo se puede cambiar el estado de la versión más reciente.",
                    )
                    return

                transiciones = {
                    "submit": ("borrador", "en_revision"),
                    "return": ("en_revision", "devuelto"),
                    "approve": ("en_revision", "aprobado"),
                    "authorize": ("aprobado", "vigente"),
                }

                esperado, nuevo_estado = transiciones[accion]
                rol_requerido = {
                    "submit": "docente",
                    "return": "coordinador-academico",
                    "approve": "coordinador-academico",
                    "authorize": "decanatura",
                }[accion]
                if not self.validar_rol(body, rol_requerido):
                    return

                estados_esperados = (
                    ("borrador", "devuelto")
                    if accion == "submit"
                    else (esperado,)
                )

                if estado not in estados_esperados:
                    self.error(
                        409,
                        f"No se puede ejecutar {accion} desde el estado '{estado}'."
                    )
                    return

                if accion == "return":
                    observacion = body.get("observacion")
                    if not isinstance(observacion, str) or not observacion.strip():
                        self.error(400, "Debes indicar una observación no vacía.")
                        return
                if accion == "submit" and not self.usuario(body):
                    self.error(400, "Escribe el nombre del docente antes de enviar a revisión.")
                    return
                if accion == "submit":
                    faltantes = validar_datos_para_revision(version)
                    if faltantes:
                        self.error(
                            400,
                            "Completa los campos obligatorios antes de enviar: "
                            + ", ".join(faltantes),
                        )
                        return

                if accion == "return":
                    version.setdefault("observaciones", []).append({
                        "fecha": fecha_actual(),
                        "usuario": self.usuario(body),
                        "texto": observacion.strip(),
                    })

                responsables = version.setdefault("secciones", {}).setdefault(
                    "responsables",
                    {"usuario": self.usuario(body), "contenido": {}},
                )
                contenido_responsables = responsables.setdefault("contenido", {})
                campo_responsable = {
                    "submit": "docente",
                    "return": "coordinador",
                    "approve": "coordinador",
                    "authorize": "decanatura",
                }[accion]
                contenido_responsables[campo_responsable] = self.usuario(body)

                version["estado"] = nuevo_estado
                version["actualizado_en"] = fecha_actual()

                programa = buscar_programa(data, version["programa_id"])

                if programa:
                    programa["estado"] = nuevo_estado

                if accion == "authorize" and programa:
                    for anterior in data["versiones"]:
                        if (
                            anterior["programa_id"] == programa["id"]
                            and anterior["id"] != version["id"]
                            and anterior.get("estado") == "vigente"
                        ):
                            anterior["estado"] = "reemplazado"
                    programa["version_actual"] = version["numero_version"]

                registrar_historial(
                    data,
                    version,
                    accion.capitalize(),
                    self.usuario(body),
                    body.get("observacion", f"Estado actualizado a {nuevo_estado}."),
                )

                guardar_datos(data)
                self.send_json(200, {
                    "ok": True,
                    "version": version,
                    "programa": programa,
                })
                return

            self.error(404, "Ruta de API no encontrada.")

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.error(500, str(exc))

    @sincronizado
    def do_PUT(self):
        path = urlsplit(self.path).path.rstrip("/")

        try:
            body = self.leer_body()
        except ValueError as exc:
            self.error(400, str(exc))
            return

        try:
            data = leer_datos()

            # Compatibilidad con la API anterior.
            if path == "/api/programas":
                self.error(
                    410,
                    "La actualización completa fue retirada; usa las rutas de programas y versiones.",
                )
                return

            partes = path.strip("/").split("/")

            # Guardar una sección específica.
            if (
                len(partes) == 4
                and partes[0] == "program-versions"
                and partes[1].isdigit()
                and partes[2] == "sections"
            ):
                if partes[3] not in {
                    "responsables",
                    "general",
                    "prerrequisitos",
                    "descripcion",
                    "competencias",
                    "perfil",
                    "metodologia",
                    "contenidos",
                    "bibliografia",
                    "evaluacion",
                }:
                    self.error(404, "Sección de programa no reconocida.")
                    return
                version = buscar_version(data, int(partes[1]))

                if not version:
                    self.error(404, "Versión no encontrada.")
                    return

                if not self.validar_rol(body, "docente"):
                    return
                if not isinstance(body.get("contenido"), dict):
                    self.error(400, "El contenido de la sección debe ser un objeto.")
                    return
                if version.get("estado") not in ("borrador", "devuelto"):
                    self.error(409, "Solo se puede editar un borrador o una versión devuelta.")
                    return

                version.setdefault("secciones", {})[partes[3]] = body
                version["actualizado_en"] = fecha_actual()
                version.setdefault("secciones", {}).setdefault(
                    "responsables", {"usuario": self.usuario(body), "contenido": {}}
                ).setdefault("contenido", {})["docente"] = self.usuario(body)
                if partes[3] == "general":
                    programa = buscar_programa(data, version["programa_id"])
                    equivalencias = {
                        "programa": "programa_academico",
                        "ciclo": "ciclo_academico",
                        "anio": "anio",
                        "nivel": "nivel_academico",
                        "horas": "horas_semanales",
                    }
                    for campo, valor_campo in body["contenido"].items():
                        if campo in {
                            "codigo",
                            "asignatura",
                            "departamento",
                            "facultad",
                            "modalidad",
                            "creditos",
                            "sede",
                        }:
                            programa[campo] = valor_campo
                        elif campo in equivalencias:
                            programa[equivalencias[campo]] = valor_campo
                elif partes[3] == "responsables":
                    programa = buscar_programa(data, version["programa_id"])
                    docente = body["contenido"].get("docente")
                    if docente is not None:
                        programa["profesor"] = docente

                registrar_historial(
                    data, version, "Guardado de sección",
                    self.usuario(body),
                    f"Se guardó la sección '{partes[3]}'."
                )

                guardar_datos(data)
                self.send_json(200, {"ok": True, "version": version})
                return

            # Guardar una versión completa.
            if len(partes) == 2 and partes[0] == "program-versions":
                if not partes[1].isdigit():
                    self.error(400, "ID de versión inválido.")
                    return

                version = buscar_version(data, int(partes[1]))

                if not version:
                    self.error(404, "Versión no encontrada.")
                    return

                if not self.validar_rol(body, "docente"):
                    return
                if version.get("estado") not in ("borrador", "devuelto"):
                    self.error(409, "La versión ya no se puede editar.")
                    return

                campos_protegidos = {
                    "id", "programa_id", "numero_version", "estado"
                }

                for clave, valor in body.items():
                    if clave not in campos_protegidos:
                        version[clave] = valor

                version["actualizado_en"] = fecha_actual()

                registrar_historial(
                    data, version, "Guardado",
                    self.usuario(body), "Se guardaron los datos de la versión."
                )

                guardar_datos(data)
                self.send_json(200, {"ok": True, "version": version})
                return

            self.error(404, "Ruta de API no encontrada.")

        except (OSError, json.JSONDecodeError, ValueError) as exc:
            self.error(500, str(exc))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), ProgramaHandler)
    print("Aplicación disponible en http://127.0.0.1:8000")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido.")
    finally:
        server.server_close()
