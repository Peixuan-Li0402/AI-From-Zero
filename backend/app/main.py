import logging
import secrets
import time

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import DATA_DIR, FRONTEND_DIR, settings
from .routes import router
from .qingxiaoda import router as qingxiaoda_router
from .terms import terms_index


logger = logging.getLogger("ai_from_zero.qingxiaoda")


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)

    @app.middleware("http")
    async def trace_qingxiaoda_requests(request: Request, call_next):
        if request.url.path not in {
            "/models",
            "/chat/completions",
            "/v1/models",
            "/v1/chat/completions",
        }:
            return await call_next(request)

        request_id = secrets.token_hex(6)
        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "qxd_request id=%s method=%s path=%s status=500",
                request_id,
                request.method,
                request.url.path,
            )
            raise
        elapsed_ms = round((time.perf_counter() - started) * 1000)
        response.headers["X-AFZ-Request-ID"] = request_id
        logger.info(
            "qxd_request id=%s method=%s path=%s status=%s elapsed_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="frontend")
    app.include_router(router)
    app.include_router(qingxiaoda_router)
    return app


app = create_app()


def run() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    print("AI-From-Zero backend starting")
    print(f"URL: http://localhost:{settings.app_port}")
    print(f"LLM provider: {settings.llm_provider}")
    print(f"LLM model: {settings.llm_model}")
    print(f"LLM configured: {settings.llm_configured}")
    print(f"Qingxiaoda Agent configured: {settings.qxd_configured}")
    print(f"Qingxiaoda model: {settings.qxd_model_id}")
    print(f"Term index entries: {len(terms_index)}")
    uvicorn.run(app, host=settings.app_host, port=settings.app_port, log_level="info")
