import streamlit as st


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

    css = f"""
    <style>
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

        .block-container {{
            max-width: 1440px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
            padding-left: 2.5rem;
            padding-right: 2.5rem;
        }}

        section[data-testid="stSidebar"] {{
            background-color: var(--surface);
            border-right: 1px solid var(--border);
        }}

        section[data-testid="stSidebar"] > div {{
            padding-top: 1.4rem;
        }}

        h1,
        h2,
        h3,
        h4 {{
            color: var(--text);
            letter-spacing: -0.02em;
        }}

        .portal-hero {{
            padding: 2.1rem 2.2rem;
            background: linear-gradient(
                135deg,
                #FFFFFF 0%,
                #F4F9FC 100%
            );
            border: 1px solid #DCE7EE;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(0, 61, 102, 0.06);
            margin-bottom: 1.6rem;
        }}

        .portal-hero-eyebrow {{
            color: var(--primary);
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.09em;
            text-transform: uppercase;
            margin-bottom: 0.65rem;
        }}

        .portal-hero-title {{
            margin: 0;
            color: var(--text);
            font-size: clamp(1.8rem, 4vw, 2.6rem);
            line-height: 1.12;
            letter-spacing: -0.035em;
        }}

        .portal-hero-description {{
            margin: 0.9rem 0 0;
            max-width: 780px;
            color: var(--text-secondary);
            font-size: 1.02rem;
            line-height: 1.65;
        }}

        .portal-metric-card {{
            min-height: 160px;
            padding: 1.25rem;
            background-color: var(--surface);
            border: 1px solid var(--border);
            border-radius: 14px;
            box-shadow: 0 4px 16px rgba(0, 61, 102, 0.045);
        }}

        .portal-metric-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .portal-metric-label {{
            color: var(--text-secondary);
            font-size: 0.82rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }}

        .portal-metric-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 38px;
            height: 38px;
            border-radius: 10px;
            background-color: var(--primary-light);
            font-size: 1.15rem;
        }}

        .portal-metric-value {{
            margin-top: 1rem;
            color: var(--text);
            font-size: 1.85rem;
            font-weight: 750;
        }}

        .portal-metric-description {{
            margin-top: 0.4rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.45;
        }}

        .portal-module-card {{
            display: flex;
            align-items: flex-start;
            gap: 0.9rem;
            min-height: 92px;
        }}

        .portal-module-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 44px;
            height: 44px;
            border-radius: 12px;
            background-color: var(--primary-light);
            font-size: 1.3rem;
        }}

        .portal-module-title {{
            color: var(--text);
            font-size: 1rem;
            font-weight: 700;
        }}

        .portal-module-description {{
            margin-top: 0.35rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.45;
        }}

        .portal-sidebar-header {{
            padding: 0.25rem 0 1.4rem;
            border-bottom: 1px solid var(--border);
            margin-bottom: 1.2rem;
        }}

        .portal-sidebar-organization {{
            color: var(--primary);
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }}

        .portal-sidebar-title {{
            color: var(--text);
            font-size: 1.25rem;
            font-weight: 750;
            margin-top: 0.3rem;
        }}

        .portal-search-result {{
            padding: 0.2rem 0;
        }}
        
        .portal-search-result-top {{
            display: flex;
            align-items: center;
            gap: 0.45rem;
            margin-bottom: 0.7rem;
        }}
        
        .portal-search-result-icon {{
            font-size: 1rem;
        }}
        
        .portal-search-result-category {{
            color: var(--primary);
            font-size: 0.74rem;
            font-weight: 750;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }}
        
        .portal-search-result-title {{
            color: var(--text);
            font-size: 1.05rem;
            font-weight: 750;
            line-height: 1.35;
        }}
        
        .portal-search-result-subtitle {{
            margin-top: 0.3rem;
            color: var(--text-secondary);
            font-size: 0.82rem;
            font-weight: 600;
        }}
        
        .portal-search-result-description {{
            margin-top: 0.65rem;
            color: var(--text-secondary);
            font-size: 0.88rem;
            line-height: 1.55;
        }}

                .portal-operadora-card {{
            min-height: 185px;
            padding: 0.25rem 0;
        }}

        .portal-operadora-card-top {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .portal-operadora-icon {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 42px;
            height: 42px;
            border-radius: 12px;
            background-color: var(--primary-light);
            font-size: 1.2rem;
        }}

        .portal-operadora-status {{
            padding: 0.32rem 0.6rem;
            border-radius: 999px;
            background-color: #E3F4E8;
            color: #166534;
            font-size: 0.7rem;
            font-weight: 750;
            text-transform: uppercase;
        }}

        .portal-operadora-name {{
            margin-top: 1rem;
            color: var(--text);
            font-size: 1.08rem;
            font-weight: 750;
            line-height: 1.3;
        }}

        .portal-operadora-full-name {{
            min-height: 40px;
            margin-top: 0.3rem;
            color: var(--text-secondary);
            font-size: 0.82rem;
            line-height: 1.4;
        }}

        .portal-operadora-plans {{
            margin-top: 0.9rem;
            color: var(--text-secondary);
            font-size: 0.84rem;
        }}

        .portal-operadora-plans strong {{
            color: var(--primary);
        }}

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

        div[data-baseweb="input"] > div,
        div[data-baseweb="select"] > div,
        div[data-baseweb="textarea"] > div {{
            border-radius: 10px;
            border-color: var(--border);
            background-color: var(--surface);
        }}

        div[data-testid="stExpander"] {{
            border: 1px solid var(--border);
            border-radius: 12px;
            background-color: var(--surface);
            overflow: hidden;
        }}

        div[data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        #MainMenu {{
            visibility: hidden;
        }}

        footer {{
            visibility: hidden;
        }}

        header[data-testid="stHeader"] {{
            background-color: transparent;
        }}

        @media (max-width: 768px) {{
            .block-container {{
                padding-top: 1rem;
                padding-left: 1rem;
                padding-right: 1rem;
            }}

            .portal-hero {{
                padding: 1.5rem;
            }}

            .portal-hero-title {{
                font-size: 1.65rem;
            }}
        }}
    </style>
    """

    st.html(css)
