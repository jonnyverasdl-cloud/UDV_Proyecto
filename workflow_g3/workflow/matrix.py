from dataclasses import dataclass

COORDINATOR, TEACHER, REVIEWER, AUTHORITY, SYSTEM = (
    "coordinator", "teacher", "reviewer", "authority", "system")
ROLES = (COORDINATOR, TEACHER, REVIEWER, AUTHORITY, SYSTEM)

STATES = ("draft", "assigned", "in_progress", "submitted", "under_review",
          "returned", "approved", "closed", "cancelled")
ACTIONS = ("publish", "start", "submit", "review", "return",
           "resubmit", "approve", "close", "cancel")


@dataclass(frozen=True)
class Rule:
    from_state: str
    action: str
    to_state: str
    roles: frozenset
    scope: str = None
    unscoped_roles: frozenset = frozenset()
    comment_required: bool = False


def _r(frm, action, to, roles, scope=None, unscoped=(), comment=False):
    return Rule(frm, action, to, frozenset(roles), scope, frozenset(unscoped), comment)


STANDARD = (
    _r("draft",        "publish",  "assigned",     [COORDINATOR],           "task_coordinator"),
    _r("assigned",     "start",    "in_progress",  [TEACHER],               "assignee"),
    _r("in_progress",  "submit",   "submitted",    [TEACHER],               "assignee"),
    _r("submitted",    "review",   "under_review", [REVIEWER],              "task_reviewer"),
    _r("under_review", "return",   "returned",     [REVIEWER],              "task_reviewer", comment=True),
    _r("returned",     "resubmit", "submitted",    [TEACHER],               "assignee"),
    _r("under_review", "approve",  "approved",     [REVIEWER, AUTHORITY],   "task_reviewer", unscoped=[AUTHORITY]),
    _r("approved",     "close",    "closed",       [COORDINATOR, SYSTEM],   "task_coordinator", unscoped=[SYSTEM]),
    _r("draft",        "cancel",   "cancelled",    [COORDINATOR],           "task_coordinator"),
    _r("assigned",     "cancel",   "cancelled",    [COORDINATOR],           "task_coordinator"),
)


SHORT = tuple(r for r in STANDARD if r.action in ("publish", "close", "cancel")) + (
    _r("assigned",  "submit",  "submitted", [TEACHER],             "assignee"),
    _r("submitted", "approve", "approved",  [REVIEWER, AUTHORITY], "task_reviewer", unscoped=[AUTHORITY]),
)


def _index(rules):
    return {(r.from_state, r.action): r for r in rules}


FLOWS = {"standard": _index(STANDARD), "short": _index(SHORT)}


def render_markdown() -> str:
    """Genera la matriz documentada (docs/matriz_estados.md)."""
    names = {COORDINATOR: "Coordinador", TEACHER: "Docente", REVIEWER: "Revisor",
             AUTHORITY: "Autoridad", SYSTEM: "Sistema"}
    scopes = {"assignee": "solo el docente destinatario",
              "task_reviewer": "el revisor designado en la tarea",
              "task_coordinator": "quien creó la tarea o su responsable", None: "-"}
    out = ["# Matriz de estados, acciones y roles", "",
           "Generada desde `workflow/matrix.py`. No editar a mano: ejecutar "
           "`python -m workflow.matrix`.", ""]
    for flow, rules in (("standard", STANDARD), ("short", SHORT)):
        out += [f"## Flujo `{flow}`", "",
                "| Estado actual | Acción | Estado nuevo | Roles | Alcance | Comentario |",
                "| --- | --- | --- | --- | --- | --- |"]
        for r in rules:
            roles = ", ".join(names[x] for x in ROLES if x in r.roles)
            out.append(f"| {r.from_state} | {r.action} | {r.to_state} | {roles} | "
                       f"{scopes[r.scope]} | {'obligatorio' if r.comment_required else '-'} |")
        out.append("")
    out += ["Cualquier otra combinación estado/acción responde **409** sin modificar datos.",
            "Rol no permitido o usuario que no es el destinatario: **403**.",
            "Devolver (`return`) sin comentario: **422**.", ""]
    return "\n".join(out)


if __name__ == "__main__":
    import pathlib
    path = pathlib.Path(__file__).resolve().parent.parent / "docs" / "matriz_estados.md"
    path.write_text(render_markdown(), encoding="utf-8")
    print(f"Escrito {path}")
