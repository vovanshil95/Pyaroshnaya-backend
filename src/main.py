from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from auth.routes import router as auth_router
from questions.routers import router as questions_router
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