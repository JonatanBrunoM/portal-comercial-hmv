from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from config.settings import CACHE_SETTINGS, DATASETS
from core.supabase_repository import get_supabase_client

logger = logging.getLogger(__name__)


COLUMN_ALIASES: dict[str, dict[str, str]] = {
    "operadoras": {
        "id": "ID Operadora", "codigo": "Código", "nome": "Operadora",
        "nome_curto": "Nome curto", "status": "Status", "observacoes": "Observações",
        "logo_url": "Logo URL", "site_url": "Site URL",
    },
    "planos": {
        "id": "ID Plano", "codigo": "Código", "operadora_id": "ID Operadora",
        "nome": "Plano", "nome_padronizado": "Nome padronizado",
        "tipo_plano": "Tipo do plano", "observacao_resumida": "Observação resumida",
        "status": "Status",
    },
    "portais": {
        "id": "ID Portal", "codigo": "Código", "operadora_id": "ID Operadora",
        "plano_id": "ID Plano", "local_id": "ID Local", "nome": "Nome do portal",
        "tipo": "Tipo", "url": "URL", "exige_login": "Exige login",
        "instrucao_acesso": "Instrução de acesso", "observacoes": "Observações",
        "status": "Status", "dica_geral_acesso": "Dica geral de acesso",
    },
    "elegibilidade": {
        "id": "ID Elegibilidade", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento": "Tipo atendimento", "tipo_atendimento_id": "ID Tipo Atendimento",
        "local_id": "ID Local", "elegivel": "Elegível",
        "documento_necessario": "Documento necessário", "como_verificar": "Como verificar",
        "observacoes": "Observações", "status": "Status",
    },
    "documentos": {
        "id": "ID Documento", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento": "Tipo atendimento", "tipo_atendimento_id": "ID Tipo Atendimento",
        "local_id": "ID Local", "documento": "Documento", "obrigatorio": "Obrigatório",
        "validade_dias": "Validade em dias", "validade_em_dias": "Validade em dias",
        "original_copia": "Original/Cópia", "aceita_email": "Aceita e-mail",
        "aceita_fax": "Aceita fax", "aceita_outro_convenio": "Aceita outro convênio",
        "arquivo_url": "Link Documento", "link": "Link Documento", "url": "Link Documento",
        "observacoes": "Observações", "status": "Status", "status_revisao": "Status revisão",
    },
    "autorizacoes": {
        "id": "ID Autorização", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento": "Tipo atendimento", "tipo_atendimento_id": "ID Tipo Atendimento",
        "local_id": "ID Local", "necessita_autorizacao": "Necessita autorização",
        "pre_pos": "Pré/Pós", "quem_solicita": "Quem solicita",
        "meio_solicitacao": "Meio de solicitação", "prazo_retorno_horas": "Prazo retorno horas",
        "observacoes": "Observações", "status": "Status",
    },
    "coberturas": {
        "id": "ID Cobertura", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento": "Tipo atendimento", "tipo_atendimento_id": "ID Tipo Atendimento",
        "local_id": "ID Local", "coberto": "Coberto", "acomodacao": "Acomodação",
        "acompanhante": "Acompanhante", "restricao": "Restrição",
        "observacoes": "Observações", "status": "Status",
    },
    "contatos": {
        "id": "ID Contato", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "finalidade": "Finalidade", "tipo": "Tipo", "tipo_contato": "Tipo de contato",
        "contato": "Contato", "nome_setor": "Nome/Setor", "responsavel": "Responsável",
        "horario_atendimento": "Horário atendimento", "observacoes": "Observações",
        "status": "Status",
    },
    "contingencias": {
        "id": "ID Contingência", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "local_id": "ID Local", "evento": "Evento", "prioridade": "Prioridade",
        "orientacao_alternativa": "Orientação alternativa", "contato_alternativo": "Contato alternativo",
        "data_inicio": "Data início", "data_fim": "Data fim", "destaque_portal": "Destaque portal",
        "status": "Status", "status_contingencia": "Status contingência",
        "status_revisao": "Status revisão", "observacoes": "Observações",
    },
    "dicas_operacionais": {
        "id": "ID Dica", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "titulo": "Título", "dica": "Dica operacional", "categoria": "Categoria",
        "palavras_chave": "Palavras-chave", "observacoes": "Observações", "status": "Status",
    },
    "consultores": {
        "id": "ID Consultor", "nome": "Nome", "email": "E-mail", "telefone": "Telefone",
        "cargo": "Cargo", "segmento": "Segmento", "observacoes": "Observações", "status": "Status",
        "operadora_id": "ID Operadora",
    },
    "carteiras": {
        "id": "ID Carteira", "consultor_id": "ID Consultor", "operadora_id": "ID Operadora",
        "plano_id": "ID Plano", "segmento": "Segmento", "observacoes": "Observações carteira",
        "status": "Status",
    },
    "comunicados": {
        "id": "ID Comunicado", "operadora_id": "ID Operadora", "titulo": "Título",
        "resumo": "Resumo", "conteudo": "Conteúdo", "categoria": "Categoria",
        "prioridade": "Prioridade", "publico_alvo": "Público-alvo", "responsavel": "Responsável",
        "data_inicio": "Data início", "data_fim": "Data fim", "link": "Link",
        "status": "Status", "status_publicacao": "Status publicação",
    },
    "forum_posts": {
        "id": "ID Post", "operadora_id": "ID Operadora", "titulo": "Título",
        "conteudo": "Conteúdo", "categoria": "Categoria", "autor": "Autor",
        "palavras_chave": "Palavras-chave", "data_publicacao": "Data publicação",
        "created_at": "Data", "status": "Status",
    },
    "forum_comentarios": {
        "id": "ID Comentário", "post_id": "ID Post", "forum_post_id": "ID Post",
        "comentario": "Comentário", "conteudo": "Comentário", "autor": "Autor",
        "created_at": "Data", "status": "Status",
    },
    "conhecimento_ia": {
        "id": "ID Conhecimento", "operadora_id": "ID Operadora", "pergunta": "Pergunta",
        "pergunta_canonica": "Pergunta canônica", "resposta": "Resposta", "fonte": "Fonte",
        "categoria": "Categoria", "intencao": "Intenção", "palavras_chave": "Palavras-chave",
        "sinonimos": "Sinônimos", "confianca": "Confiança", "nivel_confianca": "Nível de confiança",
        "status": "Status", "status_revisao": "Status revisão", "data_revisao": "Data revisão",
        "updated_at": "Última revisão", "registro_fonte_id": "ID Registro Fonte",
    },
}

EXPECTED_COLUMNS: dict[str, list[str]] = {
    key: list(dict.fromkeys(mapping.values()))
    for key, mapping in COLUMN_ALIASES.items()
}


def _resolve_dataset(dataset: str) -> str:
    if dataset in DATASETS:
        return DATASETS[dataset]
    if dataset in DATASETS.values():
        return dataset
    raise KeyError(f"Conjunto de dados não configurado: {dataset}")


def _key_for_table(table_name: str) -> str:
    for key, value in DATASETS.items():
        if value == table_name:
            return key
    return table_name


def _clean_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe is None or dataframe.empty:
        return pd.DataFrame()
    cleaned = dataframe.copy()
    cleaned.columns = [str(column).strip() for column in cleaned.columns]
    return cleaned.dropna(axis=0, how="all").reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner=False)
def read_dataset(dataset: str, ttl: int = 600) -> pd.DataFrame:
    """Lê um conjunto de dados diretamente do Supabase."""
    del ttl  # cache controlado pelo decorator
    table_name = _resolve_dataset(dataset)
    key = _key_for_table(table_name)

    try:
        response = get_supabase_client().table(table_name).select("*").execute()
    except Exception as error:
        logger.exception("Erro ao ler o conjunto %s no Supabase.", table_name)
        raise RuntimeError(
            f"Erro ao carregar '{table_name}' no Supabase: {type(error).__name__}: {error}"
        ) from error

    dataframe = _clean_dataframe(pd.DataFrame(response.data or []))
    aliases = COLUMN_ALIASES.get(key, {})
    if not dataframe.empty:
        dataframe = dataframe.rename(columns={c: aliases[c] for c in dataframe.columns if c in aliases})

    for column in EXPECTED_COLUMNS.get(key, []):
        if column not in dataframe.columns:
            dataframe[column] = ""

    return dataframe.reset_index(drop=True)


def _active_only(dataframe: pd.DataFrame) -> pd.DataFrame:
    if dataframe.empty or "Status" not in dataframe.columns:
        return dataframe
    mask = dataframe["Status"].fillna("").astype(str).str.strip().str.casefold().eq("ativo")
    return dataframe[mask].reset_index(drop=True)


def get_operadoras() -> pd.DataFrame:
    return _active_only(read_dataset("operadoras", CACHE_SETTINGS.OPERADORAS))


def get_planos() -> pd.DataFrame:
    return _active_only(read_dataset("planos", CACHE_SETTINGS.PLANOS))


def get_portais() -> pd.DataFrame:
    return read_dataset("portais", CACHE_SETTINGS.PORTAIS)


def get_documentos() -> pd.DataFrame:
    return read_dataset("documentos", CACHE_SETTINGS.DOCUMENTOS)


def get_contatos() -> pd.DataFrame:
    return read_dataset("contatos", CACHE_SETTINGS.CONTATOS)


def get_contingencias() -> pd.DataFrame:
    return read_dataset("contingencias", CACHE_SETTINGS.CONTINGENCIAS)


def get_comunicados() -> pd.DataFrame:
    return read_dataset("comunicados", CACHE_SETTINGS.COMUNICADOS)


def get_elegibilidade() -> pd.DataFrame:
    return read_dataset("elegibilidade", CACHE_SETTINGS.ELEGIBILIDADE)


def get_autorizacoes() -> pd.DataFrame:
    return read_dataset("autorizacoes", CACHE_SETTINGS.AUTORIZACOES)


def get_coberturas() -> pd.DataFrame:
    return read_dataset("coberturas", CACHE_SETTINGS.COBERTURAS)


def get_dicas_operacionais() -> pd.DataFrame:
    return read_dataset("dicas_operacionais", CACHE_SETTINGS.DICAS)


def get_consultores() -> pd.DataFrame:
    return read_dataset("consultores", CACHE_SETTINGS.CONSULTORES)


def get_carteiras() -> pd.DataFrame:
    return read_dataset("carteiras", CACHE_SETTINGS.CARTEIRAS)


def get_forum_posts() -> pd.DataFrame:
    return read_dataset("forum_posts", CACHE_SETTINGS.FORUM)


def get_forum_comentarios() -> pd.DataFrame:
    return read_dataset("forum_comentarios", CACHE_SETTINGS.FORUM)


def get_conhecimento() -> pd.DataFrame:
    return read_dataset("conhecimento", CACHE_SETTINGS.CONHECIMENTO)


def clear_data_cache() -> None:
    st.cache_data.clear()
