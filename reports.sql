.headers on
.mode column
.width 18 18 18 18 18

DROP VIEW IF EXISTS cleaned_orders;

CREATE TEMP VIEW cleaned_orders AS
WITH deduped AS (
    SELECT o.*,
           ROW_NUMBER() OVER (
             PARTITION BY customer_id, product_id, order_date, quantity,
                          discount_pct, payment_method, rating, returned
             ORDER BY order_id
           ) AS rn
    FROM orders o
)
SELECT
    d.order_id,
    d.customer_id,
    d.product_id,
    d.order_date,
    d.quantity,
    COALESCE(d.discount_pct, 20.0) AS discount_pct_clean,
    UPPER(TRIM(d.payment_method)) AS payment_method_clean,
    d.rating,
    d.returned,
    p.product_name,
    p.category,
    p.price,
    d.quantity * p.price AS gross_value,
    (d.quantity * p.price) *
      (1 - COALESCE(d.discount_pct, 20.0) / 100.0) AS net_revenue
FROM deduped d
JOIN products p ON p.product_id = d.product_id
WHERE d.rn = 1;

SELECT
    COUNT(*) AS cleaned_orders,
    SUM(returned) AS returned_orders,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) AS return_rate_pct,
    ROUND(SUM(net_revenue), 2) AS net_revenue
FROM cleaned_orders;

SELECT
    SUBSTR(order_date, 1, 7) AS month,
    COUNT(*) AS orders,
    ROUND(SUM(net_revenue), 2) AS net_revenue,
    SUM(returned) AS returned_orders,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) AS return_rate_pct
FROM cleaned_orders
GROUP BY month
ORDER BY month;

SELECT
    payment_method_clean AS payment_method,
    COUNT(*) AS orders,
    SUM(returned) AS returned_orders,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) AS return_rate_pct,
    ROUND(SUM(net_revenue), 2) AS net_revenue
FROM cleaned_orders
GROUP BY payment_method_clean
ORDER BY return_rate_pct DESC;

SELECT
    category,
    COUNT(*) AS orders,
    ROUND(SUM(net_revenue), 2) AS net_revenue,
    SUM(returned) AS returned_orders,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) AS return_rate_pct
FROM cleaned_orders
GROUP BY category
ORDER BY net_revenue DESC;

SELECT
    c.city_tier,
    COUNT(*) AS orders,
    ROUND(SUM(b.net_revenue), 2) AS net_revenue,
    SUM(b.returned) AS returned_orders,
    ROUND(100.0 * SUM(b.returned) / COUNT(*), 2) AS return_rate_pct
FROM cleaned_orders b
JOIN customers c ON c.customer_id = b.customer_id
GROUP BY c.city_tier
ORDER BY c.city_tier;

SELECT
    c.acquisition_source,
    COUNT(*) AS orders,
    COUNT(DISTINCT c.customer_id) AS customers,
    ROUND(SUM(b.net_revenue), 2) AS net_revenue,
    SUM(b.returned) AS returned_orders,
    ROUND(100.0 * SUM(b.returned) / COUNT(*), 2) AS return_rate_pct
FROM cleaned_orders b
JOIN customers c ON c.customer_id = b.customer_id
GROUP BY c.acquisition_source
ORDER BY net_revenue DESC;

SELECT
    product_id,
    product_name,
    category,
    COUNT(*) AS orders,
    SUM(returned) AS returned_orders,
    ROUND(100.0 * SUM(returned) / COUNT(*), 2) AS return_rate_pct,
    ROUND(SUM(net_revenue), 2) AS net_revenue
FROM cleaned_orders
GROUP BY product_id, product_name, category
ORDER BY return_rate_pct DESC, orders DESC;
