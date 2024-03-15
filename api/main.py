from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter
from prometheus_fastapi_instrumentator import Instrumentator
from prometheus_fastapi_instrumentator.metrics import Info, default

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


instrumentator = Instrumentator()


def endpointCounter() -> Callable[[Info], None]:
    METRIC = Counter(
        "endpoint_counter",
        "Counts the number of requests to an endpoint",
        ["method", "endpoint"],
    )

    def _endpointCounter(info: Info) -> None:
        req = info.request
        METRIC.labels(method=req.method, endpoint=req.url.path).inc()

    return _endpointCounter


instrumentator.add(endpointCounter()).add(default())


instrumentator.instrument(app).expose(app, include_in_schema=False)
