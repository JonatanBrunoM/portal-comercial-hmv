-- Executar no SQL Editor do Supabase antes de ativar os indicadores.
-- Reutiliza a RPC de conferência já existente para preservar sua validação de acesso.
-- Uma única chamada HTTP atende a página de até 20 orçamentos.
create or replace function public.particular_get_mv_status_batch(
    p_profile_id uuid,
    p_budget_ids uuid[]
)
returns jsonb
language plpgsql
security invoker
set search_path = public
as $$
declare
    v_budget_id uuid;
    v_context jsonb;
    v_result jsonb := '{}'::jsonb;
    v_outcome text;
begin
    if p_profile_id is null or p_budget_ids is null
       or cardinality(p_budget_ids) > 50 then
        raise exception 'Parâmetros inválidos para consulta de conferências.';
    end if;

    foreach v_budget_id in array p_budget_ids loop
        if v_budget_id is null then
            raise exception 'Identificador de orçamento inválido.';
        end if;
        -- A função existente verifica o perfil e o acesso a cada orçamento.
        v_context := to_jsonb(public.particular_get_mv_check_context(
            p_profile_id := p_profile_id,
            p_budget_id := v_budget_id
        ));
        v_outcome := v_context #>> '{latest_mv_check,outcome}';
        if v_outcome is not null and v_outcome not in
            ('PENDING', 'REALIZED', 'NOT_PERFORMED', 'CANCELLED') then
            raise exception 'Resultado de conferência desconhecido.';
        end if;
        v_result := v_result || jsonb_build_object(v_budget_id::text, v_outcome);
    end loop;
    return v_result;
end;
$$;

-- A aplicação utiliza a credencial server-side. Não liberar a função ao público.
revoke all on function public.particular_get_mv_status_batch(uuid, uuid[]) from public, anon, authenticated;
grant execute on function public.particular_get_mv_status_batch(uuid, uuid[]) to service_role;
