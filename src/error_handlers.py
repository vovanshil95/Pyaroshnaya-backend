from fastapi.responses import JSONResponse

async def http_exception_handler(request, exception):
    return JSONResponse(
        status_code=exception.status_code,
        content={"message": exception.detail}
    )