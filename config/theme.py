import streamlit as st
from textwrap import dedent


COLORS = {
    "primary": "#005691",
    "primary_dark": "#003D66",
    "primary_light": "#EAF4FA",
    "background": "#F5F7FA",
    "surface": "#FFFFFF",
    "text": "#17212B",
    "text_secondary": "#5B6773",
    "border": "#DCE3E8",
    "success": "#2E7D32",
    "warning": "#ED8B00",
    "error": "#C62828",
    "info": "#0277BD",
}


def apply_theme() -> None:
    """Aplica o tema visual global do Portal Comercial."""

    st.markdown(
        dedent(
            f"""
        <style>
            /* ==============================
               CONFIGURAÇÕES GERAIS
            ============================== */

            :root {{
                --primary: {COLORS["primary"]};
                --primary-dark: {COLORS["primary_dark"]};
                --primary-light: {COLORS["primary_light"]};
                --background: {COLORS["background"]};
                --surface: {COLORS["surface"]};
                --text: {COLORS["text"]};
                --text-secondary: {COLORS["text_secondary"]};
                --border: {COLORS["border"]};
                --success: {COLORS["success"]};
                --warning: {COLORS["warning"]};
                --error: {COLORS["error"]};
                --info: {COLORS["info"]};
            }}

            html,
            body,
            [class*="css"] {{
                font-family:
                    Inter,
                    -apple-system,
                    BlinkMacSystemFont,
                    "Segoe UI",
                    sans-serif;
            }}

            .stApp {{
                background-color: var(--background);
                color: var(--text);
            }}

            /* ==============================
               CONTEÚDO PRINCIPAL
            ============================== */

            .block-container {{
                max-width: 1440px;
                padding-top: 1.5rem;
                padding-bottom: 3rem;
                padding-left: 2.5rem;
                padding-right: 2.5rem;
            }}

            /* ==============================
               SIDEBAR
            ============================== */

            section[data-testid="stSidebar"] {{
                background-color: var(--surface);
                border-right: 1px solid var(--border);
            }}

            section[data-testid="stSidebar"] > div {{
                padding-top: 1.4rem;
            }}

            /* ==============================
               TÍTULOS
            ============================== */

            h1,
            h2,
            h3,
            h4 {{
                color: var(--text);
                letter-spacing: -0.02em;
            }}

            h1 {{
                font-size: 2rem;
                font-weight: 700;
            }}

            h2 {{
                font-size: 1.45rem;
                font-weight: 650;
            }}

            h3 {{
                font-size: 1.1rem;
                font-weight: 650;
            }}

            /* ==============================
               BOTÕES
            ============================== */

            .stButton > button {{
                min-height: 42px;
                border: 1px solid var(--border);
                border-radius: 10px;
                background-color: var(--surface);
                color: var(--text);
                font-weight: 600;
                transition:
                    border-color 0.2s ease,
                    color 0.2s ease,
                    background-color 0.2s ease,
                    transform 0.2s ease;
            }}

            .stButton > button:hover {{
                border-color: var(--primary);
                color: var(--primary);
                background-color: var(--primary-light);
                transform: translateY(-1px);
            }}

            .stButton > button:focus {{
                box-shadow: 0 0 0 3px rgba(0, 86, 145, 0.15);
            }}

            /* ==============================
               CAMPOS
            ============================== */

            div[data-baseweb="input"] > div,
            div[data-baseweb="select"] > div,
            div[data-baseweb="textarea"] > div {{
                border-radius: 10px;
                border-color: var(--border);
                background-color: var(--surface);
            }}

            div[data-baseweb="input"] > div:focus-within,
            div[data-baseweb="select"] > div:focus-within,
            div[data-baseweb="textarea"] > div:focus-within {{
                border-color: var(--primary);
                box-shadow: 0 0 0 3px rgba(0, 86, 145, 0.12);
            }}

            /* ==============================
               EXPANDERS
            ============================== */

            div[data-testid="stExpander"] {{
                border: 1px solid var(--border);
                border-radius: 12px;
                background-color: var(--surface);
                overflow: hidden;
            }}

            /* ==============================
               ALERTAS
            ============================== */

            div[data-testid="stAlert"] {{
                border-radius: 12px;
            }}

            /* ==============================
               OCULTA ELEMENTOS NATIVOS
            ============================== */

            #MainMenu {{
                visibility: hidden;
            }}

            footer {{
                visibility: hidden;
            }}

            header[data-testid="stHeader"] {{
                background-color: transparent;
            }}

            /* ==============================
               RESPONSIVIDADE
            ============================== */

            @media (max-width: 768px) {{
                .block-container {{
                    padding-top: 1rem;
                    padding-left: 1rem;
                    padding-right: 1rem;
                }}

                h1 {{
                    font-size: 1.65rem;
                }}

                h2 {{
                    font-size: 1.3rem;
                }}
            }}
        </style>
        """
    ),
    unsafe_allow_html=True,
)
