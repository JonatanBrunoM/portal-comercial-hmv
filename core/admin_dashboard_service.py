from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from core.supabase_repository import fetch_records


CORE_TABLES = {
    "operadoras": "Operadoras",
    "planos": "Planos",
    "portais": "Portais",
    "portal_credenciais": "Credenciais",
    "elegibilidade": "Elegibilidade",
    "autorizacoes": "Autorizações",
    "coberturas": "Coberturas",
    "documentos": "Documentos",
    "contatos": "Contatos",
    "consultores": "Consultores",
    "comunicados": "Comunicados",
    "contingencias": "Contingências",
    "dicas_operacionais": "Dicas operacionais",
}


@dataclass(frozen=True)
class AdminHealth:
    total_records: int
    active_records: int
    inactive_records: int
    operators: int
    plans: int
    portals: int
    credentials: int
    published_announcements: int
    active_contingencies: int
    issues: list[dict]


def _count_status(dataframe: pd.DataFrame, status: str) -> int:
    if dataframe.empty or "status" not in dataframe.columns:
        return 0
    return int(
        dataframe["status"]
        .fillna("")
        .astype(str)
        .str.casefold()
        .eq(status.casefold())
        .sum()
    )


def _load_core_tables() -> dict[str, pd.DataFrame]:
    data: dict[str, pd.DataFrame] = {}
    for table in CORE_TABLES:
        try:
            data[table] = fetch_records(table)
        except Exception:
            data[table] = pd.DataFrame()
    return data


def get_admin_health() -> AdminHealth:
    data = _load_core_tables()

    total_records = sum(len(df) for df in data.values())
    active_records = sum(_count_status(df, "Ativo") for df in data.values())
    inactive_records = sum(_count_status(df, "Inativo") for df in data.values())

    announcements = data["comunicados"]
    published_announcements = _count_status(announcements, "Publicado")

    contingencies = data["contingencias"]
    active_contingencies = _count_status(contingencies, "Ativo")

    issues: list[dict] = []

    plans = data["planos"]
    if not plans.empty and "operadora_id" in plans.columns:
        missing = int(plans["operadora_id"].isna().sum())
        if missing:
            issues.append({
                "severity": "Alta",
                "area": "Planos",
                "message": f"{missing} plano(s) sem operadora vinculada.",
            })

    portals = data["portais"]
    if not portals.empty:
        if "url" in portals.columns:
            missing = int(
                portals["url"].fillna("").astype(str).str.strip().eq("").sum()
            )
            if missing:
                issues.append({
                    "severity": "Média",
                    "area": "Portais",
                    "message": f"{missing} portal(is) sem URL cadastrada.",
                })

        if "exige_login" in portals.columns:
            login_portals = portals[
                portals["exige_login"].fillna(False).astype(bool)
            ]
            credentials = data["portal_credenciais"]
            credential_portal_ids = set()
            if not credentials.empty and "portal_id" in credentials.columns:
                active_credentials = credentials
                if "status" in active_credentials.columns:
                    active_credentials = active_credentials[
                        active_credentials["status"]
                        .fillna("")
                        .astype(str)
                        .str.casefold()
                        .eq("ativo")
                    ]
                credential_portal_ids = {
                    str(value)
                    for value in active_credentials["portal_id"].dropna().tolist()
                }

            if "id" in login_portals.columns:
                without_credentials = [
                    str(value)
                    for value in login_portals["id"].dropna().tolist()
                    if str(value) not in credential_portal_ids
                ]
                if without_credentials:
                    issues.append({
                        "severity": "Alta",
                        "area": "Credenciais",
                        "message": (
                            f"{len(without_credentials)} portal(is) que exigem login "
                            "estão sem credencial ativa."
                        ),
                    })

    contacts = data["contatos"]
    if not contacts.empty and "contato" in contacts.columns:
        missing = int(
            contacts["contato"].fillna("").astype(str).str.strip().eq("").sum()
        )
        if missing:
            issues.append({
                "severity": "Média",
                "area": "Contatos",
                "message": f"{missing} contato(s) sem informação de contato.",
            })

    consultants = data["consultores"]
    if not consultants.empty:
        email_missing = 0
        phone_missing = 0
        if "email" in consultants.columns:
            email_missing = int(
                consultants["email"].fillna("").astype(str).str.strip().eq("").sum()
            )
        if "telefone" in consultants.columns:
            phone_missing = int(
                consultants["telefone"].fillna("").astype(str).str.strip().eq("").sum()
            )
        if email_missing and phone_missing:
            issues.append({
                "severity": "Baixa",
                "area": "Consultores",
                "message": (
                    "Há consultores com dados de contato incompletos. "
                    "Revise e-mail e telefone."
                ),
            })

    return AdminHealth(
        total_records=total_records,
        active_records=active_records,
        inactive_records=inactive_records,
        operators=len(data["operadoras"]),
        plans=len(data["planos"]),
        portals=len(data["portais"]),
        credentials=len(data["portal_credenciais"]),
        published_announcements=published_announcements,
        active_contingencies=active_contingencies,
        issues=issues,
    )


def get_recent_audit_logs(limit: int = 100) -> pd.DataFrame:
    logs = fetch_records(
        "audit_logs",
        order_by="created_at",
        ascending=False,
        limit=limit,
    )
    if logs.empty:
        return logs

    profiles = fetch_records(
        "profiles",
        columns="id,nome,email",
    )

    if not profiles.empty and "usuario_id" in logs.columns:
        profile_map = {}
        for _, profile in profiles.iterrows():
            profile_id = str(profile.get("id") or "")
            if not profile_id:
                continue
            name = str(profile.get("nome") or "").strip()
            email = str(profile.get("email") or "").strip()
            profile_map[profile_id] = name or email or "Usuário"

        logs = logs.copy()
        logs["usuario"] = logs["usuario_id"].apply(
            lambda value: profile_map.get(str(value), "Sistema / usuário removido")
            if pd.notna(value)
            else "Sistema"
        )

    return logs


def get_admin_table_summary() -> pd.DataFrame:
    rows = []
    for table, label in CORE_TABLES.items():
        try:
            dataframe = fetch_records(table)
            rows.append({
                "Área": label,
                "Total": len(dataframe),
                "Ativos": _count_status(dataframe, "Ativo"),
                "Inativos": _count_status(dataframe, "Inativo"),
            })
        except Exception:
            rows.append({
                "Área": label,
                "Total": None,
                "Ativos": None,
                "Inativos": None,
            })

    return pd.DataFrame(rows)
