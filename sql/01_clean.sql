-- 01_clean.sql
-- Typed, analysis-ready customer table. One row per subscriber.
-- TotalCharges is blank for 11 brand-new customers (tenure 0); set to 0.

CREATE OR REPLACE TABLE customers AS
SELECT customerID                                   AS customer_id,
       gender, SeniorCitizen = 1                    AS is_senior,
       Partner = 'Yes'                              AS has_partner,
       Dependents = 'Yes'                           AS has_dependents,
       tenure                                       AS tenure_months,
       PhoneService = 'Yes'                         AS has_phone,
       MultipleLines = 'Yes'                        AS has_multiple_lines,
       InternetService                              AS internet_type,
       OnlineSecurity  = 'Yes'                      AS has_online_security,
       OnlineBackup    = 'Yes'                      AS has_online_backup,
       DeviceProtection = 'Yes'                     AS has_device_protection,
       TechSupport     = 'Yes'                      AS has_tech_support,
       StreamingTV     = 'Yes'                      AS has_streaming_tv,
       StreamingMovies = 'Yes'                      AS has_streaming_movies,
       Contract                                     AS contract,
       PaperlessBilling = 'Yes'                     AS paperless_billing,
       PaymentMethod                                AS payment_method,
       MonthlyCharges                               AS monthly_charges,
       COALESCE(TRY_CAST(NULLIF(TRIM(TotalCharges), '') AS DOUBLE), 0) AS total_charges,
       Churn = 'Yes'                                AS churned
FROM read_csv_auto('data/raw/telco_customer_churn.csv', all_varchar = false);

-- Add-ons are only sold to internet subscribers, so the cross-sell base is them.
CREATE OR REPLACE VIEW internet_customers AS
SELECT *,
       has_online_security::INT + has_online_backup::INT
     + has_device_protection::INT + has_tech_support::INT   AS protection_addons,
       has_streaming_tv::INT + has_streaming_movies::INT    AS streaming_addons,
       CASE WHEN tenure_months < 12 THEN '0 to 11 months'
            WHEN tenure_months < 24 THEN '12 to 23 months'
            WHEN tenure_months < 48 THEN '24 to 47 months'
            ELSE '48+ months' END                            AS tenure_band
FROM customers
WHERE internet_type <> 'No';
