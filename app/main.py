from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import init_db, shutdown_db
from app.routers.pages import router as pages_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await shutdown_db()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_title, lifespan=lifespan)

    template_directory = Path(__file__).resolve().parent / "templates"
    static_directory = Path(__file__).resolve().parent / "static"

    app.state.templates = Jinja2Templates(directory=str(template_directory))
    app.mount("/static", StaticFiles(directory=str(static_directory)), name="static")

    app.include_router(pages_router)
    return app


app = create_app()
