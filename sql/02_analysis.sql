-- ============================================================================
-- 02_analysis.sql
-- Question: which factors actually predict whether a patient misses an appointment?
-- Each query starts with a "-- name: <id>" line; run_analysis.py runs them and
-- saves each result to results/<id>.csv.
-- no_show = 1 means the patient did NOT show up.
-- ============================================================================

-- name: q01_baseline
SELECT
    COUNT(*)                          AS appointments,
    SUM(no_show)                      AS no_shows,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments;

-- name: q02_by_lead_bucket
-- Lead time = days between booking and the appointment.
SELECT
    lead_bucket,
    COUNT(*)                          AS appointments,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY lead_bucket
ORDER BY lead_bucket;

-- name: q03_by_age_group
SELECT
    age_group,
    COUNT(*)                          AS appointments,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY age_group
ORDER BY age_group;

-- name: q04_sms_naive
-- Naive view: patients who got an SMS reminder miss MORE appointments?!
SELECT
    sms_received,
    COUNT(*)                          AS appointments,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY sms_received;

-- name: q05_sms_by_lead_bucket
-- Same comparison, but within each lead-time bucket. SMS reminders are almost
-- never sent for short-notice bookings, so the naive comparison above mixes
-- "got an SMS" with "booked far ahead" (confounding).
SELECT
    lead_bucket,
    SUM(CASE WHEN sms_received = 0 THEN 1 ELSE 0 END)                       AS n_no_sms,
    ROUND(100.0 * AVG(CASE WHEN sms_received = 0 THEN no_show END), 2)      AS no_show_pct_no_sms,
    SUM(CASE WHEN sms_received = 1 THEN 1 ELSE 0 END)                       AS n_sms,
    ROUND(100.0 * AVG(CASE WHEN sms_received = 1 THEN no_show END), 2)      AS no_show_pct_sms
FROM appointments
GROUP BY lead_bucket
ORDER BY lead_bucket;

-- name: q06_binary_factors
SELECT 'scholarship' AS factor, CAST(scholarship AS TEXT) AS value,
       COUNT(*) AS appointments, ROUND(100.0 * AVG(no_show), 2) AS no_show_pct
FROM appointments GROUP BY scholarship
UNION ALL
SELECT 'hypertension', CAST(hypertension AS TEXT),
       COUNT(*), ROUND(100.0 * AVG(no_show), 2)
FROM appointments GROUP BY hypertension
UNION ALL
SELECT 'diabetes', CAST(diabetes AS TEXT),
       COUNT(*), ROUND(100.0 * AVG(no_show), 2)
FROM appointments GROUP BY diabetes
UNION ALL
SELECT 'alcoholism', CAST(alcoholism AS TEXT),
       COUNT(*), ROUND(100.0 * AVG(no_show), 2)
FROM appointments GROUP BY alcoholism
UNION ALL
SELECT 'handicap', CAST(handicap AS TEXT),
       COUNT(*), ROUND(100.0 * AVG(no_show), 2)
FROM appointments GROUP BY handicap
UNION ALL
SELECT 'gender', gender,
       COUNT(*), ROUND(100.0 * AVG(no_show), 2)
FROM appointments GROUP BY gender;

-- name: q07_by_weekday
SELECT
    weekday,
    COUNT(*)                          AS appointments,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY weekday, weekday_num
ORDER BY weekday_num;

-- name: q08_neighbourhood
-- Only neighbourhoods with 500+ appointments, so rates are not noise.
SELECT
    neighbourhood,
    COUNT(*)                          AS appointments,
    SUM(no_show)                      AS no_shows,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY neighbourhood
HAVING COUNT(*) >= 500
ORDER BY no_show_pct DESC;

-- name: q09_patient_history
-- Does a patient's own past behaviour predict the next miss?
-- (history counts only appointments on EARLIER days)
SELECT
    CASE
        WHEN prior_appointments = 0 THEN '1. No earlier visit in data'
        WHEN prior_no_shows = 0     THEN '2. Earlier visits, none missed'
        WHEN prior_no_shows = 1     THEN '3. One earlier no-show'
        ELSE                             '4. Two or more earlier no-shows'
    END                               AS history,
    COUNT(*)                          AS appointments,
    ROUND(100.0 * AVG(no_show), 2)    AS no_show_pct
FROM appointments
GROUP BY history
ORDER BY history;

-- name: q10_factor_ranking
-- One-number summary per factor: gap (in percentage points) between the
-- highest and lowest no-show rate among groups with 1,000+ appointments.
-- This is a UNIVARIATE view; factors overlap (e.g. age and hypertension), so
-- 03_model.py checks which effects survive when everything is controlled.
WITH factor_rates AS (
    SELECT 'lead_time' AS factor, lead_bucket AS grp, COUNT(*) AS n, 100.0 * AVG(no_show) AS rate FROM appointments GROUP BY lead_bucket
    UNION ALL SELECT 'age_group', age_group, COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY age_group
    UNION ALL SELECT 'patient_history',
        CASE WHEN prior_appointments = 0 THEN 'none'
             WHEN prior_no_shows = 0 THEN 'clean'
             WHEN prior_no_shows = 1 THEN 'one'
             ELSE 'two_plus' END,
        COUNT(*), 100.0 * AVG(no_show) FROM appointments
        GROUP BY CASE WHEN prior_appointments = 0 THEN 'none'
                      WHEN prior_no_shows = 0 THEN 'clean'
                      WHEN prior_no_shows = 1 THEN 'one'
                      ELSE 'two_plus' END
    UNION ALL SELECT 'neighbourhood', neighbourhood, COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY neighbourhood
    UNION ALL SELECT 'sms_received', CAST(sms_received AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY sms_received
    UNION ALL SELECT 'scholarship', CAST(scholarship AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY scholarship
    UNION ALL SELECT 'weekday', weekday, COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY weekday
    UNION ALL SELECT 'alcoholism', CAST(alcoholism AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY alcoholism
    UNION ALL SELECT 'hypertension', CAST(hypertension AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY hypertension
    UNION ALL SELECT 'diabetes', CAST(diabetes AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY diabetes
    UNION ALL SELECT 'handicap', CAST(handicap AS TEXT), COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY handicap
    UNION ALL SELECT 'gender', gender, COUNT(*), 100.0 * AVG(no_show) FROM appointments GROUP BY gender
)
SELECT
    factor,
    ROUND(MAX(rate), 2)                AS highest_group_pct,
    ROUND(MIN(rate), 2)                AS lowest_group_pct,
    ROUND(MAX(rate) - MIN(rate), 2)    AS gap_pp
FROM factor_rates
WHERE n >= 1000
GROUP BY factor
ORDER BY gap_pp DESC;
