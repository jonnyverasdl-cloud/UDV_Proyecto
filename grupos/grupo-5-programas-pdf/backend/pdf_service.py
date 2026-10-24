"""Arma el PDF institucional del programa a partir de sus datos y secciones."""

import json
from io import BytesIO
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

def flatten_data(value, prefix=""):
    """Pone los datos anidados en una lista de campos fácil de imprimir."""
    if isinstance(value, dict):
        flattened = {}
        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else key
            flattened.update(flatten_data(child, path))
        return flattened
    if isinstance(value, list):
        flattened = {}
        for index, child in enumerate(value):
            flattened.update(flatten_data(child, f"{prefix}[{index}]"))
        return flattened
    return {prefix: value} if prefix else {}

def build_pdf(program, version, approval=None):
    """Arma el documento y devuelve sus bytes para poder descargarlo."""
    # ReportLab construye el documento en memoria para devolverlo como descarga HTTP.
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
        title=f"Programa de curso - {program.get('asignatura', '')}",
        author="Universidad Da Vinci de Guatemala",
    )
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="TituloInstitucional",
        parent=styles["Title"],
        alignment=TA_CENTER,
        textColor=colors.HexColor("#001D4A"),
        fontSize=15,
        leading=19,
        spaceAfter=5 * mm,
    ))
    styles.add(ParagraphStyle(
        name="SeccionPrograma",
        parent=styles["Heading2"],
        textColor=colors.HexColor("#001D4A"),
        fontSize=11,
        leading=14,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    ))
    styles.add(ParagraphStyle(
        name="TextoPrograma",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    ))

    def text(value):
        """Escapa valores de usuario antes de insertarlos en párrafos del PDF."""
        # Escapa el texto para que caracteres del usuario no se interpreten como markup.
        if isinstance(value, (dict, list)):
            return json.dumps(value, ensure_ascii=False)
        return escape(str(value if value is not None else ""))

    general = (
        version.get("secciones", {})
        .get("general", {})
        .get("contenido", {})
    )
    program_pdf = dict(program)
    # Las etiquetas del formulario usan nombres distintos a los de la ficha del programa.
    field_mappings = {
        "programa": "programa_academico",
        "ciclo": "ciclo_academico",
        "anio": "anio",
        "nivel": "nivel_academico",
        "horas": "horas_semanales",
    }
    for field, general_value in general.items():
        program_pdf[field_mappings.get(field, field)] = general_value

    story = [
        Paragraph("UNIVERSIDAD DA VINCI DE GUATEMALA", styles["TituloInstitucional"]),
        Paragraph("PROGRAMA DE CURSO", styles["Heading1"]),
        Spacer(1, 3 * mm),
    ]
    summary = [
        ["Asignatura", text(program_pdf.get("asignatura"))],
        ["Código", text(program_pdf.get("codigo"))],
        ["Programa académico", text(program_pdf.get("programa_academico"))],
        ["Versión", text(version.get("numero_version"))],
        ["Estado", text(version.get("estado", "")).replace("_", " ").upper()],
        ["Departamento", text(program_pdf.get("departamento"))],
        ["Facultad", text(program_pdf.get("facultad"))],
        ["Ciclo", text(program_pdf.get("ciclo_academico"))],
        ["Año", text(program_pdf.get("anio"))],
        ["Nivel", text(program_pdf.get("nivel_academico"))],
        ["Modalidad", text(program_pdf.get("modalidad"))],
        ["Créditos", text(program_pdf.get("creditos"))],
        ["Horas", text(program_pdf.get("horas_semanales"))],
        ["Sede", text(program_pdf.get("sede"))],
    ]
    if approval:
        summary.extend([
            ["Fecha de autorización", text(approval.get("creado_en"))],
            ["Aprobación de origen", text(approval.get("id"))],
        ])
    summary_table = Table(summary, colWidths=[35 * mm, 130 * mm])
    summary_table.setStyle(TableStyle([
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
    story.append(summary_table)

    # Cada sección con contenido se presenta como una tabla independiente.
    for section, data in version.get("secciones", {}).items():
        content = data.get("contenido", {}) if isinstance(data, dict) else {}
        if not content:
            continue

        story.extend([
            Paragraph(section.replace("_", " ").title(), styles["SeccionPrograma"]),
        ])
        rows = []
        for key, value in flatten_data(content).items():
            rows.append([
                Paragraph(key.replace("_", " ").title(), styles["TextoPrograma"]),
                Paragraph(text(value).replace("\n", "<br/>"), styles["TextoPrograma"]),
            ])
        table = Table(rows, colWidths=[45 * mm, 120 * mm], repeatRows=0)
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#A0A0A0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F4F6F8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(table)

    document.build(story)
    return buffer.getvalue()