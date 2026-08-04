import html

import streamlit as st


def render_hero(
    title: str,
    description: str,
    eyebrow: str | None = None,
) -> None:
    """
    Renderiza o cabeçalho principal de uma página.

    Args:
        title: Título principal.
        description: Texto complementar.
        eyebrow: Texto pequeno exibido acima do título.
    """

    safe_title = html.escape(title)
    safe_description = html.escape(description)
    safe_eyebrow = html.escape(eyebrow) if eyebrow else ""

    eyebrow_html = ""

    if safe_eyebrow:
        eyebrow_html = f"""
            <div style="
                color: #005691;
                font-size: 0.76rem;
                font-weight: 750;
                letter-spacing: 0.09em;
                text-transform: uppercase;
                margin-bottom: 0.65rem;
            ">
                {safe_eyebrow}
            </div>
        """

    st.markdown(
        f"""
        <section style="
            padding: 2.1rem 2.2rem;
            background:
                linear-gradient(
                    135deg,
                    #FFFFFF 0%,
                    #F4F9FC 100%
                );
            border: 1px solid #DCE7EE;
            border-radius: 18px;
            box-shadow: 0 10px 30px rgba(0, 61, 102, 0.06);
            margin-bottom: 1.6rem;
        ">
            {eyebrow_html}

            <h1 style="
                margin: 0;
                color: #17212B;
                font-size: clamp(1.8rem, 4vw, 2.6rem);
                line-height: 1.12;
                letter-spacing: -0.035em;
            ">
                {safe_title}
            </h1>

            <p style="
                margin: 0.9rem 0 0 0;
                max-width: 780px;
                color: #5B6773;
                font-size: 1.02rem;
                line-height: 1.65;
            ">
                {safe_description}
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )
