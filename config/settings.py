from dataclasses import dataclass


@dataclass(frozen=True)
class CacheSettings:
    """Tempos de cache em segundos."""

    OPERADORAS: int = 1800
    PLANOS: int = 1800
    PORTAIS: int = 1800
    ELEGIBILIDADE: int = 1800
    DOCUMENTOS: int = 1800
    AUTORIZACOES: int = 1800
    COBERTURAS: int = 1800
    CONTATOS: int = 1800
    CONTINGENCIAS: int = 600
    DICAS: int = 1800
    COMUNICADOS: int = 600
    SEARCH_INDEX: int = 1800


CACHE_SETTINGS = CacheSettings()


SHEETS = {
    "operadoras": "02_OPERADORAS",
    "planos": "03_PLANOS",
    "portais": "04_PORTAIS",
    "elegibilidade": "05_ELEGIBILIDADE",
    "documentos": "06_DOCUMENTOS",
    "autorizacoes": "07_AUTORIZACOES",
    "coberturas": "08_COBERTURAS",
    "contatos": "09_CONTATOS",
    "contingencias": "10_CONTINGENCIAS",
    "dicas": "11_DICAS_OPERACIONAIS",
    "consultores": "12_CONSULTORES",
    "carteiras": "13_CARTEIRAS",
    "comunicados": "14_COMUNICADOS",
    "forum_posts": "15_FORUM_POSTS",
    "forum_comentarios": "16_FORUM_COMENTARIOS",
    "conhecimento": "18_CONHECIMENTO_IA",
}
