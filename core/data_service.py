from __future__ import annotations

import logging

import pandas as pd
import streamlit as st

from config.settings import CACHE_SETTINGS, DATASETS
from core.supabase_repository import fetch_table

logger = logging.getLogger(__name__)


# Colunas nativas do Supabase. Esta é a linguagem interna oficial da aplicação.
NATIVE_COLUMNS: dict[str, list[str]] = {
    "operadoras": [
        "id", "codigo", "nome", "nome_curto", "status", "observacoes",
        "logo_url", "site_url", "created_at", "updated_at",
    ],
    "planos": [
        "id", "codigo", "operadora_id", "nome", "nome_padronizado",
        "tipo_plano", "observacao_resumida", "status", "created_at", "updated_at",
    ],
    "locais_atendimento": ["id", "codigo", "nome", "status", "created_at", "updated_at"],
    "tipos_atendimento": ["id", "codigo", "nome", "status", "created_at", "updated_at"],
    "plano_locais": ["id", "plano_id", "local_id", "created_at"],
    "portais": [
        "id", "codigo", "operadora_id", "plano_id", "local_id", "nome", "tipo",
        "url", "exige_login", "instrucao_acesso", "observacoes", "status",
        "dica_geral_acesso", "created_at", "updated_at",
    ],
    "elegibilidade": [
        "id", "codigo", "operadora_id", "plano_id", "local_id",
        "tipo_atendimento_id", "necessario", "orientacao", "observacoes",
        "status", "created_at", "updated_at",
    ],
    "documentos": [
        "id", "codigo", "operadora_id", "plano_id", "local_id",
        "tipo_atendimento_id", "nome", "obrigatorio", "formato", "validade_dias",
        "orientacao", "observacoes", "arquivo_url", "status", "created_at", "updated_at",
    ],
    "autorizacoes": [
        "id", "codigo", "operadora_id", "plano_id", "local_id",
        "tipo_atendimento_id", "necessita_autorizacao", "momento_autorizacao",
        "quem_solicita", "meio_solicitacao", "prazo", "orientacao", "observacoes",
        "status", "created_at", "updated_at",
    ],
    "coberturas": [
        "id", "codigo", "operadora_id", "plano_id", "local_id",
        "tipo_atendimento_id", "coberto", "restricoes_cobertura", "acomodacao",
        "acompanhante", "observacoes", "status", "created_at", "updated_at",
    ],
    "contatos": [
        "id", "codigo", "operadora_id", "plano_id", "nome_setor", "finalidade",
        "tipo", "contato", "responsavel", "horario_atendimento", "observacoes",
        "status", "created_at", "updated_at",
    ],
    "contingencias": [
        "id", "codigo", "operadora_id", "plano_id", "local_id", "titulo",
        "descricao", "orientacao_alternativa", "contato_alternativo", "prioridade",
        "inicio_em", "fim_em", "status", "created_at", "updated_at",
    ],
    "dicas_operacionais": [
        "id", "codigo", "operadora_id", "plano_id", "local_id", "titulo", "categoria",
        "dica", "palavras_chave", "destaque", "status", "created_at", "updated_at",
    ],
    "consultores": [
        "id", "codigo", "nome", "cargo", "email", "telefone", "observacoes",
        "status", "created_at", "updated_at",
    ],
    "carteiras": [
        "id", "consultor_id", "operadora_id", "plano_id", "papel", "observacoes",
        "status", "created_at", "updated_at",
    ],
    "comunicados": [
        "id", "codigo", "operadora_id", "titulo", "resumo", "conteudo", "categoria",
        "prioridade", "publico_alvo", "inicio_em", "fim_em", "destaque", "status",
        "responsavel", "created_at", "updated_at",
    ],
    # Estes módulos permanecem em compatibilidade até a revisão funcional deles.
    "forum_posts": [],
    "forum_comentarios": [],
    "conhecimento_ia": [],
}


# Compatibilidade temporária para views ainda não migradas na Etapa 2B.
# Nenhum service novo deve depender destes nomes.
LEGACY_ALIASES: dict[str, dict[str, str]] = {
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
        "tipo_atendimento_id": "ID Tipo Atendimento", "local_id": "ID Local",
        "necessario": "Necessário", "orientacao": "Orientação",
        "observacoes": "Observações", "status": "Status",
    },
    "documentos": {
        "id": "ID Documento", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento_id": "ID Tipo Atendimento", "local_id": "ID Local",
        "nome": "Documento", "obrigatorio": "Obrigatório", "formato": "Formato",
        "validade_dias": "Validade em dias", "orientacao": "Orientação",
        "arquivo_url": "Link Documento", "observacoes": "Observações", "status": "Status",
    },
    "autorizacoes": {
        "id": "ID Autorização", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento_id": "ID Tipo Atendimento", "local_id": "ID Local",
        "necessita_autorizacao": "Necessita autorização", "momento_autorizacao": "Momento autorização",
        "quem_solicita": "Quem solicita", "meio_solicitacao": "Meio de solicitação",
        "prazo": "Prazo", "orientacao": "Orientação", "observacoes": "Observações",
        "status": "Status",
    },
    "coberturas": {
        "id": "ID Cobertura", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "tipo_atendimento_id": "ID Tipo Atendimento", "local_id": "ID Local",
        "coberto": "Coberto", "restricoes_cobertura": "Restrições de cobertura",
        "acomodacao": "Acomodação", "acompanhante": "Acompanhante",
        "observacoes": "Observações", "status": "Status",
    },
    "contatos": {
        "id": "ID Contato", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "finalidade": "Finalidade", "tipo": "Tipo", "contato": "Contato",
        "nome_setor": "Nome/Setor", "responsavel": "Responsável",
        "horario_atendimento": "Horário atendimento", "observacoes": "Observações",
        "status": "Status",
    },
    "contingencias": {
        "id": "ID Contingência", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "local_id": "ID Local", "titulo": "Evento", "descricao": "Descrição",
        "prioridade": "Prioridade", "orientacao_alternativa": "Orientação alternativa",
        "contato_alternativo": "Contato alternativo", "inicio_em": "Data início",
        "fim_em": "Data fim", "status": "Status", "observacoes": "Observações",
    },
    "dicas_operacionais": {
        "id": "ID Dica", "operadora_id": "ID Operadora", "plano_id": "ID Plano",
        "titulo": "Título", "dica": "Dica operacional", "categoria": "Categoria",
        "palavras_chave": "Palavras-chave", "status": "Status",
    },
    "consultores": {
        "id": "ID Consultor", "nome": "Nome", "email": "E-mail", "telefone": "Telefone",
        "cargo": "Cargo", "observacoes": "Observações", "status": "Status",
    },
    "carteiras": {
        "id": "ID Carteira", "consultor_id": "ID Consultor", "operadora_id": "ID Operadora",
        "plano_id": "ID Plano", "papel": "Papel", "observacoes": "Observações carteira",
        "status": "Status",
    },
    "comunicados": {
        "id": "ID Comunicado", "operadora_id": "ID Operadora", "titulo": "Título",
        "resumo": "Resumo", "conteudo": "Conteúdo", "categoria": "Categoria",
        "prioridade": "Prioridade", "publico_alvo": "Público-alvo", "responsavel": "Responsável",
        "inicio_em": "Data início", "fim_em": "Data fim", "status": "Status",
    },
}


LEGACY_EXPECTED_COLUMNS: dict[str, list[str]] = {
    "operadoras": ["ID Operadora", "Código", "Operadora", "Nome curto", "Status", "Observações", "Logo URL", "Site URL"],
    "planos": ["ID Plano", "Código", "ID Operadora", "Plano", "Nome padronizado", "Tipo do plano", "Observação resumida", "Status"],
    "portais": ["ID Portal", "Código", "ID Operadora", "ID Plano", "ID Local", "Nome do portal", "Tipo", "URL", "Exige login", "Instrução de acesso", "Observações", "Status", "Dica geral de acesso"],
    "elegibilidade": ["ID Elegibilidade", "ID Operadora", "ID Plano", "Tipo atendimento", "ID Tipo Atendimento", "ID Local", "Elegível", "Documento necessário", "Como verificar", "Observações", "Status"],
    "documentos": ["ID Documento", "ID Operadora", "ID Plano", "Tipo atendimento", "ID Tipo Atendimento", "ID Local", "Documento", "Obrigatório", "Validade em dias", "Original/Cópia", "Aceita e-mail", "Aceita fax", "Aceita outro convênio", "Link Documento", "Observações", "Status", "Status revisão"],
    "autorizacoes": ["ID Autorização", "ID Operadora", "ID Plano", "Tipo atendimento", "ID Tipo Atendimento", "ID Local", "Necessita autorização", "Pré/Pós", "Quem solicita", "Meio de solicitação", "Prazo retorno horas", "Observações", "Status"],
    "coberturas": ["ID Cobertura", "ID Operadora", "ID Plano", "Tipo atendimento", "ID Tipo Atendimento", "ID Local", "Coberto", "Acomodação", "Acompanhante", "Restrição", "Observações", "Status"],
    "contatos": ["ID Contato", "ID Operadora", "ID Plano", "Finalidade", "Tipo", "Tipo de contato", "Contato", "Nome/Setor", "Responsável", "Horário atendimento", "Observações", "Status"],
    "contingencias": ["ID Contingência", "ID Operadora", "ID Plano", "ID Local", "Evento", "Prioridade", "Orientação alternativa", "Contato alternativo", "Data início", "Data fim", "Destaque portal", "Status", "Status contingência", "Status revisão", "Observações"],
    "dicas_operacionais": ["ID Dica", "ID Operadora", "ID Plano", "Título", "Dica operacional", "Categoria", "Palavras-chave", "Observações", "Status"],
    "consultores": ["ID Consultor", "Nome", "E-mail", "Telefone", "Cargo", "Segmento", "Observações", "Status", "ID Operadora"],
    "carteiras": ["ID Carteira", "ID Consultor", "ID Operadora", "ID Plano", "Segmento", "Observações carteira", "Status"],
    "comunicados": ["ID Comunicado", "ID Operadora", "Título", "Resumo", "Conteúdo", "Categoria", "Prioridade", "Público-alvo", "Responsável", "Data início", "Data fim", "Link", "Status", "Status publicação"],
    "forum_posts": ["ID Post", "ID Operadora", "Título", "Conteúdo", "Categoria", "Autor", "Palavras-chave", "Data publicação", "Data", "Status"],
    "forum_comentarios": ["ID Comentário", "ID Post", "Comentário", "Autor", "Data", "Status"],
    "conhecimento_ia": ["ID Conhecimento", "ID Operadora", "Pergunta", "Pergunta canônica", "Resposta", "Fonte", "Categoria", "Intenção", "Palavras-chave", "Sinônimos", "Confiança", "Nível de confiança", "Status", "Status revisão", "Data revisão", "Última revisão", "ID Registro Fonte"],
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
def read_dataset_native(dataset: str, ttl: int = 600) -> pd.DataFrame:
    """Lê um conjunto diretamente do Supabase preservando snake_case nativo."""
    del ttl
    table_name = _resolve_dataset(dataset)
    key = _key_for_table(table_name)

    try:
        dataframe = _clean_dataframe(fetch_table(table_name))
    except Exception as error:
        logger.exception("Erro ao ler o conjunto %s no Supabase.", table_name)
        raise RuntimeError(
            f"Erro ao carregar '{table_name}' no Supabase: {type(error).__name__}: {error}"
        ) from error

    for column in NATIVE_COLUMNS.get(key, []):
        if column not in dataframe.columns:
            dataframe[column] = pd.NA

    return dataframe.reset_index(drop=True)


@st.cache_data(ttl=600, show_spinner=False)
def read_dataset(dataset: str, ttl: int = 600) -> pd.DataFrame:
    """Compatibilidade temporária para views ainda baseadas nos rótulos da planilha."""
    dataframe = read_dataset_native(dataset, ttl).copy()
    table_name = _resolve_dataset(dataset)
    key = _key_for_table(table_name)
    aliases = LEGACY_ALIASES.get(key, {})
    if not dataframe.empty and aliases:
        dataframe = dataframe.rename(
            columns={column: aliases[column] for column in dataframe.columns if column in aliases}
        )

    for column in LEGACY_EXPECTED_COLUMNS.get(key, []):
        if column not in dataframe.columns:
            dataframe[column] = ""

    return dataframe.reset_index(drop=True)


def _active_only(dataframe: pd.DataFrame, status_column: str = "status") -> pd.DataFrame:
    if dataframe.empty or status_column not in dataframe.columns:
        return dataframe
    mask = (
        dataframe[status_column]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.casefold()
        .eq("ativo")
    )
    return dataframe[mask].reset_index(drop=True)


def _legacy_active_only(dataframe: pd.DataFrame) -> pd.DataFrame:
    return _active_only(dataframe, "Status")


# API nativa: deve ser usada em todo código novo ou migrado.
def get_operadoras_native() -> pd.DataFrame:
    return _active_only(read_dataset_native("operadoras", CACHE_SETTINGS.OPERADORAS))


def get_planos_native() -> pd.DataFrame:
    return _active_only(read_dataset_native("planos", CACHE_SETTINGS.PLANOS))


def get_locais_atendimento_native() -> pd.DataFrame:
    return _active_only(read_dataset_native("locais_atendimento", CACHE_SETTINGS.LOCAIS_ATENDIMENTO))


def get_tipos_atendimento_native() -> pd.DataFrame:
    return _active_only(read_dataset_native("tipos_atendimento", CACHE_SETTINGS.TIPOS_ATENDIMENTO))


def get_plano_locais_native() -> pd.DataFrame:
    return read_dataset_native("plano_locais", CACHE_SETTINGS.PLANO_LOCAIS)


def get_portais_native() -> pd.DataFrame:
    return read_dataset_native("portais", CACHE_SETTINGS.PORTAIS)


def get_documentos_native() -> pd.DataFrame:
    return read_dataset_native("documentos", CACHE_SETTINGS.DOCUMENTOS)


def get_contatos_native() -> pd.DataFrame:
    return read_dataset_native("contatos", CACHE_SETTINGS.CONTATOS)


def get_contingencias_native() -> pd.DataFrame:
    return read_dataset_native("contingencias", CACHE_SETTINGS.CONTINGENCIAS)


def get_comunicados_native() -> pd.DataFrame:
    return read_dataset_native("comunicados", CACHE_SETTINGS.COMUNICADOS)


def get_elegibilidade_native() -> pd.DataFrame:
    return read_dataset_native("elegibilidade", CACHE_SETTINGS.ELEGIBILIDADE)


def get_autorizacoes_native() -> pd.DataFrame:
    return read_dataset_native("autorizacoes", CACHE_SETTINGS.AUTORIZACOES)


def get_coberturas_native() -> pd.DataFrame:
    return read_dataset_native("coberturas", CACHE_SETTINGS.COBERTURAS)


def get_dicas_operacionais_native() -> pd.DataFrame:
    return read_dataset_native("dicas_operacionais", CACHE_SETTINGS.DICAS)


def get_consultores_native() -> pd.DataFrame:
    return read_dataset_native("consultores", CACHE_SETTINGS.CONSULTORES)


def get_carteiras_native() -> pd.DataFrame:
    return read_dataset_native("carteiras", CACHE_SETTINGS.CARTEIRAS)


# API legada: mantida apenas para as views que serão migradas na Parte 2.
def get_operadoras() -> pd.DataFrame:
    return _legacy_active_only(read_dataset("operadoras", CACHE_SETTINGS.OPERADORAS))


def get_planos() -> pd.DataFrame:
    return _legacy_active_only(read_dataset("planos", CACHE_SETTINGS.PLANOS))


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
