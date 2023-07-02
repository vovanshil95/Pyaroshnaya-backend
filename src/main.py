from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from users.routers import router as users_router
from config import ORIGINS

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(users_router)
