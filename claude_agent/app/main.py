from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api import chat, sessions, news, categories
from app.core.config import settings
from app.db.session import engine, Base

# Import models to ensure they are registered with Base
from app.models import news

def create_app() -> FastAPI:
    app = FastAPI(
        title="Claude Agent",
        description="A simple agent using Claude API with session persistence",
        version="0.1.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")

    # Templates
    templates = Jinja2Templates(directory="app/templates")

    # Database initialization
    @app.on_event("startup")
    def on_startup():
        Base.metadata.create_all(bind=engine)

    # Include routers
    app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
    app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
    app.include_router(news.router, prefix="/api/news", tags=["news"])
    app.include_router(categories.router, prefix="/api/news/categories", tags=["categories"])

    # Root endpoint
    @app.get("/")
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    # News timeline page
    @app.get("/news/timeline")
    async def timeline_page(request: Request):
        return templates.TemplateResponse("timeline.html", {"request": request})

    # News feed sources page
    @app.get("/news/feed-sources")
    async def feed_sources_page(request: Request):
        return templates.TemplateResponse("feed_sources.html", {"request": request})

    # News categories page
    @app.get("/news/categories")
    async def categories_page(request: Request):
        return templates.TemplateResponse("categories.html", {"request": request})

    return app

app = create_app()
