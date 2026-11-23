-- 03_segments.sql
-- Marketing segments for ACTIVE internet customers (churned customers are not targets).
-- Segment = contract type x tenure band, the two levers that shape the message and channel.

CREATE OR REPLACE VIEW active_segments AS
SELECT contract,
       tenure_band,
       COUNT(*)                                          AS active_customers,
       ROUND(AVG(protection_addons), 2)                  AS avg_protection_addons,
       ROUND(AVG((protection_addons = 0)::INT), 3)       AS share_with_no_protection,
       ROUND(AVG(monthly_charges), 2)                    AS avg_monthly_charges
FROM internet_customers
WHERE NOT churned
GROUP BY contract, tenure_band
ORDER BY contract, tenure_band;
