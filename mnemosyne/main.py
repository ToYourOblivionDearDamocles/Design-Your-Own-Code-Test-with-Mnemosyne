from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from mnemosyne.api.routes import router as api_router
from mnemosyne.storage.submissions import init_db
from mnemosyne.ui import APP_HTML

app = FastAPI(title="Mnemosyne")
app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return APP_HTML
