with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    customer_id,
    customer_name,
    customer_tier,
    country_code,
    signup_date
from customers
