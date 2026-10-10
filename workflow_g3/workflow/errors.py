class WorkflowError(Exception):
    status_code = 400
    code = "error"

    def __init__(self, message, details=None, code=None):
        super().__init__(message)
        self.message = message
        self.details = details
        if code:
            self.code = code

    def to_dict(self):
        body = {"code": self.code, "message": self.message}
        if self.details is not None:
            body["details"] = self.details
        return {"error": body}


class Unauthorized(WorkflowError):
    status_code = 401
    code = "unauthorized"


class Forbidden(WorkflowError):
    status_code = 403
    code = "forbidden"


class NotFound(WorkflowError):
    status_code = 404
    code = "not_found"


class Conflict(WorkflowError):
    status_code = 409
    code = "conflict"


class ValidationFailed(WorkflowError):
    status_code = 422
    code = "validation_error"
