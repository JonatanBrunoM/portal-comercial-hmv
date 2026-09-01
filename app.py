from __future__ import annotations

import os
from pathlib import Path

from nicegui import app, ui


BASE_DIR = Path(__file__).resolve().parent
STYLE_PATH = BASE_DIR / "styles" / "nicegui_poc.css"


def load_styles() -> None:
    """Carrega apenas o CSS da POC NiceGUI."""
    ui.add_css(STYLE_PATH.read_text(encoding="utf-8"))


@app.get("/health")
def health() -> dict[str, str]:
    """Endpoint simples para o health check do Render."""
    return {"status": "ok", "application": "portal-comercial-nicegui-poc"}


@ui.page("/")
def index() -> None:
    load_styles()

    with ui.element("main").classes("poc-shell"):
        with ui.element("section").classes("poc-card"):
            ui.label("HOSPITAL MOINHOS DE VENTO").classes("poc-kicker")

            ui.label("Portal Comercial").classes("poc-title")

            ui.label(
                "Nova geração do portal institucional, construída em NiceGUI."
            ).classes("poc-description")

            with ui.row().classes("poc-status"):
                ui.element("span").classes("poc-status-dot")
                ui.label("Ambiente NiceGUI online").classes("poc-status-text")

            ui.separator().classes("poc-separator")

            with ui.row().classes("poc-meta"):
                with ui.column().classes("poc-meta-item"):
                    ui.label("ETAPA").classes("poc-meta-label")
                    ui.label("Fundação técnica").classes("poc-meta-value")

                with ui.column().classes("poc-meta-item"):
                    ui.label("STACK").classes("poc-meta-label")
                    ui.label("Python + NiceGUI").classes("poc-meta-value")

                with ui.column().classes("poc-meta-item"):
                    ui.label("STATUS").classes("poc-meta-label")
                    ui.label("POC").classes("poc-meta-value")


if __name__ in {"__main__", "__mp_main__"}:
    ui.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8080")),
        title="Portal Comercial | NiceGUI POC",
        favicon="🏥",
        reload=False,
        show=False,
    )
