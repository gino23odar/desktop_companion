"""Local development API. Run with uvicorn backend.app:create_app --factory"""
import sqlite3
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from .auth import make_auth
from .config import Settings
from .database import Conflict, Database, NotFound
from .models import Activation, ActiveMood, Mood


def create_app(settings: Settings | None = None):
    settings = settings if settings is not None else Settings.from_env()
    db = Database(settings.db_path)
    admin, reader = make_auth(settings)

    @asynccontextmanager
    async def lifespan(_app):
        db.initialize()
        yield

    app = FastAPI(title="Desk Buddy API", version="0.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def prevent_cache(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/v1/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(NotFound)
    async def not_found(_request, exc):
        return JSONResponse(status_code=404, content={"detail": str(exc)})

    @app.exception_handler(Conflict)
    async def conflict(_request, exc):
        return JSONResponse(status_code=409, content={"detail": str(exc)})

    @app.exception_handler(sqlite3.OperationalError)
    async def db_unavailable(_request, _exc):
        return JSONResponse(status_code=503, content={"detail": "Database unavailable"})

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/api/v1/moods", response_model=list[Mood], dependencies=[Depends(admin)])
    def list_moods():
        return db.list_moods()

    @app.post("/api/v1/moods", response_model=Mood, status_code=201, dependencies=[Depends(admin)])
    def create_mood(mood: Mood):
        return db.create(mood)

    @app.get("/api/v1/moods/{mood_id}", response_model=Mood, dependencies=[Depends(admin)])
    def get_mood(mood_id: str):
        return db.get(mood_id)

    @app.put("/api/v1/moods/{mood_id}", response_model=Mood, dependencies=[Depends(admin)])
    def replace_mood(mood_id: str, mood: Mood):
        if mood_id != mood.id:
            raise HTTPException(422, "Path ID must match mood ID")
        return db.replace(mood_id, mood)

    @app.delete("/api/v1/moods/{mood_id}", status_code=204, dependencies=[Depends(admin)])
    def delete_mood(mood_id: str):
        db.delete(mood_id)
        return Response(status_code=204)

    @app.get("/api/v1/active", response_model=ActiveMood, dependencies=[Depends(reader)])
    def get_active():
        return db.active()

    @app.put("/api/v1/active", response_model=ActiveMood, dependencies=[Depends(admin)])
    def activate(selection: Activation):
        return db.activate(selection.mood_id)

    return app
