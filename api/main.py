from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import router

app = FastAPI(title="Kraken API", swagger_ui_parameters={"persistAuthorization": True})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
