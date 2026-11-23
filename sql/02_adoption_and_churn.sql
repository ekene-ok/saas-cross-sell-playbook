-- 02_adoption_and_churn.sql
-- How widely is each add-on adopted, and how does churn differ with and without it?

CREATE OR REPLACE VIEW addon_adoption AS
WITH long AS (
    SELECT 'Online Security'   AS addon, has_online_security   AS has_it, churned FROM internet_customers UNION ALL
    SELECT 'Online Backup',              has_online_backup,              churned FROM internet_customers UNION ALL
    SELECT 'Device Protection',          has_device_protection,          churned FROM internet_customers UNION ALL
    SELECT 'Tech Support',               has_tech_support,               churned FROM internet_customers UNION ALL
    SELECT 'Streaming TV',               has_streaming_tv,               churned FROM internet_customers UNION ALL
    SELECT 'Streaming Movies',           has_streaming_movies,           churned FROM internet_customers
)
SELECT addon,
       ROUND(AVG(has_it::INT), 3)                                        AS adoption_rate,
       ROUND(AVG(churned::INT) FILTER (WHERE has_it), 3)                 AS churn_with_addon,
       ROUND(AVG(churned::INT) FILTER (WHERE NOT has_it), 3)             AS churn_without_addon,
       COUNT(*) FILTER (WHERE NOT has_it AND NOT churned)                AS active_non_adopters
FROM long
GROUP BY addon
ORDER BY churn_without_addon - churn_with_addon DESC;

-- Churn by number of protection add-ons (security, backup, device protection, tech support).
CREATE OR REPLACE VIEW churn_by_protection_count AS
SELECT protection_addons,
       COUNT(*)                         AS customers,
       ROUND(AVG(churned::INT), 3)      AS churn_rate,
       ROUND(AVG(tenure_months), 1)     AS avg_tenure_months
FROM internet_customers
GROUP BY protection_addons
ORDER BY protection_addons;

-- Same view within each contract type: does the pattern survive a key confounder?
CREATE OR REPLACE VIEW churn_by_protection_and_contract AS
SELECT contract,
       protection_addons,
       COUNT(*)                         AS customers,
       ROUND(AVG(churned::INT), 3)      AS churn_rate
FROM internet_customers
GROUP BY contract, protection_addons
ORDER BY contract, protection_addons;
