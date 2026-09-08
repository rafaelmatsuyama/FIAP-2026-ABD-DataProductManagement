with transactions as (
    select * from {{ ref('stg_transactions') }}
),

completed_transactions as (
    select
        transaction_id,
        customer_id,
        amount,
        fee,
        round(amount - fee, 2) as net_amount,
        currency,
        status,
        payment_method,
        created_at
    from transactions
    where status = 'COMPLETED'
)

select * from completed_transactions
