import streamlit as st


COLORS = {
    "primary": "#005691",
    "primary_dark": "#003D66",
    "primary_light": "#EAF4FA",
    "background": "#F4F7F9",
    "surface": "#FFFFFF",
    "surface_soft": "#F8FAFB",
    "text": "#17212B",
    "text_secondary": "#5B6773",
    "text_muted": "#7C8B96",
    "border": "#D7E1E7",
    "border_strong": "#C6D5DE",
}


def apply_theme() -> None:
    css = f"""
    <style>
        :root {{
            --portal-primary: {COLORS["primary"]};
            --portal-primary-dark: {COLORS["primary_dark"]};
            --portal-primary-light: {COLORS["primary_light"]};
            --portal-background: {COLORS["background"]};
            --portal-surface: {COLORS["surface"]};
            --portal-surface-soft: {COLORS["surface_soft"]};
            --portal-text: {COLORS["text"]};
            --portal-text-secondary: {COLORS["text_secondary"]};
            --portal-text-muted: {COLORS["text_muted"]};
            --portal-border: {COLORS["border"]};
            --portal-border-strong: {COLORS["border_strong"]};

            --sidebar-rail: clamp(64px, 5vw, 76px);
            --sidebar-open: min(290px, 88vw);
            --content-max: 1320px;
            --page-pad: clamp(0.9rem, 2vw, 1.65rem);
        }}

        /* =========================================================
           BASE
           ========================================================= */

        html,
        body,
        .stApp,
        [data-testid="stAppViewContainer"] {{
            background: var(--portal-background) !important;
            color: var(--portal-text) !important;
        }}

        html,
        body,
        [class*="css"],
        .stApp {{
            font-family:
                Inter,
                -apple-system,
                BlinkMacSystemFont,
                "Segoe UI",
                Roboto,
                Helvetica,
                Arial,
                sans-serif !important;
        }}

        header[data-testid="stHeader"],
        [data-testid="stToolbar"],
        [data-testid="stDecoration"] {{
            display: none !important;
        }}

        [data-testid="stAppViewContainer"] {{
            padding-top: 0 !important;
        }}

        .block-container {{
            width: min(100%, var(--content-max)) !important;
            max-width: var(--content-max) !important;
            padding:
                clamp(1rem, 2vw, 1.35rem)
                var(--page-pad)
                clamp(2rem, 4vw, 3rem) !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            color: var(--portal-text) !important;
            letter-spacing: -0.025em;
        }}

        /* =========================================================
           BOTÕES GERAIS
           ========================================================= */

        main .stButton > button {{
            min-height: 44px !important;
            border-radius: clamp(10px, 1vw, 12px) !important;
            border: 1px solid var(--portal-border-strong) !important;
            background: var(--portal-surface) !important;
            color: var(--portal-text) !important;
            font-size: clamp(.8rem, .75vw, .88rem) !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
            box-shadow: none !important;
            white-space: normal !important;
            transition:
                transform .10s ease,
                border-color .10s ease,
                background .10s ease,
                box-shadow .10s ease !important;
        }}

        main .stButton > button *,
        main .stButton > button p,
        main .stButton > button span {{
            color: inherit !important;
            -webkit-text-fill-color: currentColor !important;
        }}

        main .stButton > button:hover {{
            transform: translateY(-1px);
            border-color: #9FC4D9 !important;
            background: #F8FCFE !important;
            color: var(--portal-primary-dark) !important;
            box-shadow: 0 6px 16px rgba(0, 86, 145, .07) !important;
        }}

        main .stButton > button[kind="primary"] {{
            border-color: var(--portal-primary) !important;
            background: var(--portal-primary) !important;
            color: #FFFFFF !important;
        }}

        /* =========================================================
           CAMPOS
           ========================================================= */

        [data-testid="stTextInput"] div[data-baseweb="input"],
        [data-testid="stNumberInput"] div[data-baseweb="input"],
        [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
        [data-testid="stMultiSelect"] div[data-baseweb="select"] > div,
        [data-testid="stDateInput"] div[data-baseweb="input"],
        [data-testid="stTextArea"] textarea {{
            border-color: var(--portal-border-strong) !important;
            border-radius: 11px !important;
            background: var(--portal-surface) !important;
            color: var(--portal-text) !important;
            box-shadow: none !important;
        }}

        /* =========================================================
           SIDEBAR
           Desktop: rail compacta que abre em overlay.
           Tablet/mobile: rail compacta e rolável; não fica expandida fixa.
           ========================================================= */

        section[data-testid="stSidebar"] {{
            width: var(--sidebar-rail) !important;
            min-width: var(--sidebar-rail) !important;
            max-width: var(--sidebar-rail) !important;
            overflow: visible !important;
            background: transparent !important;
            border: 0 !important;
            z-index: 99999 !important;
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            width: var(--sidebar-rail) !important;
            min-width: var(--sidebar-rail) !important;
            max-width: var(--sidebar-rail) !important;
            height: 100% !important;
            overflow-x: hidden !important;
            overflow-y: auto !important;
            overscroll-behavior: contain;
            scrollbar-width: thin;
            background: var(--portal-surface) !important;
            border-right: 1px solid var(--portal-border) !important;
            box-shadow: 5px 0 16px rgba(13,38,56,.045);
            transition:
                width .09s ease-out,
                min-width .09s ease-out,
                max-width .09s ease-out,
                box-shadow .09s ease-out !important;
        }}

        @media (hover: hover) and (pointer: fine) and (min-width: 901px) {{
            section[data-testid="stSidebar"]:hover > div:first-child,
            section[data-testid="stSidebar"]:focus-within > div:first-child {{
                width: var(--sidebar-open) !important;
                min-width: var(--sidebar-open) !important;
                max-width: var(--sidebar-open) !important;
                box-shadow: 14px 0 34px rgba(13,38,56,.13);
            }}
        }}

        section[data-testid="stSidebar"] [data-testid="stSidebarCollapseButton"],
        section[data-testid="stSidebar"] button[kind="header"] {{
            display: none !important;
        }}

        .portal-sidebar-shell {{
            width: var(--sidebar-open);
            min-width: var(--sidebar-open);
        }}

        .portal-sidebar-header {{
            width: var(--sidebar-open) !important;
            min-height: clamp(66px, 7vw, 74px) !important;
            display: flex !important;
            align-items: center !important;
            padding-inline: clamp(10px, 1vw, 15px) !important;
            border-bottom: 1px solid var(--portal-border);
            box-sizing: border-box;
        }}

        .portal-sidebar-brandmark {{
            display: flex;
            align-items: center;
            gap: clamp(10px, 1vw, 14px);
            min-width: 0;
        }}

        .portal-sidebar-brand-icon {{
            width: clamp(40px, 3vw, 46px) !important;
            min-width: clamp(40px, 3vw, 46px) !important;
            height: clamp(40px, 3vw, 46px) !important;
            flex: 0 0 clamp(40px, 3vw, 46px) !important;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: clamp(10px, 1vw, 13px);
            background: linear-gradient(145deg, var(--portal-primary), var(--portal-primary-dark));
            color: #FFFFFF !important;
            font-weight: 850;
            box-shadow: 0 6px 15px rgba(0,86,145,.18);
        }}

        .portal-sidebar-brand-copy,
        .portal-sidebar-section-label,
        .portal-sidebar-account-label,
        .portal-sidebar-user-copy,
        .portal-sidebar-footer,
        .portal-sidebar-nav-text {{
            opacity: 0;
            pointer-events: none;
            transition: opacity .05s linear !important;
        }}

        @media (hover: hover) and (pointer: fine) and (min-width: 901px) {{
            section[data-testid="stSidebar"]:hover .portal-sidebar-brand-copy,
            section[data-testid="stSidebar"]:hover .portal-sidebar-section-label,
            section[data-testid="stSidebar"]:hover .portal-sidebar-account-label,
            section[data-testid="stSidebar"]:hover .portal-sidebar-user-copy,
            section[data-testid="stSidebar"]:hover .portal-sidebar-footer,
            section[data-testid="stSidebar"]:hover .portal-sidebar-nav-text,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-brand-copy,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-section-label,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-account-label,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-user-copy,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-footer,
            section[data-testid="stSidebar"]:focus-within .portal-sidebar-nav-text {{
                opacity: 1;
                pointer-events: auto;
            }}
        }}

        .portal-sidebar-organization {{
            color: var(--portal-primary) !important;
            font-size: clamp(.56rem, .55vw, .62rem);
            font-weight: 850;
            letter-spacing: .075em;
            text-transform: uppercase;
        }}

        .portal-sidebar-title {{
            margin-top: 2px;
            color: var(--portal-text) !important;
            font-size: clamp(.86rem, .9vw, .98rem);
            font-weight: 800;
        }}

        .portal-sidebar-section-label,
        .portal-sidebar-account-label {{
            width: calc(var(--sidebar-open) - 2rem);
            margin:
                clamp(10px, 1vw, 13px)
                0
                5px
                clamp(12px, 1.25vw, 18px);
            color: var(--portal-text-muted) !important;
            font-size: .58rem;
            font-weight: 850;
            letter-spacing: .105em;
        }}

        .portal-sidebar-nav {{
            width: var(--sidebar-open);
            display: flex;
            flex-direction: column;
            gap: 2px;
            padding-inline: clamp(5px, .5vw, 7px);
            box-sizing: border-box;
        }}

        .portal-sidebar-nav-item {{
            width: calc(var(--sidebar-open) - clamp(10px, 1vw, 14px));
            min-height: 44px;
            display: grid;
            grid-template-columns: clamp(42px, 4vw, 48px) minmax(0, 1fr);
            align-items: center;
            padding: 0;
            border: 1px solid transparent;
            border-radius: 11px;
            text-decoration: none !important;
            color: #425765 !important;
            background: transparent;
            overflow: hidden;
            box-sizing: border-box;
            transition: background .08s linear, color .08s linear, border-color .08s linear;
        }}

        .portal-sidebar-nav-item:hover {{
            background: #EFF7FB;
            color: var(--portal-primary-dark) !important;
        }}

        .portal-sidebar-nav-item.is-active {{
            background: #E2F1FA;
            color: var(--portal-primary-dark) !important;
            border-color: #C7E1F0;
            box-shadow: inset 3px 0 0 var(--portal-primary);
        }}

        .portal-sidebar-nav-icon {{
            width: 100%;
            height: 44px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: currentColor !important;
        }}

        .portal-sidebar-nav-icon svg {{
            width: clamp(19px, 1.5vw, 21px);
            height: clamp(19px, 1.5vw, 21px);
            fill: none;
            stroke: currentColor;
            stroke-width: 1.8;
            stroke-linecap: round;
            stroke-linejoin: round;
            overflow: visible;
        }}

        .portal-sidebar-nav-text {{
            min-width: 0;
            overflow: hidden;
            text-overflow: ellipsis;
            color: inherit !important;
            font-size: clamp(.78rem, .8vw, .85rem);
            font-weight: 680;
            white-space: nowrap;
        }}

        .portal-sidebar-separator {{
            width: calc(var(--sidebar-open) - 14px);
            height: 1px;
            margin: 12px 7px 3px;
            background: var(--portal-border);
        }}

        .portal-sidebar-user-compact {{
            width: calc(var(--sidebar-open) - 14px);
            min-height: 52px;
            display: grid;
            grid-template-columns: clamp(42px, 4vw, 48px) minmax(0, 1fr);
            align-items: center;
            margin: 0 7px 4px;
            padding: 0;
            overflow: hidden;
        }}

        .portal-sidebar-avatar,
        .portal-sidebar-avatar-fallback {{
            width: clamp(38px, 3vw, 44px) !important;
            min-width: clamp(38px, 3vw, 44px) !important;
            height: clamp(38px, 3vw, 44px) !important;
            justify-self: center;
            border-radius: 50% !important;
        }}

        .portal-sidebar-avatar {{
            object-fit: cover !important;
            border: 2px solid #E0EAF0;
        }}

        .portal-sidebar-avatar-fallback {{
            display: flex;
            align-items: center;
            justify-content: center;
            background: #DDEEF8;
            color: var(--portal-primary-dark) !important;
            font-weight: 850;
        }}

        .portal-sidebar-user-name {{
            max-width: 100%;
            overflow: hidden;
            text-overflow: ellipsis;
            color: var(--portal-text) !important;
            font-size: .77rem;
            font-weight: 760;
            white-space: nowrap;
        }}

        .portal-sidebar-user-role {{
            margin-top: 2px;
            color: var(--portal-text-muted) !important;
            font-size: .66rem;
        }}

        section[data-testid="stSidebar"] .stButton {{
            width: var(--sidebar-open) !important;
        }}

        section[data-testid="stSidebar"] .stButton > button {{
            width: calc(var(--sidebar-open) - 14px) !important;
            margin-inline: 7px !important;
        }}

        .portal-sidebar-footer {{
            width: calc(var(--sidebar-open) - 2rem);
            margin: 10px 0 20px 20px;
            color: #8B99A3 !important;
            font-size: .63rem;
        }}

        /* =========================================================
           HOME
           ========================================================= */

        .portal-home-hero-v3 {{
            min-height: clamp(250px, 28vw, 306px);
            display: grid;
            grid-template-columns: minmax(0, 1.55fr) minmax(min(285px, 100%), .72fr);
            gap: clamp(1.25rem, 3vw, 2.2rem);
            align-items: center;
            padding: clamp(1.5rem, 3vw, 2.75rem) clamp(1.4rem, 3.3vw, 3rem);
            border-radius: clamp(18px, 2vw, 25px);
            background:
                radial-gradient(circle at 75% 12%, rgba(38,146,205,.26), transparent 24%),
                radial-gradient(circle at 98% 92%, rgba(255,255,255,.09), transparent 29%),
                linear-gradient(135deg, #005691 0%, #004B7E 47%, #003D66 100%);
            box-shadow: 0 20px 48px rgba(0,61,102,.16);
            overflow: hidden;
        }}

        .portal-home-title {{
            margin: .52rem 0 0;
            max-width: 18ch;
            color: #FFFFFF !important;
            font-size: clamp(2rem, 4.1vw, 3.55rem);
            line-height: 1.02;
            letter-spacing: -.052em;
        }}

        .portal-home-title span {{
            display: block;
            color: #AEDDFA !important;
        }}

        .portal-home-description {{
            max-width: 62ch;
            margin: .95rem 0 0;
            color: #E8F4FA !important;
            font-size: clamp(.86rem, 1vw, .98rem);
            line-height: 1.58;
        }}

        .portal-home-pulse {{
            min-width: 0;
            padding: clamp(1rem, 1.4vw, 1.25rem);
            border: 1px solid rgba(255,255,255,.18);
            border-radius: 20px;
            background: rgba(255,255,255,.10);
        }}

        .portal-command-heading {{
            margin: clamp(1.35rem, 2.5vw, 1.8rem) auto .72rem;
            text-align: center;
        }}

        .portal-command-title {{
            margin-top: .15rem;
            color: var(--portal-text) !important;
            font-size: clamp(1.45rem, 2.8vw, 2.15rem);
            font-weight: 820;
            letter-spacing: -.035em;
        }}

        .portal-command-subtitle {{
            width: min(100%, 680px);
            margin: .25rem auto 0;
            padding-inline: .5rem;
            color: var(--portal-text-secondary) !important;
            font-size: clamp(.75rem, .9vw, .82rem);
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) {{
            width: min(100%, 1040px);
            margin: 0 auto .72rem;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"])
        div[data-baseweb="input"] {{
            min-height: clamp(54px, 5.5vw, 62px) !important;
            display: flex !important;
            align-items: center !important;
            overflow: visible !important;
            border: 1px solid #C5D5DF !important;
            border-radius: clamp(14px, 1.5vw, 18px) !important;
            background: var(--portal-surface) !important;
            box-shadow: 0 12px 30px rgba(13,38,56,.085) !important;
        }}

        [data-testid="stTextInput"]:has(input[aria-label="Pesquisa global"]) input {{
            width: 100% !important;
            height: auto !important;
            min-height: 0 !important;
            padding:
                clamp(15px, 1.5vw, 18px)
                clamp(14px, 1.5vw, 18px) !important;
            margin: 0 !important;
            line-height: 1.35 !important;
            font-size: clamp(.85rem, 1vw, .96rem) !important;
            color: #173447 !important;
            -webkit-text-fill-color: #173447 !important;
        }}

        .portal-home-quick-wrap {{
            width: min(100%, 1040px);
            margin: 0 auto 1.25rem;
        }}

        .portal-home-quick-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(180px, 100%), 1fr));
            gap: clamp(.5rem, 1vw, .72rem);
        }}

        .portal-quick-card {{
            min-width: 0;
            min-height: clamp(76px, 7vw, 88px);
            display: grid;
            grid-template-columns: clamp(34px, 3.5vw, 40px) minmax(0, 1fr) auto;
            align-items: center;
            gap: clamp(.5rem, 1vw, .75rem);
            padding: clamp(.7rem, 1vw, .9rem);
            border: 1px solid #D4E1E8;
            border-radius: clamp(13px, 1.3vw, 16px);
            background: linear-gradient(180deg, #FFFFFF 0%, #F7FBFD 100%);
            box-shadow: 0 5px 16px rgba(13,38,56,.05);
            color: #173447 !important;
            text-decoration: none !important;
        }}

        .portal-quick-copy strong {{
            color: inherit !important;
            font-size: clamp(.74rem, .8vw, .81rem);
            font-weight: 790;
        }}

        .portal-quick-copy small {{
            color: #71818D !important;
            font-size: clamp(.58rem, .65vw, .65rem);
            line-height: 1.25;
        }}

        .portal-home-section-title {{
            margin-top: .12rem;
            color: var(--portal-text) !important;
            font-size: clamp(1.35rem, 2vw, 1.58rem);
            font-weight: 810;
        }}

        .portal-explore-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(min(280px, 100%), 1fr));
            gap: clamp(.65rem, 1vw, .9rem);
        }}

        .portal-explore-link {{
            min-height: clamp(148px, 14vw, 168px);
            display: flex;
            flex-direction: column;
            padding: clamp(.95rem, 1.2vw, 1.18rem);
            border: 1px solid #D8E3E9;
            border-radius: clamp(13px, 1.3vw, 16px);
            background: #FFFFFF;
            color: #17212B !important;
            text-decoration: none !important;
            box-shadow: 0 4px 14px rgba(13,38,56,.045);
        }}

        /* =========================================================
           BREAKPOINTS
           ========================================================= */

        @media (max-width: 1100px) {{
            .portal-home-hero-v3 {{
                grid-template-columns: 1fr;
            }}

            .portal-home-pulse {{
                display: grid;
                grid-template-columns: 1fr;
            }}
        }}

        @media (max-width: 900px) {{
            /* Em telas menores não existe hover confiável.
               A sidebar continua como rail e pode ser rolada verticalmente. */
            section[data-testid="stSidebar"] {{
                width: var(--sidebar-rail) !important;
                min-width: var(--sidebar-rail) !important;
                max-width: var(--sidebar-rail) !important;
            }}

            section[data-testid="stSidebar"] > div:first-child {{
                width: var(--sidebar-rail) !important;
                min-width: var(--sidebar-rail) !important;
                max-width: var(--sidebar-rail) !important;
                overflow-y: auto !important;
            }}

            .block-container {{
                padding-left: clamp(.8rem, 2vw, 1rem) !important;
                padding-right: clamp(.8rem, 2vw, 1rem) !important;
            }}

            .portal-home-pulse {{
                display: none;
            }}
        }}

        @media (max-width: 640px) {{
            :root {{
                --sidebar-rail: 60px;
            }}

            .portal-sidebar-header {{
                padding-inline: 8px !important;
            }}

            .portal-sidebar-brand-icon {{
                width: 40px !important;
                min-width: 40px !important;
                height: 40px !important;
                flex-basis: 40px !important;
            }}

            .portal-home-hero-v3 {{
                min-height: 0;
                padding: 1.4rem 1.15rem;
            }}

            .portal-home-title {{
                max-width: 100%;
                font-size: clamp(1.8rem, 8vw, 2.25rem);
            }}

            .portal-home-hero-tags {{
                display: none;
            }}

            .portal-home-quick-grid,
            .portal-explore-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
    """

    st.html(css)
