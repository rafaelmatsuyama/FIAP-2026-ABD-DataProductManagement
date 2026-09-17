-- Singular Test: Ensures no settled transaction has a negative net amount
-- Business Rule: Net amount (net_amount) must be strictly >= 0
select
    transaction_id,
    amount,
    fee,
    net_amount
from {{ ref('fct_financial_transactions') }}
where net_amount < 0
