"""Datos de ejemplo para desarrollar sin G1/G3 (README raíz §3).

Se reemplazan por la base de datos real cuando exista, más un segundo docente para probar privacidad.
"""
from datetime import date, timedelta

DOCENTE_1 = 1
DOCENTE_2 = 2


def asignaciones_ejemplo(hoy=None):
    from .inbox import Asignacion

    hoy = hoy or date.today()

    def a(id, docente, title, task_type, status, priority, dias):
        return Asignacion(id, docente, title, task_type, status, priority,
                          hoy + timedelta(days=dias))

    return [
        a(1, DOCENTE_1, "Actualizar programa de Programación Web", "Actualizar programa", "in_progress", "high", 2),
        a(2, DOCENTE_1, "Subir CV actualizado 2026", "Subir ficha o CV", "assigned", "medium", -2),
        a(3, DOCENTE_1, "Factura de septiembre", "Entregar factura", "returned", "high", 1),
        a(4, DOCENTE_1, "Evidencia del laboratorio 1", "Cargar evidencia", "submitted", "medium", -1),
        a(5, DOCENTE_1, "Confirmar asistencia al claustro", "Confirmar actividad", "assigned", "low", 10),
        a(6, DOCENTE_1, "Confirmar horario de tutorías", "Confirmar actividad", "assigned", "urgent", -1),
        a(7, DOCENTE_1, "Evidencia del proyecto integrador", "Cargar evidencia", "approved", "medium", -15),
        a(8, DOCENTE_1, "Actualizar programa de Bases de Datos", "Actualizar programa", "in_progress", "medium", 20),
        # Del otro docente: el docente 1 nunca debe verlas.
        a(9, DOCENTE_2, "Factura privada del docente 2", "Entregar factura", "assigned", "high", 1),
        a(10, DOCENTE_2, "Subir CV del docente 2", "Subir ficha o CV", "returned", "medium", -3),
    ]
