from fastapi.responses import JSONResponse


def api_response(
    status_code: int,
    message: str,
    success: bool | None = None,
    error_code: str | None = None,
    data: dict | list | None = None,
):

    return JSONResponse(
        status_code=status_code,
        content={
            "status_code": status_code,
            "message": message,
            "success": int(success) if success is not None else int(status_code < 400),
            "data": data if data is not None else [],
            "error_code": error_code,
        },
    )
