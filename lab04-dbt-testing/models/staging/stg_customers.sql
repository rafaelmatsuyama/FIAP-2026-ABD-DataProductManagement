with source as (
    select * from {{ source('raw_sources', 'customers') }}
),

renamed as (
    select
        cast(customer_id as varchar) as customer_id,
        cast(customer_name as varchar) as customer_name,
        cast(customer_tier as varchar) as customer_tier,
        cast(country_code as varchar) as country_code,
        cast(signup_date as date) as signup_date
    from source
)

select * from renamed
