from dataclasses import dataclass


@dataclass(frozen=True)
class CacheSettings:
    """Tempos de cache em segundos para dados do Supabase."""

    OPERADORAS: int = 1800
    PLANOS: int = 1800
    LOCAIS_ATENDIMENTO: int = 1800
    TIPOS_ATENDIMENTO: int = 1800
    PLANO_LOCAIS: int = 1800
    PORTAIS: int = 1800
    ELEGIBILIDADE: int = 1800
    DOCUMENTOS: int = 1800
    AUTORIZACOES: int = 1800
    COBERTURAS: int = 1800
    CONTATOS: int = 1800
    CONTINGENCIAS: int = 600
    DICAS: int = 1800
    COMUNICADOS: int = 600
    CONSULTORES: int = 1800
    CARTEIRAS: int = 1800
    FORUM: int = 600
    CONHECIMENTO: int = 1800
    SEARCH_INDEX: int = 1800


CACHE_SETTINGS = CacheSettings()


DATASETS = {
    "operadoras": "operadoras",
    "planos": "planos",
    "locais_atendimento": "locais_atendimento",
    "tipos_atendimento": "tipos_atendimento",
    "plano_locais": "plano_locais",
    "portais": "portais",
    "elegibilidade": "elegibilidade",
    "documentos": "documentos",
    "autorizacoes": "autorizacoes",
    "coberturas": "coberturas",
    "contatos": "contatos",
    "contingencias": "contingencias",
    "dicas_operacionais": "dicas_operacionais",
    "consultores": "consultores",
    "carteiras": "carteiras",
    "comunicados": "comunicados",
    "forum_posts": "forum_posts",
    "forum_comentarios": "forum_comentarios",
    "conhecimento": "conhecimento_ia",
}
