-- Teste Singular: Garante que nenhuma transacao liquidada possua valor liquido negativo
-- Regra de Negocio: O valor liquido (net_amount) deve ser estritamente >= 0
select
    transaction_id,
    amount,
    fee,
    net_amount
from {{ ref('fct_financial_transactions') }}
where net_amount < 0
