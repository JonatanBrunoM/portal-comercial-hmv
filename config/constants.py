from dataclasses import dataclass


@dataclass(frozen=True)
class AppConfig:
    """Configurações centrais da aplicação."""

    APP_NAME: str = "Portal Comercial"
    ORGANIZATION_NAME: str = "Hospital Moinhos de Vento"

    APP_DESCRIPTION: str = (
        "Informações comerciais, convênios, documentos, portais "
        "e orientações em um único lugar."
    )

    PAGE_ICON: str = "🏥"
    LAYOUT: str = "wide"

    DEFAULT_PAGE: str = "Início"


APP_CONFIG = AppConfig()
