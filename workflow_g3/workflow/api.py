import os
from typing import Optional

from fastapi import Depends, FastAPI, Header, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from . import events, tasks, transitions
from .db import connect, init_db
from .errors import NotFound, Unauthorized, WorkflowError
from .matrix import STANDARD, SHORT

PREFIX = "/api/v1"


class TaskTypeIn(BaseModel):
    code: str
    name: str
    requires_evidence: bool = False
    evidence_type: Optional[str] = None
    flow: str = "standard"


class TaskIn(BaseModel):
    type_id: int
    title: str
    description: str = ""
    priority: str = "medium"
    due_date: str
    responsible_id: Optional[int] = None
    reviewer_id: Optional[int] = None


class TaskPatch(BaseModel):
    type_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    responsible_id: Optional[int] = None
    reviewer_id: Optional[int] = None


class RecipientsIn(BaseModel):
    mode: str                       
    user_ids: Optional[list[int]] = None
    campus: Optional[str] = None
    unit: Optional[str] = None


class ActionIn(BaseModel):
    comment: Optional[str] = None


class CancelIn(BaseModel):
    reason: Optional[str] = None


def create_app(db_path: Optional[str] = None) -> FastAPI:
    db_path = db_path or os.getenv("WORKFLOW_DB", "workflow.db")
    boot = connect(db_path)
    init_db(boot)
    boot.close()

    app = FastAPI(title="Workflow y tareas (Grupo 3)", version="1.0.0",
                  openapi_url=f"{PREFIX}/openapi.json", docs_url=f"{PREFIX}/docs")

    # ------------------------------------------------------------ errores
    @app.exception_handler(WorkflowError)
    async def _workflow_error(_: Request, exc: WorkflowError):
        return JSONResponse(exc.to_dict(), status_code=exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
                   for e in exc.errors()]
        return JSONResponse({"error": {"code": "validation_error",
                                       "message": "Solicitud inválida", "details": details}},
                            status_code=422)

    # ------------------------------------------------------ dependencias
    def get_conn():
        conn = connect(db_path)
        try:
            yield conn
        finally:
            conn.close()

    def current_user(x_user_id: Optional[int] = Header(default=None),
                     conn=Depends(get_conn)) -> dict:
        if x_user_id is None:
            raise Unauthorized("Falta el header X-User-Id (auth provisional)")
        row = conn.execute("SELECT * FROM users WHERE id = ? AND active = 1",
                           (x_user_id,)).fetchone()
        if row is None:
            raise Unauthorized("Usuario inválido")
        return dict(row)

    @app.get(f"{PREFIX}/me", tags=["auth"])
    def get_me(user=Depends(current_user)):
        return {k: user[k] for k in ("id", "name", "role", "campus", "unit")}

    # ------------------------------------------------------- task types
    @app.get(f"{PREFIX}/task-types", tags=["task-types"])
    def get_task_types(page: int = Query(1), page_size: int = Query(20),
                       conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.list_task_types(conn, page, page_size)

    @app.post(f"{PREFIX}/task-types", status_code=201, tags=["task-types"])
    def post_task_type(body: TaskTypeIn, conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.create_task_type(conn, user, body.model_dump())

    # ------------------------------------------------------------ tasks
    @app.get(f"{PREFIX}/tasks", tags=["tasks"])
    def get_tasks(status: Optional[str] = None, page: int = Query(1),
                  page_size: int = Query(20), conn=Depends(get_conn),
                  user=Depends(current_user)):
        return tasks.list_tasks(conn, user, status, page, page_size)

    @app.post(f"{PREFIX}/tasks", status_code=201, tags=["tasks"])
    def post_task(body: TaskIn, conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.create_task(conn, user, body.model_dump())

    @app.get(PREFIX + "/tasks/{task_id}", tags=["tasks"])
    def get_task(task_id: int, conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.get_task(conn, user, task_id)

    @app.patch(PREFIX + "/tasks/{task_id}", tags=["tasks"])
    def patch_task(task_id: int, body: TaskPatch, conn=Depends(get_conn),
                   user=Depends(current_user)):
        return tasks.update_task(conn, user, task_id, body.model_dump(exclude_unset=True))

    @app.post(PREFIX + "/tasks/{task_id}/recipients", tags=["tasks"])
    def post_recipients(task_id: int, body: RecipientsIn, conn=Depends(get_conn),
                        user=Depends(current_user)):
        return tasks.set_recipients(conn, user, task_id, body.model_dump(exclude_none=True))

    @app.post(PREFIX + "/tasks/{task_id}/publish", tags=["tasks"])
    def post_publish(task_id: int, conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.publish_task(conn, user, task_id)

    @app.post(PREFIX + "/tasks/{task_id}/cancel", tags=["tasks"])
    def post_cancel(task_id: int, body: CancelIn = CancelIn(), conn=Depends(get_conn),
                    user=Depends(current_user)):
        return tasks.cancel_task(conn, user, task_id, body.reason)

    @app.get(PREFIX + "/tasks/{task_id}/assignments", tags=["tracking"])
    def get_task_assignments(task_id: int, status: Optional[str] = None,
                             page: int = Query(1), page_size: int = Query(20),
                             conn=Depends(get_conn), user=Depends(current_user)):
        return tasks.list_task_assignments(conn, user, task_id, status, page, page_size)

    # ------------------------------------------------------ assignments
    @app.get(f"{PREFIX}/assignments/inbox", tags=["assignments"])
    def get_inbox(status: Optional[str] = None, page: int = Query(1),
                  page_size: int = Query(20), conn=Depends(get_conn),
                  user=Depends(current_user)):
        return tasks.inbox(conn, user, status, page, page_size)

    @app.get(PREFIX + "/assignments/{assignment_id}/history", tags=["assignments"])
    def get_history(assignment_id: int, conn=Depends(get_conn), user=Depends(current_user)):
        return {"items": tasks.get_history(conn, user, assignment_id)}

    @app.post(PREFIX + "/assignments/{assignment_id}/actions/{action}", tags=["assignments"])
    def post_action(assignment_id: int, action: str, body: ActionIn = ActionIn(),
                    conn=Depends(get_conn), user=Depends(current_user)):
        return transitions.perform(conn, assignment_id, action, user, body.comment)

    # ----------------------------------------------- eventos y matriz
    @app.get(f"{PREFIX}/events", tags=["events"])
    def get_events(after_id: int = Query(0), limit: int = Query(100, ge=1, le=500),
                   conn=Depends(get_conn), user=Depends(current_user)):
        if user["role"] not in ("authority", "system"):
            raise NotFound("Recurso no disponible para tu rol")   # lo consume el Grupo 6
        return {"items": events.list_events(conn, after_id, limit)}

    @app.get(f"{PREFIX}/workflow/matrix", tags=["workflow"])
    def get_matrix():
        def dump(rules):
            return [{"from": r.from_state, "action": r.action, "to": r.to_state,
                     "roles": sorted(r.roles), "scope": r.scope,
                     "comment_required": r.comment_required} for r in rules]
        return {"standard": dump(STANDARD), "short": dump(SHORT)}

    from fastapi.staticfiles import StaticFiles
    front = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")
    if os.path.isdir(front):
        app.mount("/", StaticFiles(directory=front, html=True), name="frontend")

    return app

app = None  # uvicorn: `uvicorn workflow.api:create_app --factory`
