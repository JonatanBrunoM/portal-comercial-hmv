"""Textos informativos editáveis para os cards de planos."""
from __future__ import annotations

from nicegui_app.auth.admin_access import require_current_admin
from nicegui_app.data.supabase_client import rest_select, rest_update

DEFAULTS = {
    "plano_acomodacao": "Enfermaria: leito semiprivativo (compartilhado). Apartamento: leito privativo (individual).",
    "plano_acompanhante": "Conforme estatuto: crianças e adolescentes menores de 18 anos e pessoas com 60 anos ou mais têm direito legal a acompanhante, observadas as condições legais aplicáveis.",
}


def get_plan_help_texts() -> dict[str, str]:
    rows = rest_select("portal_textos_ajuda", select="chave,conteudo", params={"chave": "in.(plano_acomodacao,plano_acompanhante)"})
    result = dict(DEFAULTS)
    for row in rows:
        key = str(row.get("chave") or "")
        value = str(row.get("conteudo") or "").strip()
        if key in result and value:
            result[key] = value
    return result


def save_plan_help_texts(actor: dict, accommodation: str, companion: str) -> None:
    require_current_admin(actor)
    values = {
        "plano_acomodacao": accommodation.strip(),
        "plano_acompanhante": companion.strip(),
    }
    if any(not text or len(text) > 2000 for text in values.values()):
        raise ValueError("Preencha os dois textos (máximo de 2.000 caracteres cada).")
    for key, value in values.items():
        rest_update(
            "portal_textos_ajuda",
            match={"chave": key},
            payload={"conteudo": value},
        )
