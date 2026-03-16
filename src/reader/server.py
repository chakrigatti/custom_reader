import pathlib
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from reader.database import init_db
from reader.errors import APIError, api_error_handler, validation_error_handler
from reader.routes import articles, feeds, sync

STATIC_DIR = pathlib.Path(__file__).resolve().parent.parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="Reader API", version="1.0.0", lifespan=lifespan)

app.add_exception_handler(APIError, api_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(feeds.router)
app.include_router(articles.router)
app.include_router(sync.router)


@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html")


if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
