with source as (
    select * from {{ source('raw_sources', 'transactions') }}
),

renamed as (
    select
        cast(transaction_id as varchar) as transaction_id,
        cast(customer_id as varchar) as customer_id,
        cast(amount as double) as amount,
        cast(fee as double) as fee,
        cast(currency as varchar) as currency,
        cast(status as varchar) as status,
        cast(payment_method as varchar) as payment_method,
        cast(created_at as timestamp) as created_at
    from source
)

select * from renamed
