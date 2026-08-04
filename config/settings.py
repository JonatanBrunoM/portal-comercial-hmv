from dataclasses import dataclass


@dataclass(frozen=True)
class CacheSettings:
    """Tempos de cache em segundos."""

    OPERADORAS: int = 600
    PLANOS: int = 600
    PORTAIS: int = 600
    DOCUMENTOS: int = 600
    CONTATOS: int = 600
    CONTINGENCIAS: int = 300
    COMUNICADOS: int = 300


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
