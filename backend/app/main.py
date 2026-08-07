import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import DATA_DIR, FRONTEND_DIR, settings
from .routes import router
from .qingxiaoda import router as qingxiaoda_router
from .terms import terms_index


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version=settings.app_version)
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
