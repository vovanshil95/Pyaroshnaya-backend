from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from auth.routes import router as auth_router
from questions.routers import router as questions_router
from history.routers import router as history_router
from users.routers import router as users_router
from files.routers import router as files_router
from admin.routers import router as admin_router
from templates.routers import router as template_router
from payment.routers import router as payment_router
from config import ORIGINS
from error_handlers import http_exception_handler

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.add_exception_handler(HTTPException, http_exception_handler)
app.include_router(auth_router)
app.include_router(questions_router)
app.include_router(history_router)
app.include_router(users_router)
app.include_router(files_router)
app.include_router(admin_router)
app.include_router(template_router)
app.include_router(payment_router)

def custom_openapi():
    openapi_schema = get_openapi(
        title='FastAPI',
        version='0.1.0',
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
        }
    }
    openapi_schema["security"] = [{"Bearer": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi
