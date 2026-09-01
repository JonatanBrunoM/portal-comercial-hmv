from __future__ import annotations

import os

from nicegui import app, ui

from nicegui_app.pages.home import render_home
from nicegui_app.pages.supabase_test import render_supabase_test
from nicegui_app.theme import apply_theme


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "application": "portal-comercial-nicegui-poc"}


@ui.page("/")
def index() -> None:
    apply_theme()
    render_home()


@ui.page("/supabase-test")
def supabase_test() -> None:
    apply_theme()
    render_supabase_test()


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        title="Portal Comercial | Hospital Moinhos de Vento",
        favicon="🏥",
        reload=False,
        show=False,
    )
